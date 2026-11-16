"""Sestaví web pro GitHub Pages do složky _site/.

Úvodní stránka s popisem, vývojem v čase a odkazy ke stažení, přehled kontrol a samotná CSV (+ xlsx).
Spouští ho workflow .github/workflows/pages.yml, lokálně:
    python web.py
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

import kontrola

ROOT = Path(__file__).resolve().parent
VYSTUP = ROOT / "vystup"
WEB = ROOT / "_site"
REPO = "https://github.com/opendatabrno/zaci"
ZDROJ = ("https://mf.gov.cz/cs/rozpoctova-politika/uzemni-rozpocty/hospodareni-uzemnich-rozpoctu/"
         "financovani-materskych-a-zakladnich-skol/2026")

SADY = [
    ("zaci_obce.csv", "Děti a žáci v obcích",
     "Obce, které zřizují aspoň jednu MŠ nebo ZŠ, jeden řádek = obec × rok (stav k 30. 9.), "
     "s odhadem prostředků ze sdílených daní. Klíč rok + kod_obce."),
    ("zaci_svazky_obci.csv", "Školy svazků obcí",
     "Školy zřizované dobrovolnými svazky obcí (ve zdroji bez kódu obce), jeden řádek = svazek × rok. "
     "Obce + svazky = celá ČR."),
    ("castka_na_zaka.csv", "Částka na žáka",
     "Kolik obce dostávají ze sdílených daní na jedno dítě nebo žáka, rozpočtové roky 2013–2026, "
     "s meziroční změnou a odhadem celkového objemu."),
]

SLOUPCE = [
    ("rok, datum", "rok a den stavu (30. 9.); v tabulce částek <code>rok</code> = rozpočtový rok"),
    ("kod_obce, nazev_obce", "kód ČSÚ a název obce, která školy zřizuje"),
    ("kod_okresu, okres, kod_kraje, kraj", "okres a kraj podle aktuálního číselníku obcí"),
    ("ms_bezne_tridy, ms_specialni_tridy, ms_celkem", "děti v mateřských školách"),
    ("ms_individualni_34b", "děti s individuálním předškolním vzděláváním (od 2024, započtené i v celkem)"),
    ("zs_specialni_pripravny_stupen, zs_pripravne_tridy", "děti v přípravném stupni ZŠ speciální a v přípravných třídách"),
    ("zs_bezne_tridy, zs_specialni_tridy, zs_celkem", "žáci základních škol"),
    ("zs_zahranici_38, zs_individualni_41", "žáci vzdělávající se v zahraničí (§ 38) a individuálně (§ 41)"),
    ("zs_hluboke_postizeni_42", "žáci s hlubokým mentálním postižením (§ 42, jen 2014–2018)"),
    ("gym_nizsi_stupen, gym_zahranici_38", "žáci nižšího stupně víceletých gymnázií zřizovaných obcí"),
    ("celkem", "děti a žáci celkem"),
    ("pocet_rud", "počet pro rozpočtové určení daní (od 2023, bez § 38)"),
    ("rok_rozpoctu, odhad_prostredku_kc", "rok, kdy obec za tyto žáky dostává peníze (rok + 1), a odhad částky: "
                                          "počet pro RUD × Kč na žáka"),
    ("castka_na_zaka_kc, jednotka, udaj", "tabulka částek: Kč na žáka (od 2026 na přepočteného žáka), "
                                          "skutečnost nebo předběžný údaj"),
]


def velikost(cesta):
    mb = cesta.stat().st_size / 1_000_000
    return (f"{mb:.1f} MB" if mb >= 0.1 else f"{cesta.stat().st_size // 1000} kB").replace(".", ",")


def main():
    if not (VYSTUP / "kontrola_souctu.csv").exists():
        print("Chybí výstupy ve vystup/ – nejdřív spusť zpracuj_data.py")
        return 1
    kontrola.main()
    shutil.rmtree(WEB, ignore_errors=True)
    WEB.mkdir()
    shutil.copy(VYSTUP / "kontrola.html", WEB / "kontrola.html")

    karty = []
    for soubor, nazev, popis in SADY:
        cesta = VYSTUP / soubor
        shutil.copy(cesta, WEB / soubor)
        # xlsx se v repozitáři neukládá, vzniká tady z CSV
        d = pd.read_csv(cesta, dtype={"kod_obce": str})
        for s in d.columns:
            if d[s].dtype == float and d[s].dropna().mod(1).eq(0).all():
                d[s] = d[s].astype("Int64")
        xlsx = WEB / cesta.with_suffix(".xlsx").name
        d.to_excel(xlsx, index=False, freeze_panes=(1, 0))
        karty.append(
            f'<div class="karta ok"><h3>{nazev}</h3><p>{popis}</p>'
            f'<p class="meta">{d.rok.min()}–{d.rok.max()} · {kontrola.cislo(len(d))} řádků</p>'
            f'<div class="tlacitka"><a class="tlacitko" href="{soubor}" download>CSV · {velikost(cesta)}</a>'
            f'<a class="tlacitko druhe" href="{xlsx.name}" download>Excel · {velikost(xlsx)}</a></div></div>')
    sloupce = "".join(f"<tr><td><code>{s}</code></td><td>{p}</td></tr>" for s, p in SLOUPCE)
    stav = (VYSTUP / "kontrola_stav.txt").read_text(encoding="utf-8").strip()

    k = pd.read_csv(VYSTUP / "kontrola_souctu.csv")
    c = pd.read_csv(VYSTUP / "castka_na_zaka.csv")
    grafy = kontrola.graf_zaku(k) + kontrola.graf_castky(c)
    obce = c[(c.prijemce == "obce") & (c.jednotka == "žák")]
    posl = obce.iloc[-1]
    prvni = obce.iloc[0]

    stranka = f"""<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Děti a žáci ve školách obcí</title><style>{kontrola.CSS}
.meta{{font-size:13px;margin-top:8px!important}}
.tlacitko{{display:inline-block;margin-top:12px;padding:7px 14px;border-radius:8px;background:var(--accent);
color:var(--panel);text-decoration:none;font-weight:600;font-size:14px}}
.tlacitko:hover{{filter:brightness(1.1)}}
.tlacitka{{display:flex;gap:8px;flex-wrap:wrap}}
.tlacitko.druhe{{background:transparent;color:var(--accent);box-shadow:inset 0 0 0 1.5px var(--accent)}}
a{{color:var(--info)}}
.odkazy{{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;align-items:center}}
</style></head><body><main>
<header><h1>Děti a žáci ve školách zřizovaných obcemi</h1>
<p>Počty dětí v mateřských a žáků v základních školách, které zřizují obce, po obcích za roky
{k.rok.min()}–{k.rok.max()} (stav k 30. září), a částka, kterou obce za jedno dítě nebo žáka dostávají
ze sdílených daní. Zdrojem jsou tabulky Ministerstva financí ČR.</p>
<div class="odkazy">{kontrola.odznak(stav)}<a href="kontrola.html">Přehled kontrol</a>
<a href="{REPO}">Zdrojový kód a dokumentace</a></div></header>

<h2>Datové sady</h2>
<section class="karty">{''.join(karty)}</section>

<h2>Vývoj v čase</h2>
<p class="popis">V roce {k.rok.max()} chodilo do škol obcí {kontrola.cislo(k.celkem.iloc[-1] + k.celkem_svazky.iloc[-1])}
dětí a žáků. Částka na žáka vzrostla z {kontrola.cislo(prvni.castka_na_zaka_kc)} Kč ({prvni.rok}) na
{kontrola.cislo(posl.castka_na_zaka_kc)} Kč ({posl.rok}); skok v roce 2018 je zvýšení váhy kritéria ze 7 na 9 %.
Pro rok 2026 je zatím jen předběžný údaj podle nového kritéria (viz tabulka částek).</p>
<div class="panel"><div class="grafy">{grafy}</div>{kontrola.legenda_zaku()}</div>

<h2>Sloupce</h2>
<p class="popis"><code>ms_celkem</code> = běžné + speciální třídy MŠ, <code>zs_celkem</code> = běžné + speciální
třídy ZŠ, <code>celkem</code> = MŠ + § 34b + přípravné třídy + ZŠ + § 38 + § 41 + § 42 + gymnázia.
Prázdná hodnota = sloupec v tom roce ve zdroji není.</p>
<div class="tab-obal"><table><thead><tr><th>Sloupec</th><th>Význam</th></tr></thead>
<tbody>{sloupce}</tbody></table></div>

<h2>Na co si dát pozor</h2>
<div class="panel"><ul>
<li>Počty jsou podle <b>obce, která školu zřizuje</b>, ne podle bydliště dětí. Obec bez vlastní školy v tabulce
není. Pro podíly na obyvatele je lepší sčítat za okresy nebo ORP.</li>
<li>Jen školy obcí a jejich svazků – krajské, církevní a soukromé školy tu nejsou.</li>
<li>Spojení s <a href="https://opendatabrno.github.io/obyvatele/">obyvateli obcí</a>: přes <code>kod_obce</code>,
stav k 30. 9. roku R odpovídá nejlépe obyvatelům k 1. 1. roku R+1.</li>
<li>Svazky obcí ve zdroji chybí v letech 2016 a 2023 (celkem za ČR je o 1–2,4 tis. nižší).</li>
<li>Roky 2014–2015: Praha, Brno, Ostrava a Liberec jsou ve zdroji po městských částech, tady sečtené na město.</li>
<li>2022: +48 tis. dětí a žáků – děti z Ukrajiny. 2024: nově § 34b, započtené i v celkem.</li>
<li><code>odhad_prostredku_kc</code> je odhad: obec dostává peníze podle počtů ve vyhlášce MF a do roku 2022
zdroj neuvádí přesný počet pro RUD. Peníze nejsou účelové.</li>
<li>Od roku 2026 se kritérium mění (děti, žáci a studenti, i kraje; částka na přepočteného žáka) – není
srovnatelné se staršími roky.</li>
</ul></div>

<footer>Zdroj: <a href="{ZDROJ}">MF ČR – Financování mateřských a základních škol</a> ·
aktualizováno {datetime.now():%d. %m. %Y}</footer>
</main></body></html>"""
    (WEB / "index.html").write_text(stranka, encoding="utf-8")
    print(f"Web: {WEB}")


if __name__ == "__main__":
    sys.exit(main())
