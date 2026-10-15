"""Diagnostyka L03: lokalne pliki + odczyt ERPNext. Bez importu i bez Submit.
Uruchom: py -3 00_start.py
Opcje: --offline | --po-imporcie | --invoice "NUMER_FAKTURY"
Nie importuje zadania.py: niedokończone zadania nie blokują kontroli serwera.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryFile

ROOT = Path(__file__).resolve().parent


class Raport:
    def __init__(self, cfg=None):
        self.checks = []
        self.cfg = cfg

    def add(self, status, test, details):
        details = str(details)
        if self.cfg:
            for secret in (self.cfg.api_key, self.cfg.api_secret):
                if secret:
                    details = details.replace(secret, '[UKRYTO]')
        self.checks.append({'status': status, 'test': test, 'opis': details})
        print(f'[{status:7}] {test}: {details}', flush=True)

    def save(self, offline=False):
        counts = Counter(c['status'] for c in self.checks)
        state = 'BLEDY' if counts['BLAD'] else ('DO_WERYFIKACJI' if counts['UWAGA'] else ('LOKALNE_OK' if offline else 'KONTROLE_ODCZYTU_OK'))
        data = {'wersja': 'L03-r3', 'czas_utc': datetime.now(timezone.utc).isoformat(),
                'wynik': state, 'offline': offline, 'kontrole': self.checks,
                'ograniczenia': 'To kontrola odczytu i ustawień. Nie potwierdza walidacji zapisu/Submit ani pełnej konfiguracji księgowej. Bez --invoice PDF nie jest testowany.'}
        try:
            target = ROOT / 'wyniki'
            target.mkdir(exist_ok=True)
            (target / 'diagnostyka_start.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            (target / 'diagnostyka_start.txt').write_text('\n'.join(f"[{c['status']}] {c['test']}: {c['opis']}" for c in self.checks) + '\n' + state + '\n' + data['ograniczenia'], encoding='utf-8')
            print('\nRaport: wyniki/diagnostyka_start.json i diagnostyka_start.txt')
        except OSError as exc:
            print('Nie udało się zapisać raportu:', exc)
            return 1
        print('WYNIK:', state)
        return 1 if counts['BLAD'] else (2 if counts['UWAGA'] else 0)


def load_csv(filename, required, report):
    path = ROOT / 'dane' / filename
    try:
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            missing = set(required) - set(reader.fieldnames or [])
            if missing:
                raise ValueError('Brak kolumn: ' + ', '.join(sorted(missing)))
            rows = list(reader)
            if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
                raise ValueError('Pusty plik lub nierówna liczba pól w wierszach.')
        report.add('OK', filename, f'{len(rows)} wierszy; poprawne nagłówki i separator ;')
        return rows
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        report.add('BLAD', filename, exc)
        return []


def local_checks(report):
    for filename in ('zadania.py', 'procedury.py', 'konfiguracja.py', 'erpnext_client.py', 'uruchom.py'):
        try:
            source = (ROOT / filename).read_text(encoding='utf-8-sig')
            ast.parse(source, filename=filename)
            report.add('OK', filename, 'Plik istnieje i ma poprawną składnię. To nie jest ocena logiki funkcji.')
        except (OSError, SyntaxError, UnicodeError) as exc:
            report.add('BLAD', filename, f'{type(exc).__name__}; sprawdź plik w PyCharm.')
    try:
        (ROOT / 'wyniki').mkdir(exist_ok=True)
        with TemporaryFile(dir=ROOT / 'wyniki') as f:
            f.write(b'test')
        report.add('OK', 'Zapis lokalny', 'Katalog wyniki jest zapisywalny.')
    except OSError as exc:
        report.add('BLAD', 'Zapis lokalny', exc)
    customers = load_csv('klienci.csv', ('external_customer_id','customer_name','customer_type','address_line1','city','country'), report)
    orders = load_csv('zamowienia.csv', ('external_order_id','customer_external_id','transaction_date','delivery_date','po_no','item_code','item_name','qty','rate','uom'), report)
    items = load_csv('towary_wymagane.csv', ('item_code','item_name','item_group','stock_uom','is_stock_item','is_sales_item','standard_rate'), report)
    ids = [r['external_customer_id'].strip() for r in customers]
    if customers:
        report.add('OK' if '' not in ids and len(ids)==len(set(ids)) else 'BLAD', 'Klucze klientów', 'Wymagane unikalne, niepuste external_customer_id.')
    grouped = defaultdict(list)
    issues = []
    total = Decimal('0')
    for n, row in enumerate(orders, 2):
        grouped[row['external_order_id'].strip()].append(row)
        try:
            qty, rate = Decimal(row['qty']), Decimal(row['rate'])
            if not qty.is_finite() or not rate.is_finite() or qty <= 0 or rate <= 0:
                raise ValueError('qty/rate muszą być dodatnie i skończone')
            total += qty * rate
            if date.fromisoformat(row['delivery_date']) < date.fromisoformat(row['transaction_date']):
                raise ValueError('delivery_date przed transaction_date')
            if row['customer_external_id'] not in ids:
                raise ValueError('klient spoza pliku klientów')
            if not all(row[k].strip() for k in ('external_order_id','item_code','item_name','uom')):
                raise ValueError('puste pole wymagane')
        except (ValueError, InvalidOperation) as exc:
            issues.append(f'linia {n}: {exc}')
    for ident, lines in grouped.items():
        for key in ('customer_external_id', 'transaction_date', 'delivery_date', 'po_no'):
            if len({r[key] for r in lines}) > 1:
                issues.append(f'{ident}: niespójne {key}')
    pos = [r['po_no'] or key for key, lines in grouped.items() for r in lines[:1]]
    if len(pos) != len(set(pos)):
        issues.append('różne zamówienia mają ten sam po_no; importer używa go do ponowień')
    if orders:
        report.add('BLAD' if issues else 'OK', 'Dane wsadowe (kontrola techniczna)', '; '.join(issues) if issues else f'{len(grouped)} zamówień, {len(orders)} pozycji, suma qty*rate={total:.2f}. Bez podatków i przeliczeń ERP.')
    report.add('INFO', 'zadania.py', 'Logikę studenta sprawdza oddzielnie: py -3 sprawdz_zadania.py. Start nie wykonuje ciał funkcji.')
    return customers, orders, items


def remote_checks(report, client, cfg, customers, orders, items, *, after_import=False, invoice=None):
    from erpnext_client import ERPNextAPIError
    cache = {}
    def read(dt, name, required=True):
        key = (dt, name)
        if key in cache:
            return cache[key]
        try:
            doc = client.pobierz(dt, name)
            report.add('OK', f'{dt}: {name}', 'Rekord widoczny dla użytkownika API.')
            cache[key] = doc
            return doc
        except ERPNextAPIError as exc:
            if exc.status == 404:
                text = 'Nie znaleziono pod wskazaną nazwą. Sprawdź dokładne ID w ERPNext.'
            elif exc.status in (401,403):
                text = 'Brak uprawnień do odczytu; NIE dowodzi to braku rekordu. Zweryfikuj z administratorem.'
            else:
                text = str(exc)
            report.add('BLAD' if required else 'UWAGA', f'{dt}: {name}', text)
            cache[key] = None
            return None
    def flag(ok, title, good, bad, severity='BLAD'):
        report.add('OK' if ok else severity, title, good if ok else bad)

    try:
        user = client.sprawdz_polaczenie()
        report.add('OK', 'Uwierzytelnienie API', user)
    except ERPNextAPIError as exc:
        report.add('BLAD', 'Uwierzytelnienie API', exc)
        report.add('POMINIETO', 'Dane serwera', 'Brak poprawnego połączenia. Nie wykonano dalszych testów ERPNext.')
        return
    if not cfg.verify_tls:
        report.add('UWAGA', 'TLS', 'VERIFY_TLS=false: certyfikat nie jest sprawdzany. Zalecane poprawne HTTPS; skrypt nie wyłącza TLS samodzielnie.')
    if cfg.base_url.startswith('http:'):
        report.add('UWAGA', 'HTTP', 'Token jest przesyłany bez szyfrowania. Użyj HTTPS; HTTP wyłącznie w kontrolowanym laboratorium.')
    report.add('INFO', 'EXPORT_FROM_DATE', cfg.export_from_date + '; dotyczy posting_date faktury, nie daty zamówienia.')
    if cfg.export_from_date > date.today().isoformat():
        report.add('UWAGA', 'Przyszła data eksportu', 'Faktury z wcześniejszą posting_date zostaną pominięte. W pierwotnym przykładzie było 2026-10-16.')
    if not cfg.lab_prefix:
        report.add('UWAGA', 'LAB_PREFIX', 'Pusty prefiks jest dopuszczalny tylko przy oddzielnej witrynie zespołu.')
    else:
        report.add('INFO', 'LAB_PREFIX', f'{cfg.lab_prefix}; prefiks zapobiega kolizjom nazw, ale NIE zastępuje uprawnień.')
    company = read('Company', cfg.company)
    if company:
        flag(company.get('default_currency') == cfg.currency, 'Waluta firmy', cfg.currency,
             'Firma ma inną walutę niż CURRENCY. Ten importer stosuje conversion_rate=1, więc wymaga jednej waluty.')
    currency = read('Currency', cfg.currency)
    if currency:
        flag(bool(currency.get('enabled', 1)), 'Waluta aktywna', cfg.currency, 'Wyłączona waluta.')
    price = read('Price List', cfg.selling_price_list)
    if price:
        flag(bool(price.get('enabled', 1)) and bool(price.get('selling')), 'Cennik sprzedaży', 'Aktywny cennik sprzedaży.', 'Cennik jest wyłączony albo nie jest sprzedażowy.')
        flag(price.get('currency') == cfg.currency, 'Waluta cennika', cfg.currency, 'Waluta cennika nie odpowiada CURRENCY; importer stosuje kurs 1.')
    groups = {cfg.customer_group} | {r.get('customer_group','').strip() for r in customers if r.get('customer_group','').strip()}
    for name in sorted(groups):
        doc = read('Customer Group', name)
        if doc:
            flag(not doc.get('is_group'), 'Grupa klientów: ' + name, 'Grupa końcowa.', 'Wybierz grupę końcową, nie węzeł nadrzędny.')
    for name in sorted({cfg.territory} | {r.get('territory','').strip() for r in customers if r.get('territory','').strip()}):
        read('Territory', name)
    for name in sorted({r['country'] for r in customers}):
        read('Country', name)
    for name in sorted({cfg.item_group} | {r['item_group'] for r in items}):
        doc = read('Item Group', name)
        if doc:
            flag(not doc.get('is_group'), 'Grupa pozycji: ' + name, 'Grupa końcowa.', 'Wybierz grupę końcową Item Group.')
    for unit in sorted({cfg.stock_uom} | {r['uom'] for r in orders} | {r['stock_uom'] for r in items}):
        doc = read('UOM', unit)
        if doc and doc.get('must_be_whole_number'):
            wrong = [r['external_order_id'] for r in orders if r['uom']==unit and Decimal(r['qty']) != Decimal(r['qty']).to_integral_value()]
            flag(not wrong, f'UOM całkowite: {unit}', 'Ilości są całkowite.', f'Ułamkowe ilości w: {wrong}')
    for code in sorted({r['item_code'] for r in orders} | {r['item_code'] for r in items}):
        doc = read('Item', code)
        if not doc:
            continue
        flag(not doc.get('disabled') and bool(doc.get('is_sales_item')) and not doc.get('has_variants'), f'Item aktywny: {code}', 'Aktywny produkt/usługa sprzedażowa, nie szablon wariantów.', 'Item wyłączony, niesprzedażowy lub szablon wariantów.')
        flag(not doc.get('is_stock_item'), f'Usługa: {code}', 'is_stock_item=0 — scenariusz bez Delivery Note.', 'Pozycja magazynowa. Do tego ćwiczenia użyj usługi; nie zmieniaj istniejących kartotek produkcyjnych.')
        units = {r['uom'] for r in orders if r['item_code']==code}
        flag(not units or units == {doc.get('stock_uom')}, f'Jednostka pozycji: {code}', 'UOM zamówienia równe stock_uom; conversion_factor=1.', 'UOM niezgodne; ten prosty importer nie wylicza innych przeliczników.')
        if doc.get('end_of_life'):
            try:
                latest = max((r['transaction_date'] for r in orders if r['item_code']==code), default=date.today().isoformat())
                flag(doc['end_of_life'] >= latest, f'Ważność Item: {code}', doc['end_of_life'], 'Koniec ważności przed datą zamówienia.')
            except TypeError:
                report.add('UWAGA', f'Ważność Item: {code}', 'Nieobsługiwany format daty; sprawdź w UI.')
    for dt, types in {'Customer':('read','create'), 'Address':('read','create'), 'Sales Order':('read','create','write','submit'), 'Sales Invoice':('read','create','write','submit','print')}.items():
        for permission in types:
            try:
                has = client.uprawnienie(dt, permission)
                flag(has, f'Uprawnienie {dt}/{permission}', 'Uprawnienie na poziomie DocType; dokument może mieć dodatkowe ograniczenia.', 'Brak uprawnienia. Administrator powinien ustawić minimalny właściwy zakres, nie pełnego Administratora.')
            except ERPNextAPIError as exc:
                report.add('UWAGA', f'Uprawnienie {dt}/{permission}', f'Nie zweryfikowano metody na tej wersji: {exc}')
        try:
            fs = [[dt,'company','=',cfg.company]] if dt in ('Sales Order','Sales Invoice') else []
            rows = client.lista(dt, filters=fs, limit=1)
            report.add('OK', f'Lista {dt}', f'Odczyt działa; {len(rows)} rekordów próbki. Pusta lista przed importem jest dopuszczalna.')
        except ERPNextAPIError as exc:
            report.add('BLAD', f'Lista {dt}', exc)
    for dt in ('Customer','Address','Sales Order','Sales Invoice'):
        try:
            bundle = client.metadane(dt)
            main = next((d for d in bundle if d.get('name')==dt), {})
            if not main:
                raise ERPNextAPIError('Brak głównego formularza w metadanych.')
            report.add('OK', f'Schemat {dt}', 'Odczytano metadane formularza i tabel podrzędnych.')
            extra = [d.get('name','?')+'.'+f.get('fieldname','?') for d in bundle for f in d.get('fields',[]) if f.get('fieldname','').startswith('custom_') and f.get('reqd') and not f.get('default') and not f.get('read_only')]
            if extra:
                report.add('UWAGA', f'Dodatkowe wymagane pola {dt}', ', '.join(extra) + '. Domyślne reguły serwera mogą je uzupełniać; sprawdź przed importem.')
            if dt == 'Sales Order':
                field = next((f for f in main.get('fields',[]) if f.get('fieldname')=='naming_series'), {})
                options = str(field.get('options') or '').splitlines()
                if not options:
                    report.add('UWAGA', 'Numeracja Sales Order', 'Brak listy serii w schemacie; potwierdź w ERPNext.')
                else:
                    flag(cfg.sales_order_naming_series in options, 'Numeracja Sales Order', cfg.sales_order_naming_series, 'Seria z konfiguracji nie występuje w opcjach formularza.', severity='UWAGA')
        except ERPNextAPIError as exc:
            report.add('UWAGA', f'Schemat {dt}', f'Nie zweryfikowano: {exc}. Nie oznacza to automatycznie braku ERPNext.')
    if company:
        for field in ('default_receivable_account','default_income_account','cost_center'):
            value = company.get(field)
            if not value:
                report.add('UWAGA', f'Firma/{field}', 'Brak domyślnej wartości. Możliwe ustawienie na kliencie, Item/Item Group lub ręcznie; zatwierdzenie faktury wymaga pilotażu.')
                continue
            dt = 'Cost Center' if field=='cost_center' else 'Account'
            acc = read(dt, value, required=False)
            if acc:
                flag(acc.get('company') == cfg.company and not acc.get('is_group') and not acc.get('disabled'), f'Powiązanie {field}', 'Aktywny rekord końcowy właściwej firmy.', 'Sprawdź firmę, is_group i disabled rekordu.', severity='UWAGA')
    if cfg.print_format != 'Standard':
        fmt = read('Print Format', cfg.print_format, required=False)
        if fmt:
            flag(fmt.get('doc_type')=='Sales Invoice' and not fmt.get('disabled'), 'Format faktury', 'Format Sales Invoice.', 'Format nie dotyczy faktury lub jest wyłączony.', severity='UWAGA')
    else:
        report.add('INFO', 'Format Standard', 'Wbudowany format: brak osobnego rekordu Print Format o nazwie Standard nie jest błędem.')
    report.add('INFO', 'Zakres kontroli', 'Nie wykonano POST, Submit ani zmian dokumentów biznesowych. Podatki, workflow, rok fiskalny i walidacje serwera wymagają pilotażu na instancji szkoleniowej.')
    if after_import:
        check_import(report, client, cfg, customers, orders)
    else:
        report.add('INFO', 'Klienci i zamówienia ćwiczenia', 'Przed importem nie muszą istnieć. Po imporcie: py -3 00_start.py --po-imporcie')
    if invoice:
        doc = read('Sales Invoice', invoice)
        if doc:
            flag(doc.get('company')==cfg.company, 'Firma faktury', cfg.company, 'Faktura innej firmy.')
            flag(doc.get('docstatus')==1, 'Zatwierdzona faktura', 'docstatus=1', 'Eksporter pobiera wyłącznie docstatus=1.')
            flag(str(doc.get('posting_date',''))>=cfg.export_from_date, 'Data eksportu', str(doc.get('posting_date')), 'Faktura jest wcześniejsza niż EXPORT_FROM_DATE.')
            map_path = ROOT/'wyniki/mapowanie_klientow.json'
            if map_path.exists():
                try:
                    mapping = json.loads(map_path.read_text(encoding='utf-8'))
                    flag(doc.get('customer') in mapping.values(), 'Zakres klientów faktury', 'Klient w lokalnym mapowaniu.', 'Eksporter nie uwzględni klienta spoza mapowania.')
                except (OSError, ValueError):
                    report.add('UWAGA', 'Mapowanie faktury', 'Nie można odczytać mapowania lokalnego.')
            try:
                data = client.pobierz_pdf('Sales Invoice', invoice, cfg.print_format)
                flag(data.startswith(b'%PDF-'), 'Generator PDF', f'Odebrano {len(data)} bajtów; nagłówek %PDF-. Plik nie jest tu zapisywany.', 'Odpowiedź nie jest PDF.')
            except ERPNextAPIError as exc:
                report.add('BLAD', 'Generator PDF', exc)
    else:
        report.add('POMINIETO', 'Generator PDF', 'Do testu potrzeba konkretnej faktury: py -3 00_start.py --invoice NUMER. Nie tworzę pustej faktury testowej.')


def check_import(report, client, cfg, customers, orders):
    from erpnext_client import ERPNextAPIError
    prefix = lambda value: f'{cfg.lab_prefix}-{value}' if cfg.lab_prefix else value
    found_customers = {}
    for row in customers:
        try:
            result = client.lista('Customer', filters=[['Customer','customer_name','=',prefix(row['customer_name'].strip())]], limit=2)
            if len(result)!=1:
                report.add('BLAD', 'Import klienta ' + row['external_customer_id'], f'Widoczne dopasowania: {len(result)}. Oczekiwano dokładnie jednego; sprawdź import lub uprawnienia.')
            else:
                found_customers[row['external_customer_id']] = result[0]['name']
                report.add('OK', 'Import klienta ' + row['external_customer_id'], result[0]['name'])
                addresses=client.lista('Address', filters=[['Address','address_title','=',result[0]['name']],['Address','city','=',row['city']]], limit=2)
                if len(addresses)!=1:
                    report.add('BLAD','Adres klienta '+row['external_customer_id'],f'Widoczne dopasowania: {len(addresses)}; oczekiwano jednego adresu z importu.')
                else:
                    address=client.pobierz('Address',addresses[0]['name'])
                    linked=any(link.get('link_doctype')=='Customer' and link.get('link_name')==result[0]['name'] for link in address.get('links',[]))
                    correct=linked and address.get('country')==row['country'] and address.get('address_line1')==row['address_line1']
                    report.add('OK' if correct else 'BLAD','Adres klienta '+row['external_customer_id'],'Sprawdzono powiązanie Customer, kraj i ulicę.')
        except ERPNextAPIError as exc:
            report.add('BLAD', 'Import klienta', exc)
    grouped = defaultdict(list)
    for row in orders:
        grouped[row['external_order_id']].append(row)
    for ident, lines in grouped.items():
        try:
            expected_po = prefix(lines[0].get('po_no') or ident)
            docs = client.lista('Sales Order', filters=[['Sales Order','po_no','=',expected_po], ['Sales Order','company','=',cfg.company]], limit=2)
            if len(docs)!=1:
                report.add('BLAD', f'Import zamówienia {ident}', f'Widoczne dopasowania: {len(docs)}; sprawdź import/uprawnienia.')
                continue
            doc = client.pobierz('Sales Order', docs[0]['name'])
            expected = Counter((r['item_code'], Decimal(r['qty']), Decimal(r['rate']), r['uom']) for r in lines)
            actual = Counter((r.get('item_code'), Decimal(str(r.get('qty',0))), Decimal(str(r.get('rate',0))), r.get('uom')) for r in doc.get('items',[]))
            ok = expected==actual and doc.get('customer')==found_customers.get(lines[0]['customer_external_id']) and doc.get('currency')==cfg.currency
            report.add('OK' if ok else 'BLAD', f'Import zamówienia {ident}', f"{doc['name']}; docstatus={doc.get('docstatus')}; zgodność klienta, waluty, kodów, ilości i stawek: {ok}. Podatki i rabaty mogą zmieniać sumę.")
        except (ERPNextAPIError, ValueError, InvalidOperation) as exc:
            report.add('BLAD', f'Import zamówienia {ident}', exc)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Tylko pliki i składnia; bez sieci i bez erpnext.env.')
    parser.add_argument('--po-imporcie', action='store_true', help='Dodatkowo sprawdź rekordy klientów i zamówień z CSV.')
    parser.add_argument('--invoice', help='Numer istniejącej faktury do odczytu i próby PDF.')
    parser.add_argument('--timeout', type=float, default=12, help='Limit sekund pojedynczego żądania; domyślnie 12.')
    args = parser.parse_args(argv)
    report = Raport()
    if sys.version_info < (3,10):
        report.add('BLAD', 'Python', 'Wymagany Python 3.10+.')
        return report.save(args.offline)
    report.add('OK', 'Python', sys.version.split()[0])
    customers, orders, items = local_checks(report)
    if args.offline:
        report.add('POMINIETO', 'ERPNext', 'Tryb offline: nie sprawdzono autoryzacji, danych serwera, uprawnień ani PDF.')
        return report.save(True)
    if any(c['status']=='BLAD' for c in report.checks):
        report.add('POMINIETO', 'ERPNext', 'Najpierw usuń błędy lokalnych plików.')
        return report.save()
    try:
        from konfiguracja import wczytaj_konfiguracje, BladKonfiguracji
        from erpnext_client import ERPNextClient
        cfg = wczytaj_konfiguracje()
        report.cfg = cfg
        report.add('OK', 'erpnext.env', 'Wymagane pola uzupełnione. Sekrety nie są wyświetlane.')
        remote_checks(report, ERPNextClient(cfg, timeout=max(1,min(args.timeout,60))), cfg, customers, orders, items,
                      after_import=args.po_imporcie, invoice=args.invoice)
    except (RuntimeError, ValueError, OSError, ImportError) as exc:
        report.add('BLAD', 'Konfiguracja/diagnostyka', str(exc))
    return report.save()


if __name__ == '__main__':
    raise SystemExit(main())
