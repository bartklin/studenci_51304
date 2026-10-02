"""Kontrola stanowiska — nie oblicza odpowiedzi do zadań."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from pomoc import wczytaj_wiersze


def main() -> int:
    if sys.version_info < (3, 10):
        print("Potrzebny Python 3.10 lub nowszy. Zgłoś problem prowadzącemu.")
        return 1
    katalog = Path(__file__).resolve().parent  # Tutaj ustaw punkt przerwania.
    print("Python:", sys.version.split()[0])
    print("Interpreter:", sys.executable)
    print("Projekt:", katalog)
    try:
        for plik in ("zamowienia.csv", "zamowienia_bledy.csv"):
            wczytaj_wiersze(katalog / "dane" / plik)
            print("Plik i kolumny OK:", plik)
        with (katalog / "dane/klienci.json").open(encoding="utf-8") as f:
            klienci = json.load(f)
        if not isinstance(klienci, list) or not all(
            isinstance(k, dict) and {"klient_id", "nazwa", "segment"} <= k.keys()
            for k in klienci
        ):
            raise ValueError("Niepoprawna struktura klientów")
        print("Struktura JSON OK")
        print("Środowisko gotowe. To kontrola plików, nie zaliczenie diagnozy.")
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"Problem: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
