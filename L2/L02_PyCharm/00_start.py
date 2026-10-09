"""Test środowiska; nie wymaga napisania reguł."""
import sys
from biblioteka import wczytaj_firme, podsumowanie_zrodla, pokaz_zamowienie
if __name__ == "__main__":
    print("Python:", sys.version.split()[0])
    firma=wczytaj_firme()
    print("Podsumowanie wejścia:", podsumowanie_zrodla(firma))
    print("Karta Z001:", pokaz_zamowienie(firma,"Z001"))
    print("Odczyt działa. Edytuj reguly.py, a wynik oglądaj po uruchomieniu uruchom.py.")
