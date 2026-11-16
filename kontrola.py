"""Přehled kontrol zpracování – vystup/kontrola.html, kontrola_souhrn.md, kontrola_stav.txt.

Čte výstupy zpracuj_data.py a vyhodnocuje:
  - součty po obcích proti řádku „celkem“ ve zdroji (kde ho zdroj má),
  - součty složek v každém řádku (MŠ, ZŠ, celkem),
  - meziroční změnu za ČR,
  - velké meziroční skoky jednotlivých obcí (do vystup/kontrola_skoky.csv).
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

ZLOMY = {2016: "Praha, Brno, Ostrava a Liberec ve zdroji vcelku (2014–2015 po MČ, zde sečteno)",
         2019: "zrušen sloupec § 42 (žáci s hlubokým mentálním postižením)",
         2023: "nový sloupec pocet_rud (bez § 38)",
         2024: "nový sloupec ms_individualni_34b, započtený i do celkem"}


def cislo(x):
    return "" if pd.isna(x) else f"{int(x):,}".replace(",", " ")


def esc(x):
    return html.escape("" if pd.isna(x) else str(x))


def nacti(jmeno):
    cesta = VYSTUP / jmeno
    return pd.read_csv(cesta) if cesta.exists() else pd.DataFrame()


def skoky_obci(z):
    z = z.sort_values(["kod_obce", "rok"])
    z["predtim"] = z.groupby("kod_obce").celkem.shift()
    z["rok_predtim"] = z.groupby("kod_obce").rok.shift()
    z = z[z.predtim.notna() & (z.rok - z.rok_predtim == 1)]
    zmena = z.celkem - z.predtim
    s = z[(zmena.abs() >= SKOK_DETI) & (zmena.abs() / z.predtim.clip(lower=1) >= SKOK_PODIL)].copy()
    s["zmena"] = (s.celkem - s.predtim).astype(int)
    s["predtim"] = s.predtim.astype(int)
    return s[["rok", "kod_obce", "nazev_obce", "okres", "predtim", "celkem", "zmena"]].sort_values(["rok", "zmena"])


def main():
    k = nacti("kontrola_souctu.csv")
    z = nacti("zaci_obce.csv")
    r = nacti("kontrola_radku.csv")
    c = nacti("castka_na_zaka.csv")
    if k.empty or z.empty:
        raise SystemExit("Chybí výstupy, nejdřív spusť zpracuj_data.py")

    k["stav"] = "ok"
    k.loc[k.celkem_zdroj.isna(), "stav"] = "info"
    skok_cr = (k.zmena_celkem.abs() > MAX_ZMENA_CR) & ~k.rok.isin(ZLOMY)
    k.loc[skok_cr | (k.radky_nesedi > 0), "stav"] = "varovani"
    k.loc[(k.rozdil.fillna(0) != 0) | k.sloupce_nesedi.fillna("").ne(""), "stav"] = "chyba"

    skoky = skoky_obci(z)
    skoky.to_csv(VYSTUP / "kontrola_skoky.csv", index=False, encoding="utf-8-sig")

    stav = "chyba" if (k.stav == "chyba").any() else "varovani" if (k.stav == "varovani").any() else "ok"
    (VYSTUP / "kontrola_stav.txt").write_text(stav, encoding="utf-8")

    posledni = k.iloc[-1]
    souhrn = [
        f"**Stav kontrol: {stav}**",
        "",
        f"- Roky: {int(k.rok.min())}–{int(k.rok.max())} (stav k 30. 9.), poslední rok {int(posledni.rok)}: "
        f"{cislo(posledni.obci)} obcí, celkem {cislo(posledni.celkem)} dětí a žáků"
        + (f" (meziročně {posledni.zmena_celkem:+.1%})" if pd.notna(posledni.zmena_celkem) else ""),
        f"- Součty proti řádku celkem ve zdroji: nesedí v {int((k.stav == 'chyba').sum())} letech",
        f"- Řádky, kde nesedí součet složek: {int(k.radky_nesedi.sum())}",
        f"- Obce s meziročním skokem o ≥ {SKOK_DETI} dětí a ≥ {SKOK_PODIL:.0%}: {len(skoky)} (vystup/kontrola_skoky.csv)",
    ]
    if not c.empty:
        obce_zak = c[(c.prijemce == "obce") & (c.jednotka == "žák")]
        chybi = sorted(set(k.rok) - set(obce_zak.stav_zaku_k.str[:4].astype(int)))
        posl = c.iloc[-1]
        souhrn.append(f"- Částka na žáka: roky {int(c.rok.min())}–{int(c.rok.max())}, poslední "
                      f"{int(posl.rok)} ({posl.prijemce}): {cislo(posl.castka_na_zaka_kc)} Kč (jednotka: {posl.jednotka}), {posl.udaj}"
                      + (f"; pro žáky k 30. 9. {', '.join(map(str, chybi))} částka zatím není" if chybi else ""))
    (VYSTUP / "kontrola_souhrn.md").write_text("\n".join(souhrn) + "\n", encoding="utf-8")

    barvy = {"ok": "#1a7f37", "info": "#0969da", "varovani": "#bf8700", "chyba": "#cf222e"}
    radky = "".join(
        f"<tr><td>{int(x.rok)}</td><td class=c>{cislo(x.obci)}</td><td class=c>{cislo(x.mestskych_casti)}</td>"
        f"<td class=c>{cislo(x.ms_celkem)}</td><td class=c>{cislo(x.zs_celkem)}</td>"
        f"<td class=c>{cislo(x.celkem)}</td><td class=c>{cislo(x.celkem_zdroj)}</td><td class=c>{cislo(x.rozdil)}</td>"
        f"<td class=c>{'' if pd.isna(x.zmena_celkem) else f'{x.zmena_celkem:+.1%}'}</td>"
        f"<td class=c>{int(x.radky_nesedi)}</td><td>{esc(x.sloupce_nesedi)}</td>"
        f"<td style='color:{barvy[x.stav]}'>{x.stav}</td><td>{esc(ZLOMY.get(x.rok, ''))}</td></tr>"
        for x in k.itertuples())
    tab_skoky = "".join(
        f"<tr><td>{x.rok}</td><td>{x.kod_obce}</td><td>{esc(x.nazev_obce)}</td><td>{esc(x.okres)}</td>"
        f"<td class=c>{cislo(x.predtim)}</td><td class=c>{cislo(x.celkem)}</td><td class=c>{x.zmena:+d}</td></tr>"
        for x in skoky.itertuples())
    tab_radky = "" if r.empty else "".join(
        f"<tr><td>{x.rok}</td><td>{x.kod_obce}</td><td>{esc(x.nazev)}</td><td>{x.sloupec}</td>"
        f"<td class=c>{cislo(x.hodnota)}</td><td class=c>{cislo(x.soucet_slozek)}</td></tr>" for x in r.itertuples())
    tab_castky = "<p>Stránky MF s částkami nejsou stažené.</p>" if c.empty else (
        "<table><tr><th>rok rozpočtu</th><th>příjemce</th><th>Kč na žáka</th><th>jednotka</th><th>žáci k</th>"
        "<th>údaj</th><th>změna</th><th>odhad objemu</th></tr>" + "".join(
            f"<tr><td>{x.rok}</td><td>{x.prijemce}</td><td class=c>{cislo(x.castka_na_zaka_kc)}</td><td>{esc(x.jednotka)}</td>"
            f"<td>{esc(x.stav_zaku_k)}</td><td>{esc(x.udaj)}</td>"
            f"<td class=c>{'' if pd.isna(x.zmena_proti_minulemu_roku) else f'{x.zmena_proti_minulemu_roku:+.1%}'}</td>"
            f"<td class=c>{cislo(x.objem_kc_odhad)}</td></tr>" for x in c.itertuples()) + "</table>")
    stranka = f"""<!doctype html><html lang=cs><meta charset=utf-8>
<title>Kontrola – děti a žáci</title>
<style>body{{font:14px system-ui,sans-serif;margin:24px;max-width:1200px}}table{{border-collapse:collapse;margin:8px 0 24px}}
td,th{{border:1px solid #ccc;padding:3px 8px;text-align:left}}.c{{text-align:right}}th{{background:#f4f4f4}}</style>
<h1>Kontrola zpracování – děti a žáci ve školách zřizovaných obcemi</h1>
<p>Stav: <b style='color:{barvy[stav]}'>{stav}</b> · vytvořeno {datetime.now():%d. %m. %Y %H:%M}</p>
<h2>Součty za ČR po letech</h2>
<p>Součet obcí se porovnává s řádkem celkem ve zdroji (v letech 2015–2018 ho zdroj nemá – stav info).
Chyba = nesedí některý sloupec; varování = nesedí součet složek v řádcích nebo meziroční změna za ČR
nad {MAX_ZMENA_CR:.0%} mimo známé zlomy.</p>
<table><tr><th>rok</th><th>obcí</th><th>řádků MČ</th><th>MŠ</th><th>ZŠ</th><th>celkem</th><th>celkem ve zdroji</th>
<th>rozdíl</th><th>změna</th><th>řádky nesedí</th><th>sloupce nesedí</th><th>stav</th><th>zlom</th></tr>{radky}</table>
<h2>Řádky, kde nesedí součet složek</h2>
{'<p>Žádné.</p>' if not tab_radky else '<table><tr><th>rok</th><th>kód</th><th>zřizovatel</th><th>sloupec</th><th>hodnota</th><th>součet složek</th></tr>' + tab_radky + '</table>'}
<h2>Částka na žáka (rozpočtové určení daní)</h2>
{tab_castky}
<h2>Velké meziroční skoky obcí</h2>
<p>Změna celkem aspoň o {SKOK_DETI} dětí a {SKOK_PODIL:.0%} proti předchozímu roku – obvykle nová nebo zrušená
škola, převod školy na jiného zřizovatele, případně chyba ve zdroji.</p>
<table><tr><th>rok</th><th>kód</th><th>obec</th><th>okres</th><th>předchozí rok</th><th>rok</th><th>změna</th></tr>{tab_skoky}</table>
</html>"""
    (VYSTUP / "kontrola.html").write_text(stranka, encoding="utf-8")
    print("\n".join(souhrn))


if __name__ == "__main__":
    sys.exit(main())
