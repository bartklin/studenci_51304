"""GOTOWA LOGIKA URUCHOMIENIA. Edytujesz wyłącznie reguly.py."""
import sys
import reguly
from biblioteka import wczytaj_firme
from analiza import analizuj_zamowienia
from raport import zapisz_raport

if __name__ == "__main__":
    try:
        firma = wczytaj_firme()
        wynik = analizuj_zamowienia(firma, reguly)
        plik = zapisz_raport(wynik)
        print("Raport zapisano:", plik)
        print("Otwórz raport.html w przeglądarce. Odśwież po kolejnym uruchomieniu.")
        print("Status:", "REGUŁY WYKONANE — SPRAWDŹ TESTY" if wynik["kompletne"] else "NIEKOMPLETNE")
    except (OSError, ValueError, KeyError) as blad:
        print("Błąd danych lub pliku:", blad)
        sys.exit(1)
