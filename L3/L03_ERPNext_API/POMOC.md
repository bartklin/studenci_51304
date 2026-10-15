# Pomoc do funkcji w `zadania.py`

## Wzorzec sprawdzania brakującego pola
```python
if not wiersz.get("customer_name", "").strip():
    bledy.append("brak customer_name")
```

## Wzorzec konwersji liczby
```python
from decimal import Decimal, InvalidOperation
try:
    qty = Decimal(wiersz["qty"])
except InvalidOperation:
    bledy.append("qty nie jest liczbą")
```

## Wzorzec daty
```python
from datetime import date
transaction_date = date.fromisoformat(pozycje[0]["transaction_date"])
```

## Wzorzec identyfikatorów zamówień z pozycji faktury
```python
ids = sorted({
    item.get("sales_order", "")
    for item in dokument.get("items", [])
    if item.get("sales_order")
})
text = ",".join(ids)
```

Nie kopiuj API Secret do kodu, raportu ani zrzutu ekranu.

## Prefiks zespołu
Na wspólnej instancji ustaw w `erpnext.env` unikalny `LAB_PREFIX`, np. `A1`. Gotowe procedury dodadzą go do nazw klientów i numerów PO. Nie wpisuj prefiksu ręcznie do CSV.
