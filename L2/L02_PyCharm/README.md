# L02 — moduły systemu i proste reguły biznesowe
**dr inż. Bartłomiej Klin · semestr zimowy 2026/2027 · 3 × 45 minut**

Otrzymujesz działający program. Odczyt CSV/JSON, walidacja, łączenie danych, obliczanie brakującej kwoty, wykres i raport są gotowe. **Twoim jedynym obowiązkowym plikiem do edycji jest `reguly.py`**. Uzupełniasz cztery krótkie funkcje na podstawie zasad firmy DEMO.

## Start w PyCharm
1. Rozpakuj cały folder. W PyCharm użyj **Open** i wskaż **L02_PyCharm**.
2. Wybierz dostępny interpreter **Python 3.10 lub nowszy**. Nie kopiuj cudzego `.venv` ani `.idea`. Pakiety pip nie są potrzebne.
3. Uruchom prawym przyciskiem plik **00_start.py → Run**. Oczekiwane: 15 rekordów wejściowych, 12 poprawnych, 3 w kwarantannie. Kwoty i statusy objaśnia karta zadań.
4. Uruchom **uruchom.py** i otwórz `wyniki/raport.html` w przeglądarce. Na początku **NIEUZUPEŁNIONA / BRAK_WYNIKU** jest prawidłowym komunikatem — funkcje trzeba dopiero uzupełnić.
5. Otwórz **KARTA_ZADAN.md**, potem **reguly.py**. Po każdym zadaniu uruchom program ponownie i odśwież HTML.
6. Sprawdź rozwiązanie: prawy przycisk na **testy_regul.py → Run**. Przed uzupełnieniem funkcji testy celowo nie przechodzą.

Alternatywnie w terminalu w katalogu projektu:
```powershell
py -3 00_start.py
py -3 uruchom.py
py -3 -m unittest testy_regul -v
```
Na systemie bez launchera `py` użyj polecenia odpowiadającego wybranemu interpreterowi, np. `python`.

## Gdzie zaglądać?
- **KARTA_ZADAN.md** — zadania, kontrakt, kolejność decyzji.
- **POMOC.md** — krótkie gotowe wzorce warunków; nie musisz pisać pętli ani parsera.
- **KARTA_PRACY.md** — miejsce na wyniki i uzasadnienie; wypełnij i oddaj.
- **biblioteka.py, analiza.py, raport.py** — gotowe części. Nie trzeba ich przepisywać.
- **dane/** — syntetyczne źródła, których nie zmieniamy podczas podstawowych zadań.

## Zakres modelu
Jedna pozycja produktowa na zamówienie; kwoty w **groszach**, bez podatków i księgowania. Ocena na **09.10.2026**. Źródła udają eksporty ze sprzedaży, CRM, magazynu i rozliczeń, ale **nie są czterema działającymi systemami produkcyjnymi**.

`GOTOWE` oznacza kwalifikację pojedynczego zamówienia na niezmiennym stanie zapasu. Nie oznacza rezerwacji, wysyłki ani możliwości obsługi wszystkich zamówień jednocześnie. Osobne gotowe rozszerzenie pokazuje przydział na kopii stanu.

## Oddanie
Oddaj `reguly.py`, `wyniki/raport.json`, `wyniki/raport.html`, wypełnioną `KARTA_PRACY.md` oraz zapis wyniku testów. Nie oddawaj `.venv`, `.idea` i `__pycache__`. Termin i kanał określa prowadzący. Nieukończone zadania oznacz jawnie.

Wykorzystane podpowiedzi wpisz w kartę pracy. Każdy student powinien umieć samodzielnie objaśnić jeden warunek i jeden wynik. Nie ustanawiamy tu nowych procentowych progów oceniania.

Dokumentacja środowiska: https://www.jetbrains.com/help/pycharm/creating-and-running-your-first-python-project.html
