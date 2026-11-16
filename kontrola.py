"""Přehled kontrol zpracování – vystup/kontrola.html, kontrola_souhrn.md, kontrola_stav.txt.

Čte výstupy zpracuj_data.py a vyhodnocuje:
  - součty po obcích proti řádku „celkem“ ve zdroji (kde ho zdroj má),
  - součty složek v každém řádku (MŠ, ZŠ, celkem),
  - meziroční změnu za ČR,
  - velké meziroční skoky jednotlivých obcí (do vystup/kontrola_skoky.csv),
  - částku na žáka (zda je ke každému roku žáků).
Spouští se automaticky na konci zpracuj_data.py, samostatně:
    python kontrola.py
"""
import html
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
VYSTUP = ROOT / "vystup"

# Meziroční změna za ČR, nad kterou je nejspíš chyba v načtení (počty se mění o jednotky procent).
MAX_ZMENA_CR = 0.05
# Skok obce: změna celkem aspoň o tolik dětí a zároveň o tolik procent.
SKOK_DETI = 100
SKOK_PODIL = 0.30

ZLOMY = {2016: "Praha, Brno, Ostrava a Liberec ve zdroji vcelku (2014–2015 po MČ, zde sečteno); chybí svazky obcí",
         2019: "zrušen sloupec § 42 (žáci s hlubokým mentálním postižením)",
         2022: "děti z Ukrajiny (+48 tis.)",
         2023: "nový sloupec pocet_rud (bez § 38); chybí svazky obcí",
         2024: "nový sloupec ms_individualni_34b, započtený i do celkem"}
ZLOMY_CASTKA = {2018: "váha kritéria 7 % → 9 %",
                2026: "nové kritérium (děti, žáci a studenti, i kraje), na přepočteného žáka, předběžně"}

STAVY = {"ok": ("V pořádku", "✓"), "info": ("Známý rozdíl", "i"),
         "varovani": ("Ověřit ručně", "!"), "chyba": ("Nesedí", "✕")}

CSS = """
:root{--bg:#f7f6f3;--panel:#fff;--text:#1d1f23;--muted:#6b6f76;--line:#e4e2dc;
--ok:#2f7d4f;--ok-bg:#e6f2ea;--info:#3a6ea5;--info-bg:#e7eef7;--warn:#a86a00;--warn-bg:#fbf0d9;
--err:#b3261e;--err-bg:#fbe5e3;--s-ms:#3a6ea5;--s-zs:#c26a2e;--s-kc:#2f7d4f;--accent:#2f7d4f;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--panel:#1d2024;--text:#e8e6e1;
--muted:#9a9ea5;--line:#30343a;--ok:#6cc08f;--ok-bg:#1c3326;--info:#86b2e0;--info-bg:#1d2a3a;--warn:#e0b04f;
--warn-bg:#3a2e14;--err:#f08a80;--err-bg:#3d1f1c;--s-ms:#6f9fd4;--s-zs:#e0925a;--s-kc:#6cc08f;--accent:#6cc08f;}}
:root[data-theme="dark"]{--bg:#15171a;--panel:#1d2024;--text:#e8e6e1;--muted:#9a9ea5;--line:#30343a;--ok:#6cc08f;
--ok-bg:#1c3326;--info:#86b2e0;--info-bg:#1d2a3a;--warn:#e0b04f;--warn-bg:#3a2e14;--err:#f08a80;--err-bg:#3d1f1c;
--s-ms:#6f9fd4;--s-zs:#e0925a;--s-kc:#6cc08f;--accent:#6cc08f;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 16px 64px}
header h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}
header p{margin:0;color:var(--muted)}
h2{font-size:18px;margin:40px 0 6px}
.popis{color:var(--muted);margin:0 0 14px;max-width:780px}
.karty{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:22px}
.karta{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;border-top:3px solid var(--line)}
.karta.ok{border-top-color:var(--ok)}.karta.info{border-top-color:var(--info)}
.karta.varovani{border-top-color:var(--warn)}.karta.chyba{border-top-color:var(--err)}
.karta h3{font-size:15px;margin:10px 0 4px}.karta p{margin:0;color:var(--muted);font-size:14px}
.odznak{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;padding:2px 9px 2px 3px;border-radius:999px;white-space:nowrap}
.odznak b{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;color:var(--panel);font-size:11px}
.odznak.ok{background:var(--ok-bg);color:var(--ok)}.odznak.ok b{background:var(--ok)}
.odznak.info{background:var(--info-bg);color:var(--info)}.odznak.info b{background:var(--info)}
.odznak.varovani{background:var(--warn-bg);color:var(--warn)}.odznak.varovani b{background:var(--warn)}
.odznak.chyba{background:var(--err-bg);color:var(--err)}.odznak.chyba b{background:var(--err)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px}
.grafy{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.grafy svg{width:100%;height:auto;display:block}
.g-nadpis{font-size:13px;font-weight:600;fill:var(--text)}.g-osa{font-size:11px;fill:var(--muted);text-anchor:middle}
.g-hodnota{font-size:10px;fill:var(--muted);text-anchor:middle}
.s-ms{fill:var(--s-ms)}.s-zs{fill:var(--s-zs)}.s-kc{fill:var(--s-kc)}
rect.zlom{opacity:.75;stroke:var(--text);stroke-dasharray:3 2;stroke-width:1}
.legenda{color:var(--muted);font-size:13px;margin-top:8px}
.legenda i{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 10px;vertical-align:-1px}
.tab-obal{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{font-size:12.5px;color:var(--muted);font-weight:600;background:var(--panel);position:sticky;top:0}
tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}
.c{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.rok{font-weight:600;white-space:nowrap}.zlom-text{display:block;font-weight:400;font-size:12px;color:var(--muted);white-space:normal;max-width:240px}
.tlumene{color:var(--muted);font-size:12.5px}
.zmena{display:block;font-size:12px;color:var(--muted)}.zmena.skok{color:var(--err);font-weight:600}
.prazdne{background:var(--panel);border:1px dashed var(--line);border-radius:10px;padding:14px 16px;color:var(--muted);margin:0}
code{font-family:ui-monospace,Consolas,monospace;font-size:13px;background:var(--line);padding:1px 5px;border-radius:4px}
footer{margin-top:48px;color:var(--muted);font-size:13px}
"""


def cislo(x):
    return "" if pd.isna(x) else f"{int(x):,}".replace(",", " ")


def esc(x):
    return html.escape("" if pd.isna(x) else str(x))


def nacti(jmeno):
    cesta = VYSTUP / jmeno
    return pd.read_csv(cesta) if cesta.exists() else pd.DataFrame()


def odznak(stav):
    text, ikona = STAVY[stav]
    return f'<span class="odznak {stav}"><b>{ikona}</b>{text}</span>'


def karta(nadpis, stav, popis):
    return (f'<div class="karta {stav}"><div class="karta-hlava">{odznak(stav)}</div>'
            f'<h3>{nadpis}</h3><p>{popis}</p></div>')


def zmena(x, mez=None, znamy_zlom=False):
    if pd.isna(x):
        return ""
    trida = "zmena" + (" skok" if mez is not None and abs(x) > mez and not znamy_zlom else "")
    return f"<span class='{trida}'>{x:+.1%}</span>".replace(".", ",")


def graf(nadpis, roky, rady, zlomy=(), popisky=None, sirka=560, vyska=230):
    """Skládaný sloupcový graf v SVG. rady = [(css třída, hodnoty)], popisky = text nad sloupcem."""
    okraj_l, okraj_p, nahore, dole = 10, 10, 34, 24
    soucty = [sum(r[1][i] or 0 for r in rady) for i in range(len(roky))]
    maxi = max(soucty) or 1
    krok = (sirka - okraj_l - okraj_p) / len(roky)
    sloupec = krok * 0.7
    casti = [f'<svg viewBox="0 0 {sirka} {vyska}" role="img" aria-label="{esc(nadpis)}">',
             f'<text class="g-nadpis" x="{okraj_l}" y="16">{esc(nadpis)}</text>']
    vyska_grafu = vyska - nahore - dole
    for i, rok in enumerate(roky):
        x = okraj_l + i * krok + (krok - sloupec) / 2
        y = vyska - dole
        for trida, hodnoty in rady:
            h = (hodnoty[i] or 0) / maxi * vyska_grafu
            y -= h
            casti.append(f'<rect class="{trida}{" zlom" if rok in zlomy else ""}" x="{x:.1f}" y="{y:.1f}" '
                         f'width="{sloupec:.1f}" height="{h:.1f}" rx="2"><title>{rok}: {cislo(hodnoty[i])}</title></rect>')
        if popisky:
            casti.append(f'<text class="g-hodnota" x="{x + sloupec / 2:.1f}" y="{y - 4:.1f}">{popisky[i]}</text>')
        casti.append(f'<text class="g-osa" x="{x + sloupec / 2:.1f}" y="{vyska - 8}">{str(rok)[2:] if len(roky) > 12 else rok}</text>')
    casti.append("</svg>")
    return "".join(casti)


def graf_zaku(k):
    roky = k.rok.tolist()
    ostatni = (k.celkem - k.ms_celkem - k.zs_celkem).tolist()
    return graf("Děti a žáci ve školách obcí (stav k 30. 9.)", roky,
                [("s-ms", k.ms_celkem.tolist()), ("s-zs", k.zs_celkem.tolist()), ("s-kc", ostatni)], zlomy=ZLOMY, popisky=[f"{x / 1e6:.2f}".replace(".", ",") for x in k.celkem])


def graf_castky(c):
    c = c[(c.prijemce == "obce") & (c.jednotka == "žák")]
    return graf("Kč na žáka pro obce (rozpočtový rok)", c.rok.tolist(), [("s-kc", c.castka_na_zaka_kc.tolist())],
                zlomy=ZLOMY_CASTKA, popisky=[f"{x / 1000:.1f}".replace(".", ",") for x in c.castka_na_zaka_kc])


def legenda_zaku():
    return ('<p class="legenda"><i style="background:var(--s-ms)"></i>MŠ<i style="background:var(--s-zs)"></i>ZŠ'
            '<i style="background:var(--s-kc)"></i>ostatní (přípravné třídy, § 38, § 41, gymnázia) · nad sloupcem celkem v mil.'
            ' · čárkovaně roky se zlomem</p>')


def skoky_obci(z):
    z = z.sort_values(["kod_obce", "rok"])
    z["predtim"] = z.groupby("kod_obce").celkem.shift()
    z["rok_predtim"] = z.groupby("kod_obce").rok.shift()
    z = z[z.predtim.notna() & (z.rok - z.rok_predtim == 1)]
    zm = z.celkem - z.predtim
    s = z[(zm.abs() >= SKOK_DETI) & (zm.abs() / z.predtim.clip(lower=1) >= SKOK_PODIL)].copy()
    s["zmena"] = (s.celkem - s.predtim).astype(int)
    s["predtim"] = s.predtim.astype(int)
    return s[["rok", "kod_obce", "nazev_obce", "okres", "predtim", "celkem", "zmena"]].sort_values(["rok", "zmena"])


def vyhodnot(k):
    k = k.copy()
    k["stav"] = "ok"
    k.loc[k.celkem_zdroj.isna(), "stav"] = "info"
    skok_cr = (k.zmena_celkem.abs() > MAX_ZMENA_CR) & ~k.rok.isin(ZLOMY)
    k.loc[skok_cr | (k.radky_nesedi > 0), "stav"] = "varovani"
    k.loc[(k.rozdil.fillna(0) != 0) | k.sloupce_nesedi.fillna("").ne(""), "stav"] = "chyba"
    return k


def tabulka_roku(k):
    radky = []
    for x in k.itertuples():
        zlom = f'<span class="zlom-text">{esc(ZLOMY[x.rok])}</span>' if x.rok in ZLOMY else ""
        radky.append(
            f"<tr><td class='rok'>{x.rok}{zlom}</td><td class='c'>{cislo(x.obci)}</td>"
            f"<td class='c'>{cislo(x.svazku)}</td><td class='c'>{cislo(x.ms_celkem)}</td><td class='c'>{cislo(x.zs_celkem)}</td>"
            f"<td class='c'>{cislo(x.celkem)}{zmena(x.zmena_celkem, MAX_ZMENA_CR, x.rok in ZLOMY)}</td>"
            f"<td class='c'>{cislo(x.celkem_svazky)}</td>"
            f"<td class='c'>{cislo(x.celkem_zdroj) or '<span class=tlumene>není</span>'}</td>"
            f"<td class='c'>{cislo(x.rozdil)}</td><td>{odznak(x.stav)}</td></tr>")
    return ("<div class='tab-obal'><table><thead><tr><th>Rok</th><th class='c'>Obcí</th><th class='c'>Svazků</th>"
            "<th class='c'>MŠ</th><th class='c'>ZŠ</th><th class='c'>Celkem obce</th><th class='c'>Celkem svazky</th>"
            "<th class='c'>Celkem ve zdroji</th><th class='c'>Rozdíl</th><th>Stav</th></tr></thead>"
            f"<tbody>{''.join(radky)}</tbody></table></div>")


def tabulka_castek(c):
    radky = []
    for x in c.itertuples():
        zlom = f'<span class="zlom-text">{esc(ZLOMY_CASTKA[x.rok])}</span>' if x.rok in ZLOMY_CASTKA else ""
        radky.append(
            f"<tr><td class='rok'>{x.rok}{zlom}</td><td>{esc(x.prijemce)}</td>"
            f"<td class='c'>{cislo(x.castka_na_zaka_kc)}{zmena(x.zmena_proti_minulemu_roku)}</td>"
            f"<td>{esc(x.jednotka)}</td><td>{esc(x.stav_zaku_k)}</td><td>{esc(x.udaj)}</td>"
            f"<td class='c'>{'' if pd.isna(x.objem_kc_odhad) else f'{x.objem_kc_odhad / 1e9:.1f} mld.'.replace('.', ',', 1)}</td>"
            f"<td><a href='{esc(x.zdroj)}'>MF</a></td></tr>")
    return ("<div class='tab-obal'><table><thead><tr><th>Rok rozpočtu</th><th>Příjemce</th><th class='c'>Kč na žáka</th>"
            "<th>Jednotka</th><th>Žáci k</th><th>Údaj</th><th class='c'>Odhad objemu</th><th>Zdroj</th></tr></thead>"
            f"<tbody>{''.join(radky)}</tbody></table></div>")


def tabulka(d, sloupce, popisky, cisla=()):
    hlava = "".join(f"<th{' class=c' if s in cisla else ''}>{p}</th>" for s, p in zip(sloupce, popisky))
    radky = "".join("<tr>" + "".join(
        f"<td class='c'>{cislo(getattr(x, s)) if s != 'zmena' else f'{x.zmena:+d}'}</td>" if s in cisla
        else f"<td>{esc(getattr(x, s))}</td>" for s in sloupce) + "</tr>" for x in d.itertuples())
    return f"<div class='tab-obal'><table><thead><tr>{hlava}</tr></thead><tbody>{radky}</tbody></table></div>"


def main():
    k = nacti("kontrola_souctu.csv")
    z = nacti("zaci_obce.csv")
    r = nacti("kontrola_radku.csv")
    c = nacti("castka_na_zaka.csv")
    if k.empty or z.empty:
        print("Chybí výstupy ve vystup/ – nejdřív spusť zpracuj_data.py")
        return 1
    k = vyhodnot(k)
    skoky = skoky_obci(z)
    skoky.to_csv(VYSTUP / "kontrola_skoky.csv", index=False, encoding="utf-8-sig")

    # karty
    chyby = k[k.stav == "chyba"].rok.tolist()
    bez_celkem = k[k.celkem_zdroj.isna()].rok.tolist()
    stav_soucty = "chyba" if chyby else "info" if bez_celkem else "ok"
    popis_soucty = (f"Nesedí součet proti zdroji: {', '.join(map(str, chyby))}." if chyby else
                    "Obce + svazky = řádek celkem ve zdroji, v každém sloupci."
                    + (f" Roky {bez_celkem[0]}–{bez_celkem[-1]} řádek celkem nemají." if bez_celkem else ""))
    n_radky = int(k.radky_nesedi.sum())
    stav_radky = "varovani" if n_radky else "ok"
    popis_radky = (f"V {n_radky} řádcích nesedí MŠ, ZŠ nebo celkem na součet složek." if n_radky else
                   "Ve všech řádcích sedí MŠ celkem, ZŠ celkem i celkem na součet složek.")
    skok_cr = k[(k.zmena_celkem.abs() > MAX_ZMENA_CR) & ~k.rok.isin(ZLOMY)].rok.tolist()
    stav_rada = "varovani" if skok_cr else "ok"
    popis_rada = (f"Změna za ČR nad {MAX_ZMENA_CR:.0%} mimo známé zlomy: {', '.join(map(str, skok_cr))}." if skok_cr
                  else f"Meziroční změna za ČR do {MAX_ZMENA_CR:.0%} (mimo známé zlomy).")
    stav_skoky = "info" if len(skoky) else "ok"
    popis_skoky = (f"{len(skoky)} obcí se změnou o ≥ {SKOK_DETI} dětí a ≥ {SKOK_PODIL:.0%} – obvykle nová škola "
                   "nebo převod na svazek obcí." if len(skoky) else "Žádné velké skoky u obcí.")
    chybi_castka = []
    if c.empty:
        stav_castky, popis_castky = "varovani", "Stránky MF s částkou na žáka nejsou stažené."
    else:
        obce_zak = c[(c.prijemce == "obce") & (c.jednotka == "žák")]
        chybi_castka = sorted(set(k.rok) - set(obce_zak.stav_zaku_k.str[:4].astype(int)))
        stav_castky = "info" if chybi_castka else "ok"
        popis_castky = (f"Částky za rozpočtové roky {int(c.rok.min())}–{int(c.rok.max())}."
                        + (f" Pro žáky k 30. 9. {', '.join(map(str, chybi_castka))} částka zatím není." if chybi_castka
                           else " Ke každému roku žáků je částka."))

    stav = "chyba" if chyby else "varovani" if (n_radky or skok_cr) else "ok"
    (VYSTUP / "kontrola_stav.txt").write_text(stav, encoding="utf-8")

    posledni = k.iloc[-1]
    souhrn = [
        f"**Stav kontrol: {stav}**",
        "",
        f"- Roky: {int(k.rok.min())}–{int(k.rok.max())} (stav k 30. 9.), poslední rok {int(posledni.rok)}: "
        f"{cislo(posledni.obci)} obcí, celkem {cislo(posledni.celkem)} dětí a žáků"
        + (f" (meziročně {posledni.zmena_celkem:+.1%})" if pd.notna(posledni.zmena_celkem) else ""),
        f"- Součty proti řádku celkem ve zdroji: nesedí v {len(chyby)} letech",
        f"- Řádky, kde nesedí součet složek: {n_radky}",
        f"- Obce s meziročním skokem o ≥ {SKOK_DETI} dětí a ≥ {SKOK_PODIL:.0%}: {len(skoky)} (vystup/kontrola_skoky.csv)",
        f"- Částka na žáka – {popis_castky}",
    ]
    (VYSTUP / "kontrola_souhrn.md").write_text("\n".join(souhrn) + "\n", encoding="utf-8")

    grafy = graf_zaku(k) + ("" if c.empty else graf_castky(c))
    stranka = f"""<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kontrola zpracování</title><style>{CSS}</style></head><body><main>
<header><h1>Kontrola zpracování dat MF</h1>
<p>Děti a žáci ve školách zřizovaných obcemi {int(k.rok.min())}–{int(k.rok.max())} (stav k 30. 9.) a částka na žáka ·
vygenerováno {datetime.now():%d. %m. %Y %H:%M}</p></header>

<section class="karty">
{karta("Součty proti zdroji", stav_soucty, popis_soucty)}
{karta("Součty v řádcích", stav_radky, popis_radky)}
{karta("Vývoj za ČR", stav_rada, popis_rada)}
{karta("Skoky obcí", stav_skoky, popis_skoky)}
{karta("Částka na žáka", stav_castky, popis_castky)}
</section>

<h2>Vývoj v čase</h2>
<p class="popis">Skok, který neodpovídá známým zlomům, obvykle znamená chybu v načtení tabulky.</p>
<div class="panel"><div class="grafy">{grafy}</div>{legenda_zaku()}</div>

<h2>Součty po letech</h2>
<p class="popis">Celkem obce + celkem svazky se musí rovnat řádku celkem ve zdroji (v letech 2015–2018 ho zdroj nemá).
MŠ a ZŠ jsou jen za obce.</p>
{tabulka_roku(k)}

<h2>Částka na žáka</h2>
<p class="popis">Kolik obce dostávají ze sdílených daní na jedno dítě nebo žáka. Částka pro rozpočtový rok R se počítá
z počtu dětí a žáků k 30. 9. roku R−1. Odhad objemu = počet pro RUD za všechny obce × částka.</p>
{'<p class="prazdne">Stránky MF s částkami nejsou stažené.</p>' if c.empty else tabulka_castek(c)}

<h2>Řádky, kde nesedí součet složek</h2>
{'<p class="prazdne">Žádné.</p>' if r.empty else tabulka(r, ["rok", "kod_obce", "nazev", "sloupec", "hodnota", "soucet_slozek"],
    ["Rok", "Kód", "Zřizovatel", "Sloupec", "Hodnota", "Součet složek"], cisla=("hodnota", "soucet_slozek"))}

<h2>Velké meziroční skoky obcí</h2>
<p class="popis">Změna celkem aspoň o {SKOK_DETI} dětí a {SKOK_PODIL:.0%} proti předchozímu roku – obvykle nová nebo
zrušená škola, převod školy na svazek obcí, případně chyba ve zdroji.</p>
{'<p class="prazdne">Žádné.</p>' if skoky.empty else tabulka(skoky, ["rok", "kod_obce", "nazev_obce", "okres", "predtim", "celkem", "zmena"],
    ["Rok", "Kód", "Obec", "Okres", "Předchozí rok", "Rok", "Změna"], cisla=("predtim", "celkem", "zmena"))}

<footer>Zdroj: <a href="https://mf.gov.cz/cs/rozpoctova-politika/uzemni-rozpocty/hospodareni-uzemnich-rozpoctu/financovani-materskych-a-zakladnich-skol/2026">MF ČR – Financování mateřských a základních škol</a></footer>
</main></body></html>"""
    (VYSTUP / "kontrola.html").write_text(stranka, encoding="utf-8")
    print("\n".join(souhrn))


if __name__ == "__main__":
    sys.exit(main())
