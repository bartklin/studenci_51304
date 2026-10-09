"""Przykłady kontrolne. Przed uzupełnieniem reguł FAIL jest oczekiwany.
Przykłady testują kontrakt; nie zastępują wyjaśnienia decyzji.
"""
import unittest
from dataclasses import replace
import reguly
from biblioteka import wczytaj_firme, pokaz_zamowienie
class TestRegul(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.z=pokaz_zamowienie(wczytaj_firme(),"Z001")
    def test_otwarte(self): self.assertIs(reguly.czy_otwarte(self.z),True)
    def test_zakonczone_nie_otwarte(self): self.assertIs(reguly.czy_otwarte(replace(self.z,status="zrealizowane")),False)
    def test_dzien_terminu(self): self.assertIs(reguly.czy_opoznione(replace(self.z,dni_po_terminie=0)),False)
    def test_vip_po_terminie(self): self.assertEqual(reguly.priorytet(self.z),"PILNE")
    def test_wpelni_oplacone(self): self.assertEqual(reguly.decyzja(self.z),"GOTOWE")
    def test_czesciowa_wplata(self): self.assertEqual(reguly.decyzja(replace(self.z,wplacono_gr=1)),"UZUPELNIJ_PLATNOSC")
    def test_anulowanie_przed_blokada(self): self.assertEqual(reguly.decyzja(replace(self.z,status="anulowane",blokada_klienta=True)),"POMIN_ANULOWANE")
    def test_stan_rowny_ilosci(self): self.assertEqual(reguly.decyzja(replace(self.z,dostepne_szt=2,brakuje_szt=0)),"GOTOWE")
if __name__ == "__main__": unittest.main(verbosity=2)
