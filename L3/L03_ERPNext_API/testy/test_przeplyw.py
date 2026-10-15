"""Lokalny test integracji funkcji z procedurami; API zastępuje FakeAPI.
Nie jest testem prawdziwej instancji ERPNext. Pliki wynikowe powstają w temp.
"""
from __future__ import annotations
import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import procedury
import zadania
from konfiguracja import Konfiguracja
from kontrola_wyniku import check


def config():
    return Konfiguracja('https://test.invalid','fake-key','fake-secret','Firma Test','PLN','Test Selling',
        'Commercial','Poland','Services','Nos','SAL-ORD-.YYYY.-','Standard','2026-10-01',True,'TEST')


class FakeAPI:
    def __init__(self):
        self.docs={}
        self.creates=[]
        self.sequence=0
    def lista(self,dt,*,fields=None,filters=None,limit=100,start=0):
        result=[]
        for (kind,name),doc in self.docs.items():
            if kind!=dt: continue
            matches=True
            for _,field,op,value in filters or []:
                actual=doc.get(field)
                if op=='=': matches &= actual==value
                elif op=='>=': matches &= str(actual)>=str(value)
                else: raise AssertionError(op)
            if matches: result.append(copy.deepcopy(doc))
        return sorted(result,key=lambda d:d['name'])[start:start+limit]
    def lista_wszystkie(self,dt,**kwargs):
        kwargs.pop('page_size',None)
        return self.lista(dt,limit=10000,**kwargs)
    def utworz(self,dt,payload):
        self.sequence+=1
        doc=copy.deepcopy(payload);doc['name']=f'TEST-{dt}-{self.sequence}'
        doc.setdefault('docstatus',0)
        self.docs[(dt,doc['name'])]=doc
        self.creates.append((dt,copy.deepcopy(payload)))
        return copy.deepcopy(doc)
    def pobierz(self,dt,name):
        return copy.deepcopy(self.docs[(dt,name)])
    def pobierz_pdf(self,*a):
        # Atrapa bajtów; nie przekazujemy tego jako prawdziwej faktury PDF.
        return b'%PDF-1.4\nTEST DOUBLE ONLY\n%%EOF'


class Przeplyw(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.output=Path(self.temp.name)/'wyniki'
        self.patch=patch.object(procedury,'WYNIKI',self.output);self.patch.start()
        self.client=FakeAPI(); self.cfg=config()
    def tearDown(self):
        self.patch.stop();self.temp.cleanup()
    def seed(self):
        mapping=procedury.importuj_klientow(self.client,self.cfg)
        orders=procedury.importuj_zamowienia(self.client,self.cfg)
        self.assertEqual(len(mapping),5)
        self.assertEqual(len(orders),5)
        return mapping,orders
    def invoice(self,mapping,orders):
        doc={'name':'TEST-SINV-001','customer':mapping['C001'],'company':self.cfg.company,'posting_date':'2026-10-20',
             'currency':'PLN','grand_total':1900,'outstanding_amount':900,'status':'Unpaid','docstatus':1,
             'items':[{'sales_order':orders[0]['erpnext_name']},{'sales_order':orders[0]['erpnext_name']}]}
        self.client.docs[('Sales Invoice',doc['name'])]=doc
    def test_wszystkie_cztery_funkcje_sa_wywolane(self):
        with patch.object(zadania,'waliduj_klienta',wraps=zadania.waliduj_klienta) as c, \
             patch.object(zadania,'waliduj_zamowienie',wraps=zadania.waliduj_zamowienie) as o, \
             patch.object(zadania,'wiersz_faktury_csv',wraps=zadania.wiersz_faktury_csv) as w, \
             patch.object(zadania,'status_rozliczenia',wraps=zadania.status_rozliczenia) as s:
            mapping,orders=self.seed(); self.invoice(mapping,orders)
            output=procedury.eksportuj_faktury(self.client,self.cfg)
            self.assertEqual(c.call_count,5)
            self.assertEqual(o.call_count,5)
            self.assertEqual(w.call_count,1)
            self.assertGreaterEqual(s.call_count,1)
            self.assertEqual(output[0]['payment_status'],'CZESCIOWO OPLACONA')
            self.assertEqual(check(self.output)['wynik'],'ZGODNY_Z_LOKALNYM_JSON')
    def test_odrzucenie_klienta_nie_wysyla_POST(self):
        with patch.object(zadania,'waliduj_klienta',return_value=['celowe odrzucenie']):
            mapping=procedury.importuj_klientow(self.client,self.cfg)
        self.assertEqual(mapping,{})
        self.assertEqual(self.client.creates,[])
    def test_odrzucenie_zamowienia_nie_wysyla_POST(self):
        procedury.importuj_klientow(self.client,self.cfg)
        count=len(self.client.creates)
        with patch.object(zadania,'waliduj_zamowienie',return_value=['celowe odrzucenie']):
            result=procedury.importuj_zamowienia(self.client,self.cfg)
        self.assertEqual(len(self.client.creates),count)
        self.assertTrue(all(r['status']=='ODRZUCONY' for r in result))
    def test_ponowienie_nie_dubluje_probki(self):
        self.seed(); count=len(self.client.creates)
        self.seed()
        self.assertEqual(count,len(self.client.creates))
    def test_faktura_innej_firmy_nie_jest_pobierana(self):
        mapping,orders=self.seed(); self.invoice(mapping,orders)
        self.client.docs[('Sales Invoice','TEST-SINV-001')]['company']='Inna firma'
        result=procedury.eksportuj_faktury(self.client,self.cfg)
        self.assertEqual(result,[])
        self.assertEqual(check(self.output)['wynik'],'BRAK_DANYCH')
    def test_rozbieznosc_CSV_jest_wykrywana(self):
        mapping,orders=self.seed();self.invoice(mapping,orders)
        procedury.eksportuj_faktury(self.client,self.cfg)
        p=self.output/'faktury.csv';text=p.read_text(encoding='utf-8-sig')
        p.write_text(text.replace('900.00','899.00'),encoding='utf-8-sig')
        self.assertEqual(check(self.output)['wynik'],'BLAD')
    def test_za_wczesna_faktura_nie_jest_pobierana(self):
        mapping,orders=self.seed();self.invoice(mapping,orders)
        self.client.docs[('Sales Invoice','TEST-SINV-001')]['posting_date']='2026-09-30'
        self.assertEqual(procedury.eksportuj_faktury(self.client,self.cfg),[])
    def test_robocza_faktura_nie_jest_pobierana(self):
        mapping,orders=self.seed();self.invoice(mapping,orders)
        self.client.docs[('Sales Invoice','TEST-SINV-001')]['docstatus']=0
        self.assertEqual(procedury.eksportuj_faktury(self.client,self.cfg),[])


if __name__=='__main__':unittest.main(verbosity=2)
