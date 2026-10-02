"""L01 — zadania diagnostyczne w PyCharm.
Prowadzący: dr inż. Bartłomiej Klin. Semestr zimowy 2026/2027.
Uzupełnij cztery funkcje. TODO jest niewykonanym zadaniem, nie wynikiem.
Najpierw przeczytaj README.md. Nie zmieniaj danych źródłowych.
"""
from __future__ import annotations
import csv
import json
from decimal import Decimal
from pathlib import Path
from pomoc import STATUSY, na_kwote, wczytaj_wiersze, zapisz_json

ROOT = Path(__file__).resolve().parent


def wczytaj_dane(katalog: Path) -> tuple[list[dict], list[dict]]:
    """Z1 (8 min). Odczytaj zamowienia.csv i klienci.json z katalogu dane.
    Użyj csv.DictReader(..., delimiter=";") i json.load(...).
    CSV: encoding="utf-8-sig", newline="". JSON: encoding="utf-8".
    Zwróć (zamowienia, klienci), czyli dwie listy.
    Podpowiedź składni: with sciezka.open(...) as f: ...
    """
    # TODO Z1 — odczyt plików, nie ręczne wklejenie rekordów.
    raise NotImplementedError("Z1 — wczytaj_dane")


def podsumuj(zamowienia: list[dict]) -> dict:
    """Z2 (10 min). Filtr nieanulowanych: status != "anulowane".
    Wynik: słownik z kluczami:
      liczba_wszystkich (int), liczba_nieanulowanych (int),
      suma_wszystkich (Decimal), suma_nieanulowanych (Decimal),
      wykluczone_id (lista identyfikatorów).
    Gotowe: na_kwote(wiersz["kwota_pln"]). Sumowanie od Decimal("0.00").
    """
    # TODO Z2 — kwoty oblicz z danych, nie wpisuj wyniku na sztywno.
    raise NotImplementedError("Z2 — podsumuj")


def wedlug_segmentu(zamowienia: list[dict], klienci: list[dict]) -> dict:
    """Z3 (10 min). Sumy NIEANULOWANYCH zamówień według segmentu.
    Utwórz mapę klient_id -> segment z listy klientów.
    Zwróć {segment: Decimal}. Identyfikatory w podstawowym pliku są poprawne.
    Podpowiedź: wynik.get(segment, Decimal("0.00")) zwraca poprzednią sumę.
    """
    # TODO Z3 — łącz przez klient_id, nie przez podobieństwo nazw.
    raise NotImplementedError("Z3 — wedlug_segmentu")


def sprawdz_jakosc(wiersze: list[dict]) -> list[dict]:
    """Z4 (7 min). Wykryj wadliwą kwotę i nieznany status.
    Kwota: wywołaj na_kwote i przechwyć ValueError. Status: STATUSY.
    Zwróć po jednej pozycji na WADLIWY rekord:
      {"wiersz": numer, "zamowienie_id": identyfikator,
       "przyczyny": lista niepustych opisów problemów}.
    Numer to fizyczna linia CSV: pierwszy rekord = 2 (nagłówek = 1).
    Status anulowane jest dopuszczalny, nie stanowi błędu jakości.
    Rozszerzenie (nieobowiązkowe): klient poza mapą i powtórzony ID.
    """
    # TODO Z4 — nie modyfikuj wierszy i nie zastępuj błędów zerem.
    raise NotImplementedError("Z4 — sprawdz_jakosc")


def main() -> None:
    rezultat: dict = {"zestaw": "L01_START_8", "zadania": {}}
    zamowienia = klienci = None
    try:
        zamowienia, klienci = wczytaj_dane(ROOT / "dane")
        rezultat["zadania"]["Z1"] = {
            "status": "wykonano — wymaga sprawdzenia",
            "liczba_zamowien": len(zamowienia), "liczba_klientow": len(klienci)}
        print("Z1 wykonano. Sprawdź nazwy pól i typy.")
    except NotImplementedError as exc:
        print("TODO:", exc)
        rezultat["zadania"]["Z1"] = {"status": "niewykonane"}
    except (OSError, ValueError, TypeError) as exc:
        print("BŁĄD Z1:", type(exc).__name__, exc)
        rezultat["zadania"]["Z1"] = {"status": "blad", "opis": str(exc)}
    for kod, funkcja in [("Z2", lambda: podsumuj(zamowienia)),
                          ("Z3", lambda: wedlug_segmentu(zamowienia, klienci)),
                          ("Z4", lambda: sprawdz_jakosc(wczytaj_wiersze(
                              ROOT / "dane/zamowienia_bledy.csv")))]:
        if kod in {"Z2", "Z3"} and (zamowienia is None or klienci is None):
            rezultat["zadania"][kod] = {"status": "oczekuje_na_Z1"}
            print(kod, "oczekuje na poprawny odczyt Z1")
            continue
        try:
            wynik = funkcja()
            if wynik is None:
                raise ValueError("Funkcja zwróciła None; uzupełnij return")
            rezultat["zadania"][kod] = {"status": "wykonano — wymaga sprawdzenia",
                                        "wynik": wynik}
            print(kod, "wynik:", wynik)
        except NotImplementedError as exc:
            print("TODO:", exc)
            rezultat["zadania"][kod] = {"status": "niewykonane"}
        except Exception as exc:
            # Cel dydaktyczny: zachowaj część pracy i pokaż, która funkcja nie działa.
            print("BŁĄD", kod, type(exc).__name__, exc)
            rezultat["zadania"][kod] = {"status": "blad", "opis": str(exc)}
    zapisz_json(ROOT / "wyniki/wynik.json", rezultat)
    print("Zapisano wyniki/wynik.json. Wykonanie nie jest dowodem poprawności.")


if __name__ == "__main__":
    main()
