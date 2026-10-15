# L03 — ERPNext REST API: klienci, zamówienia i lokalny eksport faktur

**Prowadzący:** dr inż. Bartłomiej Klin  
**Semestr:** zimowy 2026/2027

Projekt jest przygotowany dla osób o podstawowej znajomości Pythona. Studenci uzupełniają tylko cztery funkcje w `zadania.py`. Obsługa HTTP, autoryzacji, CSV/JSON, importu i zapisu plików jest gotowa.

## Założenia środowiska
- Python 3.10+; bez pakietów `pip`.
- Dostęp do przygotowanej instancji ERPNext/Frappe.
- Użytkownik API z uprawnieniami do Customer, Address, Sales Order oraz odczytu i wydruku Sales Invoice.
- Firma, waluta, cennik, grupa klientów, terytorium i pozycje usługowe muszą istnieć.
- Dane są syntetyczne i szkoleniowe.

## Start
1. Rozpakuj cały folder.
2. Otwórz go jako projekt w PyCharm.
3. W ERPNext otwórz rekord własnego użytkownika, w sekcji **API Access** wygeneruj API Key i API Secret. Sekret jest pokazywany jednorazowo.
4. Skopiuj `erpnext.env.example` do `erpnext.env`, wpisz adres i klucze oraz ustaw `LAB_PREFIX` na unikalny kod zespołu, np. `A1`.
5. Uzupełnij ciała funkcji w `zadania.py`.
6. Użyj gotowych plików `.cmd` albo poleceń z `KARTA_ZADAN.md`.

## Ważne
API Secret jest jednorazowo pokazywany podczas generowania kluczy. Przechowuj go wyłącznie w `erpnext.env`. Nie kopiuj sekretu do raportu, kodu, zrzutów ekranu ani systemu kontroli wersji.

## Pola wejściowe
Szczegółowe rozróżnienie pól wymaganych przez DocType ERPNext i pól wymaganych przez to ćwiczenie znajduje się w `POLA_ERPNext.md`.

## Wspólna instancja
Jeżeli kilka zespołów korzysta z jednej witryny ERPNext, każdy zespół ustawia inne `LAB_PREFIX`. Prefiks jest dodawany do nazwy Customer i numeru PO, dzięki czemu rekordy zespołów nie kolidują. Przy osobnej witrynie dla zespołu pole może pozostać puste.
