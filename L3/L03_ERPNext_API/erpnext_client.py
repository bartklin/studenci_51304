from __future__ import annotations
import json
import socket
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler
from konfiguracja import Konfiguracja


class ERPNextAPIError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


class _BezPrzekierowan(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Token nie moze zostac przekazany na obcy host / strone logowania.
        return None


class ERPNextClient:
    """Gotowa warstwa HTTP. Nie zmieniać w ramach zadań studenckich."""
    def __init__(self, cfg: Konfiguracja, timeout: float = 15):
        self.cfg = cfg
        self.timeout = timeout
        self.ssl_context = ssl.create_default_context() if cfg.verify_tls else ssl._create_unverified_context()
        self.opener = build_opener(_BezPrzekierowan(), HTTPSHandler(context=self.ssl_context))

    def _redact(self, text: str) -> str:
        for value in (self.cfg.api_secret, self.cfg.api_key):
            if value:
                text = text.replace(value, '[UKRYTO]')
        return text

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None,
                 payload: dict[str, Any] | None = None, binary: bool = False):
        url = self.cfg.base_url + path
        if params:
            clean = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                     for k, v in params.items() if v is not None}
            url += '?' + urlencode(clean)
        body = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        headers = {'Authorization': f'token {self.cfg.api_key}:{self.cfg.api_secret}',
                   'Accept': 'application/pdf' if binary else 'application/json'}
        if body is not None:
            headers['Content-Type'] = 'application/json; charset=utf-8'
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read()
                if binary:
                    if not raw.startswith(b'%PDF-'):
                        raise ERPNextAPIError('Odpowiedź nie ma nagłówka PDF; możliwy HTML logowania lub błąd generatora.')
                    return raw
                if not raw:
                    return {}
                try:
                    result = json.loads(raw.decode('utf-8-sig'))
                except (UnicodeError, ValueError) as exc:
                    raise ERPNextAPIError('Serwer zwrócił odpowiedź inną niż JSON. Sprawdź BASE_URL, proxy i stronę logowania.') from exc
                if not isinstance(result, dict):
                    raise ERPNextAPIError('Nieoczekiwany format odpowiedzi API (oczekiwano obiektu JSON).')
                return result
        except HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            try:
                detail = json.loads(raw)
                message = detail.get('exception') or detail.get('message') or detail.get('exc_type') or 'Błąd API'
            except (ValueError, AttributeError):
                message = 'Odpowiedź HTML/tekst; sprawdź proxy, adres i autoryzację.'
            if 300 <= exc.code < 400:
                message = 'Przekierowanie zablokowane. Wpisz docelowy adres witryny w BASE_URL; token nie został przesłany dalej.'
            message = ' '.join(self._redact(str(message)).split())[:600]
            raise ERPNextAPIError(f'HTTP {exc.code}: {message}', status=exc.code) from exc
        except (ssl.SSLError, URLError, TimeoutError, socket.timeout, OSError) as exc:
            text = self._redact(str(getattr(exc, 'reason', exc)))
            raise ERPNextAPIError(f'Błąd sieci/TLS: {text}') from exc

    def sprawdz_polaczenie(self) -> str:
        result = self._request('GET', '/api/method/frappe.auth.get_logged_user')
        user = result.get('message')
        if not isinstance(user, str) or not user or user == 'Guest':
            raise ERPNextAPIError('Brak uwierzytelnionego użytkownika (Guest lub niepoprawna odpowiedź).')
        return user

    def lista(self, doctype: str, *, fields: list[str] | None = None,
              filters: list | None = None, limit: int = 100, start: int = 0) -> list[dict]:
        result = self._request('GET', f'/api/resource/{quote(doctype, safe="")}', params={
            'fields': fields or ['name'], 'filters': filters or [],
            'limit_page_length': limit, 'limit_start': start, 'order_by': 'name asc'})
        data = result.get('data')
        if not isinstance(data, list):
            raise ERPNextAPIError(f'Brak listy data w odpowiedzi dla {doctype}.')
        return data

    def lista_wszystkie(self, doctype: str, *, fields=None, filters=None, page_size=100, max_pages=1000):
        out, seen = [], set()
        for page in range(max_pages):
            rows = self.lista(doctype, fields=fields, filters=filters, limit=page_size, start=len(out))
            if not rows:
                return out
            for row in rows:
                name = row.get('name')
                if not name or name in seen:
                    raise ERPNextAPIError('Powtórzona strona lub zmiana danych podczas pobierania. Powtórz odczyt przy stabilnym zbiorze.')
                seen.add(name)
            out.extend(rows)
            # Kolejny odczyt także przy krótkiej stronie: serwer może ograniczać rozmiar strony.
        raise ERPNextAPIError('Przekroczono limit stron; wynik nie jest traktowany jako kompletny.')

    def pobierz(self, doctype: str, name: str) -> dict:
        result = self._request('GET', f'/api/resource/{quote(doctype, safe="")}/{quote(name, safe="")}')
        if not isinstance(result.get('data'), dict) or not result['data'].get('name'):
            raise ERPNextAPIError(f'Brak dokumentu data dla {doctype}.')
        return result['data']

    def utworz(self, doctype: str, payload: dict) -> dict:
        result = self._request('POST', f'/api/resource/{quote(doctype, safe="")}', payload=payload)
        if not isinstance(result.get('data'), dict) or not result['data'].get('name'):
            raise ERPNextAPIError('Brak identyfikatora zapisanego dokumentu. Sprawdź ERPNext przed ponowieniem importu.')
        return result['data']

    def uprawnienie(self, doctype: str, typ: str, name: str = '') -> bool:
        result = self._request('GET', '/api/method/frappe.client.has_permission',
                               params={'doctype': doctype, 'docname': name, 'perm_type': typ})
        message = result.get('message')
        if not isinstance(message, dict) or 'has_permission' not in message:
            raise ERPNextAPIError('Nieoczekiwana odpowiedź testu uprawnień.')
        return bool(message['has_permission'])

    def metadane(self, doctype: str) -> list[dict]:
        result = self._request('GET', '/api/method/frappe.desk.form.load.getdoctype', params={'doctype': doctype})
        docs = result.get('docs')
        if not isinstance(docs, list):
            raise ERPNextAPIError('Brak metadanych formularza w odpowiedzi.')
        return docs

    def pobierz_pdf(self, doctype: str, name: str, print_format: str = 'Standard') -> bytes:
        return self._request('GET', '/api/method/frappe.utils.print_format.download_pdf', params={
            'doctype': doctype, 'name': name, 'format': print_format, 'no_letterhead': 1}, binary=True)
