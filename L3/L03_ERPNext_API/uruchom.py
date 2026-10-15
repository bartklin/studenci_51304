from __future__ import annotations
import argparse
import functools
import hashlib
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser=argparse.ArgumentParser(description='L03 — ERPNext REST API, diagnostyka i testy')
    parser.add_argument('polecenie',choices=['sprawdz','testy','kontrola-csv','diagnostyka-faktur',
                                           'import-klientow','import-zamowien','eksport-faktur'])
    parser.add_argument('--debug',action='store_true',help='Eksport: zrzut wszystkich nagłówków widocznych API PRZED filtrami.')
    parser.add_argument('--bez-zadan',action='store_true',help='Diagnostyka faktur: nie importuj/wywołuj zadania.py.')
    args=parser.parse_args(argv)
    if args.bez_zadan and args.polecenie!='diagnostyka-faktur':
        parser.error('--bez-zadan jest tylko dla diagnostyka-faktur; nie omija zadań przy eksporcie.')
    if args.debug and args.polecenie not in {'eksport-faktur','diagnostyka-faktur'}:
        parser.error('--debug jest tylko dla eksportu/diagnostyki faktur.')
    if args.polecenie=='sprawdz':
        return runpy.run_path(str(ROOT/'00_start.py'))['main']([])
    if args.polecenie=='testy':
        from sprawdz_zadania import main as tests
        return tests([])
    if args.polecenie=='kontrola-csv':
        from kontrola_wyniku import main as check
        return check([])
    if args.polecenie=='diagnostyka-faktur':
        from diagnostyka_faktur import main as diagnose
        return diagnose(['--bez-zadan'] if args.bez_zadan else [])
    from sprawdz_zadania import main as tests
    groups={'import-klientow':['Z1'],'import-zamowien':['Z2'],'eksport-faktur':['Z3','Z4']}
    def tests_ok():
        for group in groups[args.polecenie]:
            if tests(['--grupa',group]):
                print('Przerwano operację: popraw zadanie '+group+'. Nie nadpisano zadania.py ani faktury.csv.')
                return False
        return True
    # --debug ma zapisać wejście API nawet jeśli zadania.py ma błąd/składnię/TODO.
    if not args.debug and not tests_ok():
        print('Do diagnostyki bez gotowych zadań: python3 uruchom.py diagnostyka-faktur --bez-zadan')
        return 1
    from konfiguracja import wczytaj_konfiguracje
    from erpnext_client import ERPNextClient
    counts={name:0 for name in ('waliduj_klienta','waliduj_zamowienie','status_rozliczenia','wiersz_faktury_csv')}
    originals={}; tasks=None; prepared=None; cfg=None; code=0
    try:
        cfg=wczytaj_konfiguracje(); client=ERPNextClient(cfg)
        user=client.sprawdz_polaczenie()
        print('ERPNext — użytkownik API:',user)
        print('Firma:',cfg.company,'| EXPORT_FROM_DATE:',cfg.export_from_date)
        if args.debug:
            from diagnostyka_faktur import zbierz
            prepared=zbierz(client,cfg,ROOT/'wyniki',all_visible=True,user=user)
            counts['wiersz_faktury_csv']=prepared['dump'].summary['wywolania_wiersz_faktury_csv']
            counts['status_rozliczenia']=prepared['dump'].summary['wywolania_status_rozliczenia']
            if prepared['dump'].summary['bledy']:
                code=1
                print('Nie zapisano CSV: sprawdź zrzuty i podsumowanie diagnostyki.')
                return code
            if not prepared['dump'].summary['liczba_po_filtrach']:
                code=2
                print('Nie zapisano CSV: wszystkie faktury odpadły przed zadania.py.')
                return code
            if not tests_ok():
                code=1
                prepared['dump'].summary['stan']='TESTY_NIEZALICZONE_CSV_NIEZAPISANY'
                prepared['dump'].finish()
                return code
        import zadania as tasks
        for name in counts:
            func=getattr(tasks,name);originals[name]=func
            def make_wrapper(n,f):
                @functools.wraps(f)
                def wrapped(*a,**kw):
                    counts[n]+=1
                    return f(*a,**kw)
                return wrapped
            setattr(tasks,name,make_wrapper(name,func))
        from procedury import importuj_klientow, importuj_zamowienia, eksportuj_faktury
        if args.polecenie=='import-klientow': result=importuj_klientow(client,cfg)
        elif args.polecenie=='import-zamowien': result=importuj_zamowienia(client,cfg)
        else:
            result=eksportuj_faktury(client,cfg,debug=args.debug,prepared=prepared)
            if not result: code=2
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as exc:
        message=str(exc)
        if cfg:
            for secret in (cfg.api_key,cfg.api_secret):
                if secret: message=message.replace(secret,'[UKRYTO]')
        print('BŁĄD:',message)
        code=1
    finally:
        if tasks:
            for name,func in originals.items(): setattr(tasks,name,func)
        path=ROOT/'zadania.py'
        report={'czas_utc':datetime.now(timezone.utc).isoformat(),'polecenie':args.polecenie,'exit_code':code,
                'zadania_path':str(path), 'zadania_sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                'wywolania':counts,'uwaga':'Lokalne wywołania w operacji, bez testów wstępnych. Licznik nie dowodzi poprawności wyniku ani zatwierdzenia faktury.'}
        output=ROOT/'wyniki';output.mkdir(exist_ok=True)
        (output/f'slad_{args.polecenie}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Wywołania zadania.py w operacji:',counts)
    return code

if __name__=='__main__':raise SystemExit(main())
