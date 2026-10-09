# Pomoc — składasz warunki, nie budujesz całego programu
Poniższe fragmenty to wzorce. Miejsca opisane słownie trzeba zastąpić konkretnymi polami. W pliku `reguly.py` usuń `return None` dopiero wtedy, gdy wpiszesz swój warunek.

## 1. Równość i wybór z dwóch możliwości
```python
# przykład niezależny od zamówień
kolor = "niebieski"
czy_dozwolony = kolor in ("niebieski", "zielony")
```
W zadaniu zamiast `kolor` czytasz `z.status`, a zamiast kolorów stosujesz stany wymienione w karcie. Cudzysłowy są potrzebne przy tekstach; nie są potrzebne przy True i False.

## 2. Dwa warunki naraz
```python
# oba warunki muszą być prawdziwe
moze_wejsc = ma_bilet and bramka_otwarta
```
W Z2 pierwszy warunek daje `czy_otwarte(z)`, drugi sprawdza `z.dni_po_terminie > 0`.

## 3. Zaprzeczenie i wcześniejszy wynik
```python
def przyklad(osoba):
    if not osoba.aktywna:
        return "NIEAKTYWNA"
    if osoba.ma_rezerwacje:
        return "Z_REZERWACJA"
    return "BEZ_REZERWACJI"
```
Po wykonaniu `return` funkcja się kończy. Kolejne warunki nie są sprawdzane. Wcięcia to cztery spacje. Nie wpisuj wszystkiego w jednej linii.

## 4. Użycie gotowej procedury
```python
# ten fragment wolno użyć bez przepisywania obliczeń
if pozostalo_do_zaplaty(z) > 0:
    return "UZUPELNIJ_PLATNOSC"
```
Wstaw go we właściwym miejscu funkcji `decyzja`. Przed nim muszą znaleźć się wcześniejsze zasady z tabeli. Import jest już na górze pliku.

## 5. Szkielet Z4 — przeczytaj, potem uzupełnij reguly.py
1. Jeśli anulowane — zwróć POMIN_ANULOWANE.
2. Jeśli zrealizowane — zwróć ZAKONCZONE.
3. Jeśli blokada klienta — zwróć WERYFIKACJA.
4. Użyj powyższego fragmentu z `pozostalo_do_zaplaty`.
5. Jeśli brakuje sztuk — zwróć UZUPELNIJ_MAGAZYN.
6. Na końcu zwróć GOTOWE.

Nie potrzebujesz `for`, `while`, `csv`, `json`, tworzenia słowników, klas ani funkcji drukującej wykres.

## 6. Typowe komunikaty
| Komunikat | Co sprawdzić |
|---|---|
| NIEUZUPEŁNIONA | W funkcji pozostało None |
| wynik spoza dozwolonego zbioru | Literówka w tekście wyniku lub zwrócono inny typ |
| wymagane True albo False | Cudzysłowy przy wartości logicznej albo zwrócono liczbę zamiast bool |
| NameError | Nazwa pola/funkcji, brak `z.` lub literówka |
| IndentationError | Wcięcia; nie mieszaj tabulatorów i spacji |
| Raport się nie zmienił | Zapisz plik, ponownie uruchom Python, odśwież stronę |

Status „kompletne” sprawdza tylko wykonanie czterech funkcji i typy wyników. Poprawność znaczenia sprawdzasz tabelą, przykładami i testami.
