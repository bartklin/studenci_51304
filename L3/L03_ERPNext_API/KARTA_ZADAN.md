# L03 — ERPNext przez REST API

## Cel
1. Skonfigurować dostęp programu do własnego użytkownika ERPNext.
2. Zaimportować klientów i robocze Sales Order z przygotowanych CSV.
3. W ERPNext zatwierdzić wybrane zamówienie, utworzyć z niego Sales Invoice i zatwierdzić fakturę.
4. Pobrać lokalnie dane faktur do JSON, PDF i zbiorczego `wyniki/faktury.csv`.
5. Sporządzić raport DOCX.

## Student edytuje wyłącznie
`zadania.py` — cztery ciała funkcji. Nie zmieniaj klienta HTTP ani procedur importu.

## Gotowe polecenia
```powershell
copy erpnext.env.example erpnext.env
notepad erpnext.env
# Ustaw unikalny LAB_PREFIX, np. A1
py -3 -m unittest discover -s testy -v
py -3 uruchom.py sprawdz
py -3 uruchom.py import-klientow
py -3 uruchom.py import-zamowien
# następnie czynności w interfejsie ERPNext
py -3 uruchom.py eksport-faktur
```

## Czynności w ERPNext
1. Otwórz zaimportowany Sales Order i sprawdź klienta, daty i pozycje.
2. Zapisz identyfikator dokumentu i użyj **Submit**.
3. Użyj **Create → Sales Invoice** (nazwy przycisków mogą zależeć od wersji i języka).
4. Sprawdź kody i nazwy pozycji, ilości, stawki, sumę oraz powiązanie z Sales Order.
5. Zapisz i zatwierdź Sales Invoice.
6. Opcjonalnie zarejestruj częściową płatność, jeżeli prowadzący przygotował konta księgowe.
7. Uruchom lokalny eksport i sprawdź `wyniki/faktury.csv` oraz katalogi PDF/JSON.

## Oddanie
- wypełniony `Sprawozdanie_L03_ERPNext_API.docx`,
- `wyniki/faktury.csv`,
- `zadania.py`,
- opcjonalnie jeden pobrany PDF faktury.

Nie oddawaj: `erpnext.env`, haseł, API Secret, katalogu `.idea` ani `.venv`.
