"""OPCJONALNE — tylko po podstawowych zadaniach i testach."""
import json
import reguly
from biblioteka import wczytaj_firme, BAZA
from analiza import analizuj_zamowienia, plan_przydzialu
if __name__ == "__main__":
    f=wczytaj_firme(); r=analizuj_zamowienia(f,reguly)
    p=plan_przydzialu(f,r)
    (BAZA/"wyniki").mkdir(exist_ok=True)
    (BAZA/"wyniki/przydzial.json").write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(p,ensure_ascii=False,indent=2))
    print("Nie zapisano niczego do magazynu. To tylko symulacja nowego przydziału.")
