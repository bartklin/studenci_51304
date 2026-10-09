"""EDYTUJ TYLKO TEN PLIK. None znaczy: reguła jeszcze nieuzupełniona.
Nie zmieniaj nazw funkcji. Pola rekordu i dozwolone wyniki opisuje KARTA_ZADAN.md.
"""
from biblioteka import pozostalo_do_zaplaty


def czy_otwarte(z):
    # Z1: status nowe lub w_realizacji. Zwróć True albo False.
    return None


def czy_opoznione(z):
    # Z2: otwarte i dni_po_terminie > 0. Sam dzień terminu NIE jest opóźnieniem.
    return None


def priorytet(z):
    # Z3: nieopóźnione -> STANDARD; opóźnione VIP -> PILNE;
    # pozostałe opóźnione -> WYSOKI. Skorzystaj z czy_opoznione(z).
    return None


def decyzja(z):
    # Z4: zastosuj w kolejności zasady z tabeli decyzyjnej.
    # POMIN_ANULOWANE / ZAKONCZONE / WERYFIKACJA / UZUPELNIJ_PLATNOSC /
    # UZUPELNIJ_MAGAZYN / GOTOWE. To kwalifikacja, a nie wykonanie wysyłki.
    return None
