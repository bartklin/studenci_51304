from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from datetime import date

class BladKonfiguracji(RuntimeError):
    pass

@dataclass(frozen=True)
class Konfiguracja:
    base_url: str
    api_key: str
    api_secret: str
    company: str
    currency: str
    selling_price_list: str
    customer_group: str
    territory: str
    item_group: str
    stock_uom: str
    sales_order_naming_series: str
    print_format: str
    export_from_date: str
    verify_tls: bool
    lab_prefix: str = ""


def _bool(value: str) -> bool:
    return value.strip().lower() not in {'0','false','no','nie'}


def wczytaj_konfiguracje(path: str | Path | None = None) -> Konfiguracja:
    path = Path(path) if path is not None else Path(__file__).resolve().parent / 'erpnext.env'
    if not path.exists():
        raise BladKonfiguracji(
            'Brak pliku erpnext.env. Skopiuj erpnext.env.example jako erpnext.env i uzupełnij dane.'
        )
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise BladKonfiguracji(f'Niepoprawna linia {line_no} konfiguracji; oczekiwano NAZWA=wartość.')
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('\"').strip("'")
    required = [
        'BASE_URL','API_KEY','API_SECRET','COMPANY','CURRENCY','SELLING_PRICE_LIST',
        'CUSTOMER_GROUP','TERRITORY','ITEM_GROUP','STOCK_UOM',
        'SALES_ORDER_NAMING_SERIES','PRINT_FORMAT','EXPORT_FROM_DATE'
    ]
    missing = [k for k in required if not values.get(k) or values.get(k, '').startswith('WPISZ_')]
    if missing:
        raise BladKonfiguracji('Brak wymaganych wartości: ' + ', '.join(missing))
    u = urlsplit(values['BASE_URL'])
    if u.scheme not in {'http', 'https'} or not u.hostname or u.username or u.password or u.query or u.fragment or u.path.rstrip('/'):
        raise BladKonfiguracji('BASE_URL: wymagany adres witryny http(s) bez /app, /api, loginu, hasła i parametrów.')
    if u.hostname.endswith('.example') or u.hostname == 'example.com':
        raise BladKonfiguracji('BASE_URL nadal zawiera przykładową domenę. Wpisz adres własnej instancji.')
    try:
        date.fromisoformat(values['EXPORT_FROM_DATE'])
    except ValueError as exc:
        raise BladKonfiguracji('EXPORT_FROM_DATE musi być datą YYYY-MM-DD.') from exc
    if any('\n' in values[k] or '\r' in values[k] or ':' in values[k] for k in ('API_KEY', 'API_SECRET')):
        raise BladKonfiguracji('Niepoprawna postać API_KEY/API_SECRET.')
    return Konfiguracja(
        base_url=values['BASE_URL'].rstrip('/'),
        api_key=values['API_KEY'], api_secret=values['API_SECRET'],
        company=values['COMPANY'], currency=values['CURRENCY'],
        selling_price_list=values['SELLING_PRICE_LIST'],
        customer_group=values['CUSTOMER_GROUP'], territory=values['TERRITORY'],
        item_group=values['ITEM_GROUP'], stock_uom=values['STOCK_UOM'],
        sales_order_naming_series=values['SALES_ORDER_NAMING_SERIES'],
        print_format=values['PRINT_FORMAT'], export_from_date=values['EXPORT_FROM_DATE'],
        verify_tls=_bool(values.get('VERIFY_TLS','true')),
        lab_prefix=values.get('LAB_PREFIX','').strip(),
    )
