"""Zrzuty wejścia API, kolejnych filtrów i wejścia/wyjścia zadania.py.

GET wyłącznie: bez importu, bez Submit, bez pobierania PDF w trybie diagnostycznym.
Dane są widoczne dla użytkownika TOKENU (niekoniecznie konta w przeglądarce).
Pełne dokumenty pobieramy tylko dla faktur spełniających zakres ćwiczenia.
"""
from __future__ import annotations
import copy
import hashlib
import importlib
import json
import math
import sys
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
HEADERS = ['invoice_id','customer','posting_date','currency','grand_total',
           'outstanding_amount','payment_status','sales_orders','erpnext_status','docstatus','pdf_file']
FIELDS = ['name','customer','customer_name','company','posting_date','docstatus',
          'status','currency','grand_total','outstanding_amount']


def _clean(value, cfg):
    """Bez nagłówków Authorization/sekretów; dodatkowe zabezpieczenie treści błędów."""
    if isinstance(value, dict):
        return {str(k): ('[UKRYTO]' if str(k).lower() in {'api_key','api_secret','authorization','password'}
                        else _clean(v, cfg)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v, cfg) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {'__niepoprawna_liczba__': str(value)}
    if isinstance(value, str):
        for secret in (cfg.api_key, cfg.api_secret):
            if secret:
                value = value.replace(secret, '[UKRYTO]')
    return value


def _json_default(value):
    if isinstance(value, (Decimal, Path, date)):
        return str(value)
    # Zachowaj informację, że funkcja zwróciła niedozwolony typ.
    return {'__nieobslugiwany_typ__': type(value).__name__, 'repr': repr(value)[:200]}


class Dump:
    def __init__(self, folder, cfg):
        self.cfg = cfg
        self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=False)
        ignore = self.folder.parent / '.gitignore'
        if not ignore.exists():
            ignore.write_text('*\n', encoding='utf-8')
        self.context = {}
        self.summary = {'wersja': 'L03-r3-diagnostyka', 'stan': 'ROZPOCZETO',
                        'liczba_widocznych_api': 0, 'liczba_po_filtrach': 0,
                        'wywolania_wiersz_faktury_csv': 0, 'wywolania_status_rozliczenia': 0,
                        'liczba_wierszy_poprawnych_strukturalnie': 0, 'bledy': [], 'uwagi': []}
        for filename in ('01_faktury_widoczne_api.json', '02_ocena_filtrow.json',
                         '03_faktury_po_filtrach.json', '04_wejscie_zadania.json',
                         '05_wyjscie_zadania.json', '06_pominiete_lub_bledy.json'):
            self.save(filename, [])
        self.save('podsumowanie.json', self.summary)

    def save(self, name, value):
        path = self.folder / name
        temp = path.with_suffix('.tmp')
        text = json.dumps(_clean(value, self.cfg), ensure_ascii=False, indent=2, default=_json_default, allow_nan=False)
        temp.write_text(text, encoding='utf-8')
        temp.replace(path)

    def finish(self):
        self.save('podsumowanie.json', self.summary)
        text = [f'Wynik: {self.summary["stan"]}',
                f'API widoczne: {self.summary["liczba_widocznych_api"]}',
                f'Po filtrach: {self.summary["liczba_po_filtrach"]}',
                f'Wywołania Z4: {self.summary["wywolania_wiersz_faktury_csv"]}',
                f'Wywołania Z3: {self.summary["wywolania_status_rozliczenia"]}',
                'Brak odwołania sales_order NIE jest filtrem w tym ćwiczeniu.',
                'Widoczność API zależy od konta tokenu i ograniczeń serwera.',
                'To nie jest migawka transakcyjna ERPNext. Odczytuj przy stabilnym zbiorze.']
        text += ['BŁĄD: ' + e for e in self.summary['bledy']]
        text += ['UWAGA: ' + e for e in self.summary['uwagi']]
        (self.folder/'podsumowanie.txt').write_text(_clean('\n'.join(text)+'\n', self.cfg), encoding='utf-8')


def powody(doc, cfg, customers):
    """Filtry programu, NIE funkcje studenta. Wszystkie przyczyny odrzucenia."""
    reasons = []
    if doc.get('company') != cfg.company:
        reasons.append('INNA_FIRMA' if doc.get('company') else 'BRAK_POLA_COMPANY')
    if doc.get('customer') not in customers:
        reasons.append('KLIENT_POZA_MAPOWANIEM')
    status = doc.get('docstatus')
    if str(status) != '1':
        reasons.append({'0':'DRAFT_DOCSTATUS_0','2':'ANULOWANA_DOCSTATUS_2'}.get(str(status),'DOCSTATUS_NIE_1'))
    try:
        posting = date.fromisoformat(str(doc.get('posting_date','')))
        if posting < date.fromisoformat(cfg.export_from_date):
            reasons.append('DATA_PRZED_EXPORT_FROM_DATE')
    except ValueError:
        reasons.append('BRAK_LUB_BLEDNA_POSTING_DATE')
    return reasons


def _check_row(row, name):
    """Sprawdzenie struktury, nie zastępstwo obliczeń studenta."""
    if not isinstance(row, dict):
        raise TypeError('Z4 musi zwracać dict; otrzymano '+type(row).__name__+'. None/[] nie jest filtrem.')
    if set(row) != set(HEADERS):
        raise ValueError('Z4: niezgodne kolumny. Brak: '+str(sorted(set(HEADERS)-set(row)))+'; dodatkowe: '+str(sorted(set(row)-set(HEADERS))))
    if row['invoice_id'] != name:
        raise ValueError('Z4: invoice_id różni się od name pobranej faktury.')
    if not all(isinstance(v, str) for v in row.values()):
        raise TypeError('Z4: zgodnie z kontraktem wartości wiersza CSV muszą być tekstami.')
    for key in ('grand_total','outstanding_amount'):
        if not Decimal(row[key]).is_finite():
            raise ValueError('Z4: kwota niefinitywna w '+key)
    if row['payment_status'] not in {'OPLACONA','CZESCIOWO OPLACONA','NIEOPLACONA'}:
        raise ValueError('Z4: niedozwolone payment_status; sprawdź też Z3.')


def zbierz(client, cfg, wyniki: Path, *, all_visible=True, use_tasks=True, max_pages=1000, user=None):
    """Zwraca dokumenty, wyjścia Z4 i zrzuty. Nigdy nie wykonuje POST.

    all_visible=True: lista wszystkich nagłówków widocznych dla tokenu, bez
    lokalnych filtrów na firmę/klienta/datę/status. To jawny tryb --debug.
    False: źródłowe listy ograniczone klientami i firmą; filtry nadal oceniane
    ponownie lokalnie. Zrzut wyraźnie opisuje swój zakres.
    """
    wyniki = Path(wyniki)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'_'+uuid4().hex[:6]
    dump = Dump(wyniki/'diagnostyka_faktur'/run_id, cfg)
    state = {'dump': dump, 'documents': {}, 'rows': [], 'function_errors': [], 'scope_complete': False}
    visible, evaluated, selected, inputs, outputs, omitted = [], [], [], [], [], []
    try:
        mapping_path = wyniki/'mapowanie_klientow.json'
        mapping_error = None
        try:
            mapping = json.loads(mapping_path.read_text(encoding='utf-8-sig'))
            if not isinstance(mapping, dict) or not all(isinstance(v, str) and v.strip() for v in mapping.values()):
                raise ValueError('Oczekiwano obiektu external_customer_id → niepusty Customer.name.')
        except (OSError, ValueError) as exc:
            mapping = {}
            mapping_error = 'Nie odczytano poprawnego mapowania: '+str(exc)
            dump.summary['bledy'].append(mapping_error)
        customers = sorted(set(mapping.values()))
        if not customers and not mapping_error:
            dump.summary['uwagi'].append('Mapowanie klientów jest puste: żadna faktura nie przejdzie zakresu klienta.')
        task_path = ROOT/'zadania.py'
        dump.context = {
            'czas_utc': datetime.now(timezone.utc).isoformat(), 'base_url': cfg.base_url,
            'uzytkownik_api': user, 'tryb': 'DIAGNOSTYKA_ODCZYTOWA',
            'zakres_listy': 'WSZYSTKIE_WIDOCZNE_TOKENOWI' if all_visible else 'KLIENCI_Z_MAPOWANIA_I_COMPANY',
            'company': cfg.company, 'export_from_date': cfg.export_from_date,
            'docstatus': 1, 'lab_prefix': cfg.lab_prefix,
            'mapowanie_path': str(mapping_path.resolve()), 'mapowanie_klientow': mapping,
            'zadania_path': str(task_path),
            'zadania_sha256': hashlib.sha256(task_path.read_bytes()).hexdigest() if task_path.is_file() else None,
            'fields': FIELDS, 'filters_requests': [],
            'bez_zadan': not use_tasks, 'bez_pdf': True,
            'uwaga': 'Brak filtrowania po Sales Order; sales_orders jest polem wyniku. API Secret i Authorization nie są logowane.'}
        dump.save('00_kontekst.json', dump.context)
        if cfg.export_from_date > date.today().isoformat():
            dump.summary['uwagi'].append('EXPORT_FROM_DATE jest późniejsze niż lokalna data komputera. Sprawdź czy jest zamierzone.')
        queries = [[]] if all_visible else [
            [['Sales Invoice','customer','=',c],['Sales Invoice','company','=',cfg.company]] for c in customers]
        seen_all = set()
        for filters in queries:
            dump.context['filters_requests'].append(filters)
            dump.save('00_kontekst.json', dump.context)
            start, seen_query = 0, set()
            for page in range(max_pages):
                records = client.lista('Sales Invoice', fields=FIELDS, filters=filters, limit=100, start=start)
                if not records:
                    break
                for record in records:
                    name = record.get('name')
                    if not name or name in seen_query:
                        raise ValueError('Powtórzona strona lub brak name w liście. Wynik NIE jest kompletny.')
                    seen_query.add(name)
                    if name not in seen_all:
                        visible.append(copy.deepcopy(record)); seen_all.add(name)
                start += len(records)
                # Nie kończymy na krótkiej stronie: serwer może obcinać page_length.
                dump.save('01_faktury_widoczne_api.json', visible)
                dump.summary['liczba_widocznych_api'] = len(visible)
            else:
                raise ValueError('Limit stron; odczyt nie jest kompletny. Zawęź konto API, nie usuwaj uprawnień.')
        state['scope_complete'] = not bool(mapping_error)
        dump.summary['liczba_widocznych_api'] = len(visible)
        stage = {'01_api':len(visible), '02_company':0, '03_customer':0, '04_docstatus':0, '05_posting_date':0}
        for record in visible:
            reasons = powody(record, cfg, customers)
            entry = {'invoice_id':record['name'],'customer':record.get('customer'),
                     'company':record.get('company'),'posting_date':record.get('posting_date'),
                     'docstatus':record.get('docstatus'),'status':record.get('status'),
                     'przechodzi':not bool(reasons), 'powody':reasons}
            evaluated.append(entry)
            if record.get('company') == cfg.company:
                stage['02_company'] += 1
                if record.get('customer') in customers:
                    stage['03_customer'] += 1
                    if str(record.get('docstatus')) == '1':
                        stage['04_docstatus'] += 1
                        if not reasons: stage['05_posting_date'] += 1
            if reasons: omitted.append(entry)
            else: selected.append(record)
        dump.save('02_ocena_filtrow.json', evaluated)
        dump.save('02b_liczniki_etapow.json', stage)
        dump.save('03_faktury_po_filtrach.json', selected)
        dump.save('06_pominiete_lub_bledy.json', omitted)
        dump.summary['etapy_filtrowania'] = stage
        dump.summary['powody_odrzucenia'] = dict(Counter(reason for e in evaluated for reason in e['powody']))
        dump.summary['liczba_po_filtrach'] = len(selected)
        tasks, tasks_error = None, None
        if use_tasks and selected:
            try:
                tasks = importlib.import_module('zadania')
                dump.context['zadania_zaladowane_z'] = str(getattr(tasks, '__file__', ''))
                dump.save('00_kontekst.json', dump.context)
            except Exception as exc:
                tasks_error = f'Nie można wczytać zadania.py: {type(exc).__name__}: {exc}'
                dump.summary['bledy'].append(tasks_error)
        for record in selected:
            name = record['name']
            try:
                doc = client.pobierz('Sales Invoice', name)
                if doc.get('name') != name:
                    raise ValueError('API zwróciło dokument inny niż żądane name.')
                reasons = powody(doc, cfg, customers)
                if reasons:
                    omitted.append({'invoice_id':name, 'etap':'SZCZEGOLY',
                                    'powody':['ZMIANA_LUB_ROZNICA_LISTA_DOKUMENT']+reasons})
                    raise ValueError('Dane listy i dokumentu nie zgadzają się w zakresie filtrów; powtórz przy stabilnym zbiorze.')
                inputs.append({'invoice_id':name, 'funkcja':'wiersz_faktury_csv', 'argument':copy.deepcopy(doc)})
                dump.save('04_wejscie_zadania.json', inputs)
                state['documents'][name] = copy.deepcopy(doc)
                if not use_tasks:
                    outputs.append({'invoice_id':name,'stan':'NIE_WYWOLANO_BEZ_ZADAN'})
                    continue
                if tasks is None:
                    raise ValueError(tasks_error or 'Nie wczytano zadania.py.')
                original_status = getattr(tasks, 'status_rozliczenia', None)
                calls = []
                def tracked_status(*args, **kwargs):
                    call = {'args':copy.deepcopy(args),'kwargs':copy.deepcopy(kwargs)}
                    calls.append(call)
                    dump.summary['wywolania_status_rozliczenia'] += 1
                    try:
                        result = original_status(*args, **kwargs)
                        call['wynik'] = copy.deepcopy(result)
                        return result
                    except Exception as exc:
                        call['blad'] = f'{type(exc).__name__}: {exc}'
                        raise
                if callable(original_status):
                    tasks.status_rozliczenia = tracked_status
                output = {'invoice_id':name,'funkcja':'wiersz_faktury_csv', 'wywolania_Z3':calls}
                try:
                    dump.summary['wywolania_wiersz_faktury_csv'] += 1
                    argument = copy.deepcopy(doc)
                    row = tasks.wiersz_faktury_csv(argument)
                    output['wynik_surowy'] = copy.deepcopy(row)
                    output['zmieniono_argument'] = argument != doc
                    # Zapisz surowy wynik nawet gdy None, puste dict lub błędne kwoty.
                    dump.save('05_wyjscie_zadania.json', outputs+[output])
                    _check_row(row, name)
                    output['stan'] = 'OK_STRUKTURA'
                    state['rows'].append(copy.deepcopy(row))
                    if argument != doc:
                        dump.summary['uwagi'].append(f'{name}: Z4 zmieniło wejściowy argument; należy unikać mutacji źródła.')
                except Exception as exc:
                    output['stan'] = 'BLAD_ZADANIA'
                    output['blad'] = f'{type(exc).__name__}: {exc}'
                    state['function_errors'].append(name)
                    omitted.append({'invoice_id':name,'etap':'ZADANIA','powody':[output['blad']]})
                    dump.summary['bledy'].append(f'{name}: '+output['blad'])
                finally:
                    if callable(original_status):
                        tasks.status_rozliczenia = original_status
                    outputs.append(output)
                    dump.save('05_wyjscie_zadania.json', outputs)
            except Exception as exc:
                msg = f'{name}: {type(exc).__name__}: {exc}'
                dump.summary['bledy'].append(msg)
                omitted.append({'invoice_id':name,'etap':'ODCZYT_LUB_IMPORT_ZADANIA','powody':[msg]})
                outputs.append({'invoice_id':name,'stan':'BLAD_PRZED_Z4','blad':msg})
                state['function_errors'].append(name)
            finally:
                dump.save('05_wyjscie_zadania.json', outputs)
                dump.save('06_pominiete_lub_bledy.json', omitted)
        dump.summary['liczba_wierszy_poprawnych_strukturalnie'] = len(state['rows'])
        if not visible:
            dump.summary['uwagi'].append('API zwróciło pustą listę: porównaj konto tokenu, witrynę BASE_URL i uprawnienia z przeglądarką.')
        elif not selected:
            dump.summary['uwagi'].append('Wszystkie faktury odpadły PRZED zadania.py. Sprawdź 02_ocena_filtrow.json.')
        if not selected:
            dump.summary['stan'] = 'BRAK_FAKTUR_PO_FILTRACH'
        elif not use_tasks:
            dump.summary['stan'] = 'TYLKO_DANE_BEZ_ZADAN'
        else:
            dump.summary['stan'] = 'ODCZYT_I_STRUKTURA_OK'
        if dump.summary['bledy']:
            dump.summary['stan'] = 'BLAD'
    except Exception as exc:
        dump.summary['stan'] = 'BLAD_ODCZYTU'
        dump.summary['bledy'].append(f'{type(exc).__name__}: {exc}')
    finally:
        dump.finish()
        print('Diagnostyka faktur:', dump.folder)
        print('Widoczne API:',dump.summary['liczba_widocznych_api'], '| po filtrach:',dump.summary['liczba_po_filtrach'],
              '| wywołania Z4:',dump.summary['wywolania_wiersz_faktury_csv'], '| wiersze:',len(state['rows']))
        if dump.summary.get('etapy_filtrowania'): print('Kolejne etapy:', dump.summary['etapy_filtrowania'])
        if dump.summary.get('powody_odrzucenia'): print('Powody odrzucenia:', dump.summary['powody_odrzucenia'])
        for msg in dump.summary['uwagi']+dump.summary['bledy']:
            print(_clean(msg, cfg))
    return state


def main(argv=None):
    import argparse
    from konfiguracja import wczytaj_konfiguracje
    from erpnext_client import ERPNextClient
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bez-zadan',action='store_true',help='Zapisz API/filtry/dokumenty, nie importuj ani nie wywołuj zadania.py.')
    args = parser.parse_args(argv)
    cfg = None
    try:
        cfg = wczytaj_konfiguracje()
        client = ERPNextClient(cfg)
        user = client.sprawdz_polaczenie()
        print('Konto API:',user,'| firma:',cfg.company,'| EXPORT_FROM_DATE:',cfg.export_from_date)
        result = zbierz(client, cfg, ROOT/'wyniki', use_tasks=not args.bez_zadan, user=user)
        summary = result['dump'].summary
        return 1 if summary['bledy'] else (2 if not summary['liczba_po_filtrach'] else 0)
    except Exception as exc:
        print('BŁĄD:',_clean(str(exc),cfg) if cfg else str(exc))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
