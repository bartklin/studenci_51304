"""Dwa małe testy funkcji, NIE pełny klucz do danych ćwiczenia.
Uruchom po uzupełnieniu Z2/Z3: python -m unittest testy_przykladowe -v
Na pustym szkielecie testy zgłoszą ERROR — to oczekiwane.
"""
from decimal import Decimal
import unittest
from zadania import podsumuj, wedlug_segmentu


class Przyklad(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"zamowienie_id": "X1", "klient_id": "K1", "status": "nowe", "kwota_pln": "10.25"},
            {"zamowienie_id": "X2", "klient_id": "K1", "status": "anulowane", "kwota_pln": "20.50"}]

    def test_filtr(self):
        p = podsumuj(self.rows)
        self.assertEqual(p["liczba_wszystkich"], 2)
        self.assertEqual(p["liczba_nieanulowanych"], 1)
        self.assertEqual(p["suma_wszystkich"], Decimal("30.75"))
        self.assertEqual(p["suma_nieanulowanych"], Decimal("10.25"))
        self.assertEqual(p["wykluczone_id"], ["X2"])

    def test_segment(self):
        k = [{"klient_id": "K1", "nazwa": "Test", "segment": "B2B"}]
        self.assertEqual(wedlug_segmentu(self.rows, k), {"B2B": Decimal("10.25")})


if __name__ == "__main__":
    unittest.main(verbosity=2)
