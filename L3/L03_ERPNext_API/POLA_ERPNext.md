# Pola danych użyte w ćwiczeniu

Poniższa lista jest oparta na standardowych DocType ERPNext/Frappe v15. Własne modyfikacje formularzy, reguły podatkowe i role mogą dodać kolejne wymagania.

## Customer
W kodzie standardowym wymagane są `customer_name` i `customer_type`. Ćwiczenie przekazuje także istniejące `customer_group` i `territory`, aby wynik był jednoznaczny. `tax_id`, e-mail i telefon są opcjonalne.

## Address
Jeżeli importer tworzy adres, wymagane są `address_type`, `address_line1`, `city` oraz `country`. Powiązanie z Customer jest przekazywane w tabeli `links`.

## Item
Pozycje muszą istnieć przed importem zamówień. Minimalny zestaw do ich utworzenia: `item_code`, `item_group`, `stock_uom`; w ćwiczeniu przekazujemy również `item_name`, `is_stock_item=0`, `is_sales_item=1` i `standard_rate`.

## Sales Order
Ćwiczenie przekazuje: `naming_series`, `customer`, `order_type`, `transaction_date`, `delivery_date`, `company`, `currency`, `conversion_rate`, `selling_price_list`, `price_list_currency`, `plc_conversion_rate` oraz `items`.

Każdy element `items` zawiera `item_code`, `item_name`, `qty`, `rate`, `uom`, `conversion_factor` i `delivery_date`. Nazwa jest także przekazywana jawnie, aby import nie zależał od zachowania formularza klienta przeglądarkowego.

## Sales Invoice — eksport
Program nie tworzy faktury przez API. Student tworzy i zatwierdza ją w interfejsie ERPNext. Program odczytuje faktury z `docstatus=1`, zapisuje pełny JSON, próbuje pobrać PDF i buduje lokalny `faktury.csv`.
