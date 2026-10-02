# L01 — praca z danymi w PyCharm
**Prowadzący: dr inż. Bartłomiej Klin · semestr zimowy 2026/2027**

## Cel i organizacja
Pierwszy blok: 3 × 45 min. Pierwsze 90 minut: organizacja, zasady i przygotowanie stanowiska. Ostatnie 45 minut: indywidualna diagnoza pracy z danymi systemu sprzedaży. Diagnoza nie jest nowym egzaminem wstępnym ani automatyczną oceną zaliczeniową. Zapisz także częściowe rozwiązanie.

Potrzebne: PyCharm i lokalny Python 3.10 lub nowszy. **Bez pip, pandas, internetu, serwera i konta AI.** Instalacja interpretera oraz IDE powinna być przygotowana przed zajęciami. Pracuj tylko na syntetycznych plikach z tej paczki.

## Start na Windows
1. Rozpakuj cały folder; nie uruchamiaj pliku z wnętrza ZIP.
2. W PyCharm wybierz **Open** i folder **L01_PyCharm**.
3. Sprawdź interpreter: Settings → Python → Interpreter (w starszym interfejsie: Project → Python Interpreter). Wskaż dostępny interpreter pracowni. Nie pobieraj pakietów i nie kopiuj cudzych .venv/.idea.
4. Prawym przyciskiem na **00_start.py → Run**. Błąd techniczny zgłoś prowadzącemu.
5. Pokaz organizacyjny: punkt przerwania na linii `katalog = ...`, polecenie Debug, podgląd ścieżki, pojedynczy krok. Zakończ Debug.
6. Otwórz **zadania.py**. Pierwsze uruchomienie wypisze TODO. To brak implementacji, nie zaliczenie.

Alternatywny start w terminalu (gdy problem dotyczy tylko IDE):
```powershell
py -3 00_start.py
py -3 zadania.py
```
To awaryjny sposób uruchomienia tego samego zadania, nie wykonany test interfejsu PyCharm.

## Dane i kontrakt
`dane/zamowienia.csv`: separator `;`, kodowanie `utf-8-sig`, jeden rekord = całe zamówienie.
`dane/klienci.json`: UTF-8, lista obiektów z polami `klient_id`, `nazwa`, `segment`.
`dane/zamowienia_bledy.csv`: oddzielny test jakości, NIE do sumowania sprzedaży.

Statusy: `nowe`, `w_realizacji`, `zrealizowane`, `anulowane`. Nieanulowane: `status != "anulowane"`. Otwarte: `nowe` lub `w_realizacji`. Kwoty w PLN, dodatnie, skończone, maksymalnie dwa miejsca po przecinku. Zapis z kropką. Gotowa funkcja `na_kwote()` zwraca Decimal lub zgłasza ValueError. Reguły te opisują nasz przykład, a nie każdy system finansowy. Data odniesienia: 15.09.2026, identyfikator: L01_START_8.

## Cztery zadania — 45 minut łącznie
Przed kodowaniem: 5 minut na omówienie celu i schematu. **Z1: 8 min; Z2: 10 min; Z3: 10 min; Z4: 7 min; wniosek i zapis: 5 min.**

### Z1. Odczyt CSV i JSON
Uzupełnij `wczytaj_dane(katalog)`. Zwróć dwie listy. Użyj `csv.DictReader` ze średnikiem i `json.load`. Sprawdź nazwy pól. Nie wpisuj danych ręcznie do kodu.

### Z2. Filtr i wartości
Uzupełnij `podsumuj(zamowienia)`. Wyznacz liczby wszystkich i nieanulowanych zamówień, obie sumy oraz ID odrzuconych. Klucze wyniku są podane w docstringu. Używaj gotowej `na_kwote`, a sumę inicjalizuj `Decimal("0.00")`. Wyjaśnij różnicę obu wartości.

### Z3. Segment klienta z drugiego źródła
Uzupełnij `wedlug_segmentu(zamowienia, klienci)`. Zbuduj słownik klient_id → segment. Dla nieanulowanych zamówień zsumuj kwoty według segmentu. Sprawdź zgodność sumy segmentów z Z2. Nie łącz po nazwie firmy.

### Z4. Jakość oddzielnego CSV
Uzupełnij `sprawdz_jakosc(wiersze)`. Wykryj wadliwe kwoty oraz nieznane statusy. Dla wadliwego rekordu zwróć linię pliku, ID i listę przyczyn. Nagłówek to linia 1. Nie poprawiaj źródła i nie zastępuj błędu zerem. `anulowane` jest dozwolonym statusem.

### Zapis i interpretacja
Uruchom `zadania.py`. Program zapisuje `wyniki/wynik.json`, również gdy część zadań pozostała niewykonana. **Etykieta „wykonano” oznacza wyłącznie wykonanie funkcji; poprawność trzeba sprawdzić.** Uzupełnij `samoocena.md`: opis systemu, wniosek, ograniczenie, sposób kontroli i wykorzystane podpowiedzi.

## Małe testy oraz rozszerzenia
`testy_przykladowe.py` zawiera dwa niezależne przykłady z X1/X2, nie pełny klucz do L01_START_8. Przed implementacją ERROR jest oczekiwany. Po Z2/Z3 uruchom plik lub `py -3 -m unittest testy_przykladowe -v`.

Po podstawach: zlicz statusy; rozróżnij źle sformatowaną kwotę od nieznanego klienta; wykryj powtórzenie ID w pliku jakości. Dodatkowe kontrole jawnie oznacz jako rozszerzone. Nie oceniaj ich na podstawie klucza minimum.

## Oddanie
Oddaj `zadania.py`, `wyniki/` i `samoocena.md`. Bez .venv, .idea, haseł i cudzych plików. Kanał i termin określi prowadzący. W czasie diagnozy nie korzystaj z generowania rozwiązań przez AI. Podpowiedzi i dokumentacja są dozwolone po oznaczeniu ich użycia.

## Źródła techniczne
JetBrains, PyCharm Help: https://www.jetbrains.com/help/pycharm/creating-and-running-your-first-python-project.html
Python Software Foundation: https://docs.python.org/3/library/csv.html ; https://docs.python.org/3/library/json.html ; https://docs.python.org/3/library/decimal.html ; https://docs.python.org/3/library/pathlib.html
Zadania i dane: autorski przykład dydaktyczny; nie są definicją naukową systemu ERP.
