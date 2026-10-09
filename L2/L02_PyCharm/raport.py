"""Raport HTML/JSON działający offline; brak zewnętrznych bibliotek i zasobów."""
import html
import json
from pathlib import Path
from biblioteka import BAZA

STYLE = """body{margin:0;background:#f4f7fc;color:#182840;font:16px Arial,sans-serif}header{background:#112b53;color:white;padding:28px 5%}main{margin:25px auto;max-width:1120px;padding:0 20px}h1{margin:0 0 8px}.cards{display:flex;gap:16px}.card{background:white;border:1px solid #d9e3f1;border-radius:10px;padding:18px;flex:1}.num{font-size:36px;font-weight:bold;color:#0061f2}table{background:white;width:100%;border-collapse:collapse;font-size:14px}td,th{padding:10px;border-bottom:1px solid #dbe4ef;text-align:left}th{background:#e9f1fd}section{margin-top:24px}.bar{height:22px;background:#0061f2;display:inline-block;vertical-align:middle}.warn{padding:16px;background:#fff3d6;border-left:5px solid #bd7800}.small{color:#52627a;font-size:13px}select{font:inherit;padding:8px}code{background:#edf2f8;padding:2px 5px}svg{max-width:100%} .status{font-weight:bold} """

def _pln(n): return f"{n//100},{n%100:02d}"

def zapisz_raport(raport,katalog=None,nazwa="raport"):
    d=Path(katalog) if katalog else BAZA/"wyniki"
    d.mkdir(parents=True,exist_ok=True)
    (d/(nazwa+".json")).write_text(json.dumps(raport,ensure_ascii=False,indent=2),encoding="utf-8")
    e=html.escape
    meta=raport["metadane"]
    cards=[("Poprawne rekordy",str(len(raport["wiersze"]))),("Kwarantanna",str(len(raport["kwarantanna"]))),("Otwarte wg reguły",str(raport["otwarte"])),("Opóźnione wg reguły",str(raport["opoznione"]))]
    status="REGUŁY WYKONAŁY SIĘ — sprawdź poprawność" if raport["kompletne"] else "NIEKOMPLETNE REGUŁY — to nie jest wynik końcowy"
    b=['<!doctype html><html lang="pl"><meta charset="utf-8"><title>L02 — raport firmy</title><style>'+STYLE+'</style>',
       '<header><h1>Firma DEMO / L02</h1><div>Sprzedaż · klienci · magazyn · wpłaty</div></header><main>',
       '<p class="small">Dane syntetyczne • '+e(meta["snapshot"])+ ' • dzień oceny '+e(meta["dzien_oceny"])+ '</p>',
       '<p class="warn">'+e(status)+'</p><div class="cards">']
    for title,val in cards:b.append('<div class="card"><div>'+e(title)+'</div><div class="num">'+e(val)+'</div></div>')
    b.append('</div><section><h2>Decyzje dla pojedynczych zamówień</h2><p>Kwalifikacja względem tej samej migawki. Bez rezerwacji i bez wykonywania wysyłki.</p><div class="card">')
    for label,n in sorted(raport["decyzje"].items()):
        b.append('<p style="margin:8px 0"><span style="display:inline-block;width:240px">'+e(label)+'</span><span class="bar" style="width:'+str(n*32)+'px"></span> '+str(n)+'</p>')
    b.append('</div></section><section><h2>Karty zamówień</h2><label>Filtr decyzji: <select id="filtr"><option value="">Wszystkie</option>')
    for label in sorted(raport["decyzje"]):b.append('<option>'+e(label)+'</option>')
    b.append('</select></label><p class="small">Kwoty PLN. Jedno zamówienie = jeden produkt. Czas realizacji i wpłata to odrębne informacje.</p><table><thead><tr>')
    for h in ['ID','Produkt','Status','Wartość','Wpłaty','Brak szt.','Priorytet','Decyzja']:b.append('<th>'+h+'</th>')
    b.append('</tr></thead><tbody>')
    for r in raport['wiersze']:
        dec=r['decyzja'] or 'BRAK_WYNIKU'; b.append('<tr data-decyzja="'+e(dec)+'">')
        for v in [r['id'],r['produkt'],r['status'],_pln(r['wartosc_gr']),_pln(r['wplacono_gr']),r['brakuje_szt'],r['priorytet'] or '—',dec]:b.append('<td>'+e(str(v))+'</td>')
        b.append('</tr>')
    b.append('</tbody></table></section><section><h2>Kwarantanna danych</h2><p>Wyłączona z decyzji; nie jest kategorią biznesową „anulowane”.</p><ul>')
    for r in raport['kwarantanna']:b.append('<li>'+e(r['id']+': '+', '.join(r['przyczyny']))+'</li>')
    b.append('</ul></section><section><h2>Wykonanie reguł</h2><p>'+e(raport['uwaga'])+'</p><ul>')
    for r in raport['problemy_regul']:b.append('<li>'+e(r['id']+': '+r['problem'])+'</li>')
    b.append('</ul></section><p class="small">Projekt dydaktyczny: dr inż. Bartłomiej Klin, semestr zimowy 2026/2027.</p></main><script>document.getElementById("filtr").onchange=function(){document.querySelectorAll("tr[data-decyzja]").forEach(r=>r.hidden=!!this.value&&r.dataset.decyzja!==this.value)}</script></html>')
    path=d/(nazwa+".html");path.write_text(''.join(b),encoding="utf-8")
    return path
