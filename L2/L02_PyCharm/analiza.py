"""Silnik analizy — plik gotowy. Błąd reguły nie staje się wynikiem poprawnym."""
from collections import Counter
from biblioteka import pozostalo_do_zaplaty
DECYZJE = {"POMIN_ANULOWANE", "ZAKONCZONE", "WERYFIKACJA", "UZUPELNIJ_PLATNOSC", "UZUPELNIJ_MAGAZYN", "GOTOWE"}
PRIORYTETY = {"STANDARD", "WYSOKI", "PILNE"}


def _ocen(fn, z, allowed, nazwa):
    try:
        value = fn(z)
        if value is None: return None, nazwa + ": NIEUZUPEŁNIONA"
        if allowed == "bool":
            if type(value) is not bool: raise ValueError("wymagane True albo False")
        elif not isinstance(value,str) or value not in allowed:
            raise ValueError("wynik spoza dozwolonego zbioru")
        return value, None
    except Exception as exc:
        return None, nazwa + ": " + type(exc).__name__ + " — " + str(exc)


def analizuj_zamowienia(firma, reguly):
    rows, problemy = [], []
    for z in firma.zamowienia:
        values = {}
        for n, allowed in [("czy_otwarte","bool"),("czy_opoznione","bool"),("priorytet",PRIORYTETY),("decyzja",DECYZJE)]:
            value, error = _ocen(getattr(reguly,n),z,allowed,n)
            values[n] = value
            if error: problemy.append({"id":z.id,"problem":error})
        rows.append(dict(id=z.id,produkt=z.produkt_id,segment=z.segment,status=z.status,
            ilosc=z.ilosc,wartosc_gr=z.wartosc_gr,wplacono_gr=z.wplacono_gr,
            pozostalo_gr=pozostalo_do_zaplaty(z),dostepne_szt=z.dostepne_szt,
            brakuje_szt=z.brakuje_szt,dni_po_terminie=z.dni_po_terminie,vip=z.klient_vip,**values))
    pelne = not problemy
    return {"metadane":firma.metadane,"wiersze":rows,"kwarantanna":firma.odrzucone,
            "problemy_regul":problemy,"kompletne":pelne,
            "uwaga":"Kompletność wykonania NIE jest dowodem poprawności reguł. Sprawdź tabelę decyzyjną i testy.",
            "decyzje":dict(Counter(r["decyzja"] or "BRAK_WYNIKU" for r in rows)),
            "otwarte":sum(r["czy_otwarte"] is True for r in rows),
            "opoznione":sum(r["czy_opoznione"] is True for r in rows)}


def plan_przydzialu(firma, raport):
    """ROZSZERZENIE: nowa kopia wolnego stanu, kolejność rosnąca ID, całe zamówienia.
    Nie zapisuje rezerwacji ani nie wykonuje wysyłki. Nie używać przy niekompletnych regułach.
    """
    if not raport["kompletne"]:
        raise ValueError("Najpierw uzupełnij reguły i sprawdź ich poprawność")
    wolne = {k:v["stan_szt"]-v["rezerwacje_szt"] for k,v in firma.magazyn.items()}
    rows=[]
    for r in sorted(raport["wiersze"],key=lambda r:r["id"]):
        if r["decyzja"] != "GOTOWE": continue
        p=r["produkt"]; ok=wolne[p]>=r["ilosc"]
        if ok: wolne[p]-=r["ilosc"]
        rows.append({"id":r["id"],"wynik":"PRZYDZIELONO" if ok else "BRAK_PO_WCZESNIEJSZYM_PRZYDZIALE"})
    return {"tryb":"Symulacja na kopii; kolejność ID; brak częściowego przydziału","wiersze":rows,"pozostalo":wolne}
