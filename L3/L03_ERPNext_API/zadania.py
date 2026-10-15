from __future__ import annotations
from datetime import date
from decimal import Decimal, InvalidOperation

DOZWOLONE_TYPY_KLIENTA = {'Company','Individual','Partnership'}


def waliduj_klienta(wiersz: dict[str, str]) -> list[str]:
    """ZADANIE 1. Zwróć listę powodów odrzucenia rekordu klienta.

    Sprawdź co najmniej: external_customer_id, customer_name, customer_type,
    address_line1, city i country. customer_type musi należeć do
    DOZWOLONE_TYPY_KLIENTA.
    """
    bledy: list[str] = []
    # TODO: uzupełnij ciało funkcji. Nie zmieniaj sygnatury.
    return bledy


def waliduj_zamowienie(pozycje: list[dict[str, str]]) -> list[str]:
    """ZADANIE 2. Sprawdź nagłówek i wszystkie pozycje jednego zamówienia.

    Wymagania: co najmniej jedna pozycja; wspólny external_order_id,
    customer_external_id, transaction_date i delivery_date; data dostawy nie
    może być wcześniejsza od daty zamówienia; item_code, item_name i uom nie mogą być
    puste; qty i rate muszą być dodatnimi liczbami.
    """
    bledy: list[str] = []
    # TODO: uzupełnij ciało funkcji. Możesz użyć date.fromisoformat i Decimal.
    return bledy


def status_rozliczenia(grand_total: Decimal, outstanding_amount: Decimal) -> str:
    """ZADANIE 3. Zwróć: OPLACONA, CZESCIOWO OPLACONA albo NIEOPLACONA."""
    # TODO: uzupełnij ciało funkcji.
    raise NotImplementedError('Uzupełnij status_rozliczenia')


def wiersz_faktury_csv(dokument: dict) -> dict[str, str]:
    """ZADANIE 4. Zbuduj jeden wiersz lokalnego pliku wynikowego faktury.

    Pole sales_orders ma zawierać unikalne identyfikatory Sales Order znalezione
    w elementach dokumentu faktury, rozdzielone przecinkiem.
    """
    grand_total = Decimal(str(dokument.get('grand_total', 0)))
    outstanding = Decimal(str(dokument.get('outstanding_amount', 0)))
    # TODO: uzupełnij wartości w gotowej strukturze.
    return {
        'invoice_id': '',
        'customer': '',
        'posting_date': '',
        'currency': '',
        'grand_total': '',
        'outstanding_amount': '',
        'payment_status': status_rozliczenia(grand_total, outstanding),
        'sales_orders': '',
        'erpnext_status': '',
        'docstatus': '',
        'pdf_file': '',
    }
