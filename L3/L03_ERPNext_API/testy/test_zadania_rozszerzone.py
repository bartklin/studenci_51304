"""Testy kontraktu z zadania.py. Bez ERPNext, tokenów i połączeń sieciowych."""
from __future__ import annotations
import copy
import sys
import unittest
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import zadania


def klient():
    return {'external_customer_id':'TEST-C','customer_name':'Firma testowa', 'customer_type':'Company',
            'address_line1':'Testowa 1','city':'Opole','country':'Poland'}


def pozycja():
    return {'external_order_id':'TEST-SO','customer_external_id':'TEST-C','transaction_date':'2026-10-16',
            'delivery_date':'2026-10-20','item_code':'TEST-USLUGA','item_name':'Usługa testowa',
            'qty':'2','rate':'50.00','uom':'Nos'}


def faktura():
    return {'name':'TEST-SINV','customer':'TEST-CUST','company':'Firma Test', 'posting_date':'2026-10-20',
            'currency':'PLN','grand_total':120.50,'outstanding_amount':20.50,'status':'Overdue','docstatus':1,
            'items':[{'sales_order':'TEST-SO-B'},{'sales_order':'TEST-SO-A'},{'sales_order':'TEST-SO-B'}, {}, {'sales_order':''}]}


class Z1Klient(unittest.TestCase):
    def test_poprawne_typy(self):
        for typ in ('Company','Individual','Partnership'):
            with self.subTest(typ=typ):
                row=klient(); row['customer_type']=typ
                self.assertEqual(zadania.waliduj_klienta(row), [])

    def test_kazde_pole_wymagane(self):
        for field in klient():
            for value in ('', '   '):
                with self.subTest(pole=field, value=value):
                    row=klient(); row[field]=value
                    result=zadania.waliduj_klienta(row)
                    self.assertIsInstance(result, list)
                    self.assertTrue(result, f'Brak wykrycia pustego {field}')

    def test_brak_klucza(self):
        for field in klient():
            with self.subTest(pole=field):
                row=klient(); del row[field]
                self.assertTrue(zadania.waliduj_klienta(row))

    def test_zly_typ(self):
        row=klient(); row['customer_type']='Robot'
        self.assertTrue(zadania.waliduj_klienta(row))

    def test_nie_modyfikuje_zrodla(self):
        row=klient(); before=copy.deepcopy(row)
        zadania.waliduj_klienta(row)
        self.assertEqual(row,before)


class Z2Zamowienie(unittest.TestCase):
    def test_poprawna_pozycja(self):
        self.assertEqual(zadania.waliduj_zamowienie([pozycja()]), [])

    def test_wiele_pozycji(self):
        a=pozycja(); b=pozycja(); b['item_code']='TEST-USLUGA-2'
        self.assertEqual(zadania.waliduj_zamowienie([a,b]), [])

    def test_puste_zamowienie(self):
        self.assertTrue(zadania.waliduj_zamowienie([]))

    def test_puste_pola_naglowka(self):
        for field in ('external_order_id','customer_external_id','transaction_date','delivery_date'):
            with self.subTest(pole=field):
                row=pozycja(); row[field]=''
                self.assertTrue(zadania.waliduj_zamowienie([row]))

    def test_niespojny_naglowek(self):
        for field, value in [('external_order_id','INNE'),('customer_external_id','INNY'),('transaction_date','2026-10-17'),('delivery_date','2026-10-21')]:
            with self.subTest(pole=field):
                a=pozycja(); b=pozycja(); b['item_code']='TEST-2'; b[field]=value
                self.assertTrue(zadania.waliduj_zamowienie([a,b]))

    def test_datowanie(self):
        for value in ('2026-10-15','2026-02-30','xxx'):
            with self.subTest(data=value):
                row=pozycja(); row['delivery_date']=value
                self.assertTrue(zadania.waliduj_zamowienie([row]))
        row=pozycja(); row['delivery_date']=row['transaction_date']
        self.assertEqual(zadania.waliduj_zamowienie([row]), [])

    def test_puste_pola_pozycji(self):
        for field in ('item_code','item_name','uom'):
            with self.subTest(pole=field):
                row=pozycja(); row[field]='  '
                self.assertTrue(zadania.waliduj_zamowienie([row]))

    def test_liczby(self):
        for field in ('qty','rate'):
            for value in ('0','-1','abc',''):
                with self.subTest(pole=field, value=value):
                    row=pozycja(); row[field]=value
                    self.assertTrue(zadania.waliduj_zamowienie([row]))

    def test_wszystkie_pozycje_nie_tylko_pierwsza(self):
        a=pozycja(); b=pozycja(); b['item_code']='TEST-2'; b['qty']='-1'
        self.assertTrue(zadania.waliduj_zamowienie([a,b]))

    def test_nie_modyfikuje_zrodla(self):
        rows=[pozycja()]; before=copy.deepcopy(rows)
        zadania.waliduj_zamowienie(rows)
        self.assertEqual(rows,before)


class Z3Rozliczenie(unittest.TestCase):
    def test_oplacona(self):
        self.assertEqual(zadania.status_rozliczenia(Decimal('120.50'),Decimal('0')), 'OPLACONA')
    def test_czesciowa(self):
        self.assertEqual(zadania.status_rozliczenia(Decimal('120.50'),Decimal('20.50')), 'CZESCIOWO OPLACONA')
    def test_nieoplacona(self):
        self.assertEqual(zadania.status_rozliczenia(Decimal('120.50'),Decimal('120.50')), 'NIEOPLACONA')
    def test_grosz_nie_jest_zerem(self):
        self.assertEqual(zadania.status_rozliczenia(Decimal('120.50'),Decimal('0.01')), 'CZESCIOWO OPLACONA')


class Z4WierszCSV(unittest.TestCase):
    def test_pelny_wiersz(self):
        doc=faktura(); row=zadania.wiersz_faktury_csv(doc)
        expected={'invoice_id':'TEST-SINV','customer':'TEST-CUST','posting_date':'2026-10-20','currency':'PLN',
                  'grand_total':'120.50','outstanding_amount':'20.50','payment_status':'CZESCIOWO OPLACONA',
                  'sales_orders':'TEST-SO-A,TEST-SO-B','erpnext_status':'Overdue','docstatus':'1','pdf_file':''}
        self.assertEqual(row,expected)
    def test_unikalne_posortowane_referencje(self):
        self.assertEqual(zadania.wiersz_faktury_csv(faktura())['sales_orders'], 'TEST-SO-A,TEST-SO-B')
    def test_brak_referencji(self):
        doc=faktura(); doc['items']=[{}]
        self.assertEqual(zadania.wiersz_faktury_csv(doc)['sales_orders'],'')
    def test_status_wyliczony_z_kwot(self):
        doc=faktura(); doc['outstanding_amount']=0; doc['status']='Unpaid'
        row=zadania.wiersz_faktury_csv(doc)
        self.assertEqual(row['payment_status'],'OPLACONA')
        self.assertEqual(row['erpnext_status'],'Unpaid')
    def test_nie_modyfikuje_zrodla(self):
        doc=faktura(); before=copy.deepcopy(doc)
        zadania.wiersz_faktury_csv(doc)
        self.assertEqual(doc,before)


if __name__=='__main__':
    unittest.main(verbosity=2)
