"""Czytelne uruchomienie testów lokalnych. Nie łączy się z ERPNext.
--grupa Z1/Z2/Z3/Z4: tylko wybrane zadanie; bez opcji: wszystkie.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grupa', choices=['Z1','Z2','Z3','Z4'])
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    if args.worker:
        import socket
        import unittest
        from unittest.mock import patch
        def no_network(*a, **kw):
            raise RuntimeError('Test lokalny: zablokowano próbę połączenia sieciowego.')
        with patch.object(socket.socket,'connect',no_network), patch.object(socket.socket,'connect_ex',no_network):
            suite=unittest.TestLoader().discover(str(ROOT/'testy'), pattern='test_zadania_rozszerzone.py')
            def cases(obj):
                for x in obj:
                    if isinstance(x,unittest.TestSuite): yield from cases(x)
                    else: yield x
            selected=[case for case in cases(suite) if not args.grupa or ('.'+args.grupa) in case.id() or isinstance(case, unittest.loader._FailedTest)]
            if not selected:
                print('Nie znaleziono testów. Sprawdź pliki w testy/.')
                return 1
            result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
            return 0 if result.wasSuccessful() else 1
    cmd=[sys.executable,str(Path(__file__)), '--worker']
    if args.grupa: cmd.extend(['--grupa',args.grupa])
    print('Testy kodu zadania.py — OFFLINE, bez tokenu i bez ERPNext.',flush=True)
    try:
        run=subprocess.run(cmd,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=45,env={**os.environ, 'PYTHONUTF8':'1', 'PYTHONIOENCODING':'utf-8'})
        output=run.stdout+run.stderr
        code=run.returncode
    except subprocess.TimeoutExpired:
        output='Przekroczono 45 sekund. Sprawdź pętlę nieskończoną w zadania.py.'
        code=1
    print(output)
    label='OK_TESTY_LOKALNE' if code==0 else 'POPRAW_ZADANIA'
    print(label,'— wynik nie potwierdza dostępu do ERPNext ani oceny końcowej.')
    out=ROOT/'wyniki';out.mkdir(exist_ok=True)
    (out/'testy_zadania.txt').write_text(output+'\n'+label+'\n',encoding='utf-8')
    (out/'testy_zadania.json').write_text(json.dumps({'wynik':label,'grupa':args.grupa or 'WSZYSTKIE',
        'czas_utc':datetime.now(timezone.utc).isoformat(),'zadania_sha256':hashlib.sha256((ROOT/'zadania.py').read_bytes()).hexdigest() if (ROOT/'zadania.py').is_file() else None,
        'offline':True,'exit_code':code},ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if code==0 else 1

if __name__=='__main__':raise SystemExit(main())
