"""Gotowe procedury: odczyt CSV/JSON, walidacja i łączenie danych.
Python 3.10+. Biblioteka standardowa; bez instalacji pakietów.
Kwoty to grosze (int). Dane i reguły są wyłącznie dydaktyczne.
"""
from __future__ import annotations
import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from collections import Counter

BAZA = Path(__file__).resolve().parent
STATUSY = {"nowe", "w_realizacji", "zrealizowane", "anulowane"}

@dataclass(frozen=True)
class Zamowienie:
    id: str
    klient_id: str
    segment: str
    klient_vip: bool
    blokada_klienta: bool
    produkt_id: str
    ilosc: int
    wartosc_gr: int
    wplacono_gr: int
    status: str
    termin: date
    dni_po_terminie: int
    dostepne_szt: int
    brakuje_szt: int

@dataclass
class Firma:
    zamowienia: list[Zamowienie]
    odrzucone: list[dict]
    magazyn: dict
    metadane: dict
    liczba_wejsc: int


def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _indeks(rows, name):
    keys = [x["id"] for x in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Powtórzony identyfikator: " + name)
    return {x["id"]: x for x in rows}


def wczytaj_firme(katalog=None):
    folder = Path(katalog) if katalog is not None else BAZA / "dane"
    meta = _json(folder / "METADANE.json")
    dzien = date.fromisoformat(meta["dzien_oceny"])
    klienci = _indeks(_json(folder / "klienci.json"), "klienci")
    magazyn = _indeks(_json(folder / "magazyn.json"), "magazyn")
    for c in klienci.values():
        if type(c["vip"]) is not bool or type(c["blokada"]) is not bool:
            raise ValueError("Pola vip i blokada muszą być logiczne w JSON")
    for p in magazyn.values():
        if any(type(p[k]) is not int or p[k] < 0 for k in ("stan_szt", "rezerwacje_szt")):
            raise ValueError("Niepoprawne dane magazynu")
        if p["rezerwacje_szt"] > p["stan_szt"]:
            raise ValueError("Rezerwacje przekraczają stan")
    rows = _csv(folder / "zamowienia.csv")
    seen = Counter(r["id"] for r in rows)
    wplaty = _csv(folder / "wplaty.csv")
    _indeks(wplaty, "wpłaty")
    kwoty = Counter()
    for w in wplaty:
        if w["zamowienie_id"] not in seen:
            raise ValueError("Wpłata do nieznanego zamówienia")
        n = int(w["kwota_gr"])
        if n <= 0:
            raise ValueError("Wpłata musi być dodatnia")
        kwoty[w["zamowienie_id"]] += n
    dobre, bledne = [], []
    for line, r in enumerate(rows, 2):
        errors = []
        if not r["id"] or seen[r["id"]] > 1: errors.append("brak lub duplikat ID")
        if r["klient_id"] not in klienci: errors.append("nieznany klient")
        if r["produkt_id"] not in magazyn: errors.append("nieznany produkt")
        if r["status"] not in STATUSY: errors.append("nieznany status")
        try:
            qty, cena = int(r["ilosc"]), int(r["cena_gr"])
            if qty <= 0 or cena <= 0: raise ValueError()
        except ValueError:
            errors.append("ilość lub cena nie jest dodatnią liczbą całkowitą")
            qty, cena = 0, 0
        try: termin = date.fromisoformat(r["termin"])
        except ValueError:
            errors.append("błędna data")
            termin = dzien
        if qty and cena and kwoty[r["id"]] > qty*cena:
            errors.append("wpłata przekracza wartość")
        if errors:
            bledne.append({"linia":line,"id":r["id"],"przyczyny":errors})
            continue
        c, p = klienci[r["klient_id"]], magazyn[r["produkt_id"]]
        wolne = p["stan_szt"] - p["rezerwacje_szt"]
        dobre.append(Zamowienie(r["id"],r["klient_id"],c["segment"],c["vip"],c["blokada"],
            r["produkt_id"],qty,qty*cena,kwoty[r["id"]],r["status"],termin,
            max((dzien-termin).days,0),wolne,max(qty-wolne,0)))
    return Firma(dobre,bledne,magazyn,meta,len(rows))


def pozostalo_do_zaplaty(z):
    """Gotowa procedura: kwota brakująca do pełnej wpłaty, w groszach."""
    return max(z.wartosc_gr-z.wplacono_gr,0)


def pokaz_zamowienie(firma, identyfikator):
    """Odczyt jednej karty; nie zmienia źródeł."""
    for z in firma.zamowienia:
        if z.id == identyfikator: return z
    raise ValueError("Brak poprawnego zamówienia o ID " + identyfikator)


def podsumowanie_zrodla(firma):
    return {"wejscie":firma.liczba_wejsc,"poprawne":len(firma.zamowienia),
            "kwarantanna":len(firma.odrzucone),
            "statusy":dict(Counter(z.status for z in firma.zamowienia)),
            "wartosc_wszystkich_gr":sum(z.wartosc_gr for z in firma.zamowienia),
            "wplaty_gr":sum(z.wplacono_gr for z in firma.zamowienia)}
