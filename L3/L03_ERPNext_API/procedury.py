from __future__ import annotations
from collections import defaultdict
from csv import DictReader, DictWriter
from datetime import date
from decimal import Decimal
from pathlib import Path
import json
import hashlib
import re
from datetime import datetime, timezone
from erpnext_client import ERPNextClient, ERPNextAPIError
from konfiguracja import Konfiguracja
import zadania

ROOT=Path(__file__).resolve().parent
DANE=ROOT/'dane'; WYNIKI=ROOT/'wyniki'


def czytaj_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return [dict(r) for r in DictReader(f, delimiter=';')]


def zapisz_csv(path: Path, rows: list[dict], headers: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w=DictWriter(f, fieldnames=headers, delimiter=';'); w.writeheader(); w.writerows(rows)


def _prefiks(value: str, cfg: Konfiguracja) -> str:
    prefix=cfg.lab_prefix.strip()
    return f'{prefix}-{value}' if prefix else value


def _first(client: ERPNextClient, doctype: str, filters: list, fields=None):
    rows=client.lista(doctype, fields=fields or ['name'], filters=filters, limit=2)
    if len(rows)>1:
        raise RuntimeError(f'Niejednoznaczne dopasowanie {doctype}: {filters}')
    return rows[0] if rows else None


def _payload_klienta(row: dict, cfg: Konfiguracja) -> dict:
    return {k:v for k,v in {
        'customer_name': _prefiks(row['customer_name'].strip(), cfg),
        'customer_type': row['customer_type'].strip(),
        'customer_group': row.get('customer_group','').strip() or cfg.customer_group,
        'territory': row.get('territory','').strip() or cfg.territory,
        'tax_id': row.get('tax_id','').strip(),
        'email_id': row.get('email_id','').strip(),
        'mobile_no': row.get('mobile_no','').strip(),
    }.items() if v!=''}


def _payload_adresu(row: dict, customer_name: str) -> dict:
    return {k:v for k,v in {
        'address_title': customer_name,
        'address_type': 'Billing',
        'address_line1': row['address_line1'].strip(),
        'address_line2': row.get('address_line2','').strip(),
        'city': row['city'].strip(),
        'pincode': row.get('pincode','').strip(),
        'country': row['country'].strip(),
        'email_id': row.get('email_id','').strip(),
        'phone': row.get('mobile_no','').strip(),
        'is_primary_address': 1,
        'is_shipping_address': 1,
        'links': [{'link_doctype':'Customer','link_name':customer_name}],
    }.items() if v!=''}


def importuj_klientow(client: ERPNextClient, cfg: Konfiguracja) -> dict[str,str]:
    rows=czytaj_csv(DANE/'klienci.csv'); out=[]; mapping={}
    for row in rows:
        errors=zadania.waliduj_klienta(row)
        if not isinstance(errors, list):
            raise TypeError('waliduj_klienta musi zwracać listę błędów.')
        ext=row.get('external_customer_id','')
        if errors:
            out.append({'external_customer_id':ext,'customer_name':row.get('customer_name',''),'erpnext_name':'','status':'ODRZUCONY','details':' | '.join(errors)})
            continue
        expected_name=_prefiks(row['customer_name'].strip(),cfg)
        existing=_first(client,'Customer',[["Customer","customer_name","=",expected_name]],['name','customer_name'])
        if existing:
            customer=existing['name']; status='ISTNIEJE'
        else:
            customer=client.utworz('Customer',_payload_klienta(row,cfg))['name']; status='UTWORZONY'
        mapping[ext]=customer
        # Adres jest opcjonalny dla Customer, ale wymagany dla realistycznego wydruku.
        addr=_first(client,'Address',[["Address","address_title","=",customer],["Address","city","=",row['city']]],['name'])
        if not addr:
            client.utworz('Address',_payload_adresu(row,customer))
        out.append({'external_customer_id':ext,'customer_name':row['customer_name'],'erpnext_name':customer,'status':status,'details':''})
    WYNIKI.mkdir(exist_ok=True)
    (WYNIKI/'mapowanie_klientow.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
    zapisz_csv(WYNIKI/'import_klientow.csv',out,['external_customer_id','customer_name','erpnext_name','status','details'])
    return mapping


def _group_orders(rows: list[dict[str,str]]) -> dict[str,list[dict[str,str]]]:
    grouped=defaultdict(list)
    for r in rows: grouped[r.get('external_order_id','')].append(r)
    return dict(grouped)


def _payload_zamowienia(lines: list[dict[str,str]], customer: str, cfg: Konfiguracja) -> dict:
    head=lines[0]
    return {
        'naming_series': cfg.sales_order_naming_series,
        'customer': customer,
        'order_type': 'Sales',
        'transaction_date': head['transaction_date'],
        'delivery_date': head['delivery_date'],
        'po_no': _prefiks(head.get('po_no') or head['external_order_id'], cfg),
        'company': cfg.company,
        'currency': cfg.currency,
        'conversion_rate': 1,
        'selling_price_list': cfg.selling_price_list,
        'price_list_currency': cfg.currency,
        'plc_conversion_rate': 1,
        'items': [
            {
                'item_code': r['item_code'],
                'item_name': r['item_name'],
                'qty': float(Decimal(r['qty'])),
                'rate': float(Decimal(r['rate'])),
                'uom': r['uom'],
                'conversion_factor': 1,
                'delivery_date': head['delivery_date'],
            } for r in lines
        ],
    }


def importuj_zamowienia(client: ERPNextClient, cfg: Konfiguracja) -> list[dict]:
    map_path=WYNIKI/'mapowanie_klientow.json'
    if not map_path.exists():
        raise RuntimeError('Najpierw uruchom import klientów.')
    mapping=json.loads(map_path.read_text(encoding='utf-8'))
    grouped=_group_orders(czytaj_csv(DANE/'zamowienia.csv')); out=[]
    for ext_id, lines in grouped.items():
        errors=zadania.waliduj_zamowienie(lines)
        if not isinstance(errors, list):
            raise TypeError('waliduj_zamowienie musi zwracać listę błędów.')
        customer_ext=lines[0].get('customer_external_id','') if lines else ''
        customer=mapping.get(customer_ext)
        if not customer: errors.append(f'brak mapowania klienta {customer_ext}')
        if errors:
            out.append({'external_order_id':ext_id,'erpnext_name':'','customer':customer or '', 'status':'ODRZUCONY','details':' | '.join(errors)})
            continue
        expected_po=_prefiks(lines[0].get('po_no') or ext_id,cfg)
        existing=_first(client,'Sales Order',[["Sales Order","po_no","=",expected_po],["Sales Order","company","=",cfg.company]],['name','docstatus'])
        if existing:
            name=existing['name']; status='ISTNIEJE'
        else:
            doc=client.utworz('Sales Order',_payload_zamowienia(lines,customer,cfg)); name=doc['name']; status='UTWORZONY_DRAFT'
        out.append({'external_order_id':ext_id,'erpnext_name':name,'customer':customer,'status':status,'details':''})
    zapisz_csv(WYNIKI/'import_zamowien.csv',out,['external_order_id','erpnext_name','customer','status','details'])
    return out


def eksportuj_faktury(client: ERPNextClient, cfg: Konfiguracja, *, debug=False, prepared=None) -> list[dict]:
    """Pobierz CSV/PDF; puste lub błędne wyniki Z4 nie są milcząco pomijane.

    debug: lista wszystkich nagłówków widocznych tokenowi, przed filtrami.
    prepared: zrzut z wcześniejszej diagnostyki tej samej operacji (bez drugiego odczytu).
    """
    from diagnostyka_faktur import zbierz, HEADERS
    batch = prepared or zbierz(client, cfg, WYNIKI, all_visible=debug)
    dump = batch['dump']
    if dump.summary['bledy'] or not batch['scope_complete']:
        raise RuntimeError('Eksport przerwany; nie nadpisano faktury.csv. Szczegóły: '+str(dump.folder/'podsumowanie.json'))
    out = batch['rows']
    if not out:
        dump.summary['stan'] = 'BRAK_EKSPORTU'
        dump.finish()
        print('UWAGA: 0 faktur po filtrach. Z4 nie jest wywoływane dla odrzuconych faktur.')
        print('Sprawdź EXPORT_FROM_DATE, Customer.name w mapowaniu, Company i docstatus. Uruchom diagnostyka-faktur.')
        if not (WYNIKI/'faktury.csv').exists():
            zapisz_csv(WYNIKI/'faktury.csv', [], HEADERS)
        else:
            print('Pozostawiono wcześniejszy faktury.csv — NIE jest wynikiem obecnej operacji.')
        return []
    pdf_dir=WYNIKI/'faktury_pdf'; json_dir=WYNIKI/'faktury_json'
    pdf_dir.mkdir(parents=True,exist_ok=True); json_dir.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for row in out:
        name=row['invoice_id']; doc=batch['documents'][name]
        safe=re.sub(r'[^A-Za-z0-9._-]+','_',name).strip('._')[:100] + '_' + hashlib.sha256(name.encode()).hexdigest()[:12]
        json_path=json_dir/f'{safe}.json'
        json_path.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
        pdf_name=f'{safe}.pdf'; pdf_status=pdf_name
        try:
            pdf=client.pobierz_pdf('Sales Invoice',name,cfg.print_format)
            if not pdf.startswith(b'%PDF-'): raise ValueError('Odpowiedź nie ma nagłówka PDF.')
            (pdf_dir/pdf_name).write_bytes(pdf)
        except Exception as exc:
            pdf_status='BLAD: '+str(exc)
            for secret in (cfg.api_key,cfg.api_secret):
                if secret: pdf_status=pdf_status.replace(secret,'[UKRYTO]')
            dump.summary['uwagi'].append(name+': '+pdf_status)
        row['pdf_file']=pdf_status
        manifest.append({'invoice_id':name,'json_file':json_path.name,
            'json_sha256':hashlib.sha256(json_path.read_bytes()).hexdigest(),
            'pdf_file':pdf_name if not pdf_status.startswith('BLAD:') else None})
    # Atomowy zapis końcowego CSV. Brak częściowego zastąpienia poprzedniego wyniku.
    temporary=WYNIKI/'faktury.csv.tmp'
    zapisz_csv(temporary,out,HEADERS)
    temporary.replace(WYNIKI/'faktury.csv')
    (WYNIKI/'eksport_manifest.json').write_text(json.dumps({
        'czas_utc':datetime.now(timezone.utc).isoformat(),'company':cfg.company,
        'export_from_date':cfg.export_from_date,'diagnostyka_katalog':str(dump.folder),
        'invoices':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    dump.save('07_wiersze_zapisane_csv.json',out)
    dump.summary.update(stan='ZAPISANO_CSV',liczba_wyeksportowanych=len(out))
    dump.finish()
    return out
