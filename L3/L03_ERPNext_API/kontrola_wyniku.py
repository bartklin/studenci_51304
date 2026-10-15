"""Niezależna kontrola lokalnego faktury.csv względem JSON pobranych przez eksporter.
Nie łączy się z ERPNext; nie sprawdza aktualności lokalnej kopii na serwerze.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
ROOT = Path(__file__).resolve().parent


def check(folder: Path) -> dict:
    errors, warnings = [], []
    csv_path=folder/'faktury.csv'
    try:
        with csv_path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f,delimiter=';')
            required={'invoice_id','customer','posting_date','currency','grand_total','outstanding_amount','payment_status','sales_orders','erpnext_status','docstatus','pdf_file'}
            if set(reader.fieldnames or []) != required:
                errors.append('Niepoprawny zestaw kolumn CSV.')
            rows=list(reader)
    except (OSError, ValueError, csv.Error) as exc:
        return {'wynik':'BLAD','bledy':[str(exc)],'uwagi':[], 'liczba_faktur':0}
    if not rows:
        return {'wynik':'BRAK_DANYCH','bledy':[], 'uwagi':['CSV ma sam nagłówek. To nie jest dowód eksportu faktury.'], 'liczba_faktur':0}
    manifest_path=folder/'eksport_manifest.json'
    references={}
    if manifest_path.exists():
        try:
            manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
            references={r['invoice_id']:r for r in manifest['invoices']}
            if len(references)!=len(manifest['invoices']): errors.append('Powtórzone ID w manifeście eksportu.')
            if set(references)!=set(r.get('invoice_id') for r in rows): errors.append('Zestaw faktur CSV nie zgadza się z manifestem eksportu.')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append('Niepoprawny manifest eksportu: '+str(exc))
    else:
        warnings.append('Brak eksport_manifest.json (starszy eksport). Sprawdzono pola z lokalnych JSON, ale nie potwierdzono kompletności partii.')
    index={}
    for path in sorted((folder/'faktury_json').glob('*.json')):
        try:
            doc=json.loads(path.read_text(encoding='utf-8-sig'))
            if isinstance(doc,dict) and doc.get('name'):
                index.setdefault(doc['name'],[]).append((path,doc))
        except (ValueError,OSError) as exc:
            warnings.append(f'Nieczytelny JSON {path.name}: {exc}')
    seen=set()
    for row in rows:
        ident=row.get('invoice_id','')
        if not ident or ident in seen:
            errors.append(f'Puste lub powtórzone invoice_id: {ident}')
            continue
        seen.add(ident)
        candidates=index.get(ident,[])
        ref=references.get(ident)
        if ref:
            candidates=[item for item in candidates if item[0].name==ref.get('json_file')]
        if len(candidates)!=1:
            errors.append(f'{ident}: oczekiwano jednego lokalnego JSON, znaleziono {len(candidates)}.')
            continue
        path,doc=candidates[0]
        if ref and hashlib.sha256(path.read_bytes()).hexdigest()!=ref.get('json_sha256'):
            errors.append(f'{ident}: JSON zmienił się od zapisu eksportu.')
        for csv_key,json_key in [('invoice_id','name'),('customer','customer'),('posting_date','posting_date'),('currency','currency'),('erpnext_status','status'),('docstatus','docstatus')]:
            if row.get(csv_key) != str(doc.get(json_key,'')):
                errors.append(f'{ident}: niezgodne {csv_key}.')
        try:
            total=Decimal(str(doc['grand_total'])); outstanding=Decimal(str(doc['outstanding_amount']))
            if not total.is_finite() or not outstanding.is_finite(): raise ValueError('Kwota nieskończona/NaN')
            for key,expected in [('grand_total',total),('outstanding_amount',outstanding)]:
                actual=Decimal(row.get(key,''))
                if not actual.is_finite() or actual!=expected.quantize(Decimal('0.01')):
                    errors.append(f'{ident}: niezgodna kwota {key}.')
            status='OPLACONA' if outstanding<=0 else ('CZESCIOWO OPLACONA' if outstanding<total else 'NIEOPLACONA')
            if row.get('payment_status')!=status: errors.append(f'{ident}: błędny payment_status, oczekiwano {status}.')
        except (InvalidOperation,ValueError,KeyError):
            errors.append(f'{ident}: kwota nie jest poprawną liczbą dziesiętną.')
        ids=sorted({str(i['sales_order']) for i in doc.get('items',[]) if i.get('sales_order')})
        if row.get('sales_orders')!=','.join(ids): errors.append(f'{ident}: niezgodne lub powtórzone powiązania Sales Order.')
        if doc.get('docstatus')!=1: errors.append(f'{ident}: JSON nie jest zatwierdzoną fakturą (docstatus != 1).')
        pdf=row.get('pdf_file','')
        if not pdf or pdf.startswith('BLAD:'):
            warnings.append(f'{ident}: PDF nie został pobrany; JSON/CSV mogą być poprawne.')
        elif Path(pdf).name!=pdf or '/' in pdf or '\\' in pdf:
            errors.append(f'{ident}: niebezpieczna ścieżka PDF.')
        else:
            try:
                if not (folder/'faktury_pdf'/pdf).read_bytes().startswith(b'%PDF-'):
                    errors.append(f'{ident}: plik nie ma nagłówka PDF.')
            except OSError:
                errors.append(f'{ident}: brak wskazanego pliku PDF.')
    return {'wynik':'BLAD' if errors else ('UWAGI' if warnings else 'ZGODNY_Z_LOKALNYM_JSON'),
            'bledy':errors,'uwagi':warnings,'liczba_faktur':len(rows)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--katalog',type=Path,default=ROOT/'wyniki')
    args=parser.parse_args(argv)
    result=check(args.katalog)
    result['czas_utc']=datetime.now(timezone.utc).isoformat()
    result['zakres']='Lokalna kontrola CSV ↔ JSON/PDF. Nie potwierdza świeżości kopii na serwerze ani całej semantyki księgowej.'
    print(json.dumps(result,ensure_ascii=False,indent=2))
    args.katalog.mkdir(parents=True,exist_ok=True)
    (args.katalog/'kontrola_csv.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return 1 if result['bledy'] else (2 if result['wynik'] in {'UWAGI','BRAK_DANYCH'} else 0)

if __name__=='__main__':raise SystemExit(main())
