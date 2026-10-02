"""Gotowe funkcje techniczne. Bez instalowania pakietów zewnętrznych."""
from __future__ import annotations
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

STATUSY = {"nowe", "w_realizacji", "zrealizowane", "anulowane"}
POLA = ["zamowienie_id", "klient_id", "status", "kwota_pln"]


def na_kwote(tekst: str) -> Decimal:
    """Kwota zamówienia: skończona, dodatnia, maksymalnie 2 miejsca po przecinku.
    To kontrakt tych danych, nie reguła wszystkich dokumentów finansowych.
    Błąd nie staje się zerem. Przykład: na_kwote("12.50").
    """
    try:
        wartosc = Decimal(str(tekst).strip())
        if not wartosc.is_finite() or wartosc <= 0:
            raise ValueError("Kwota musi być skończona i dodatnia")
        wynik = wartosc.quantize(Decimal("0.01"))
        if wynik != wartosc:
            raise ValueError("Kwota ma więcej niż dwa miejsca po przecinku")
        return wynik
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Niepoprawny zapis kwoty: {tekst!r}") from exc


def wczytaj_wiersze(sciezka: Path) -> list[dict[str, str]]:
    """Gotowy odczyt niezależnego pliku walidacji; w Z1 odczyt napisz sam."""
    with sciezka.open(encoding="utf-8-sig", newline="") as f:
        czytnik = csv.DictReader(f, delimiter=";")
        if czytnik.fieldnames != POLA:
            raise ValueError(f"Niepoprawne kolumny: {czytnik.fieldnames!r}")
        return list(czytnik)


def zapisz_json(sciezka: Path, dane: Any) -> None:
    """Decimal zapisujemy jako tekst dziesiętny; nie przez float."""
    def konwersja(obj: Any) -> str:
        if isinstance(obj, Decimal):
            return format(obj, ".2f")
        raise TypeError(f"Nieobsługiwany typ wyniku: {type(obj).__name__}")
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    sciezka.write_text(json.dumps(dane, ensure_ascii=False, indent=2,
                                 default=konwersja) + "\n", encoding="utf-8")
