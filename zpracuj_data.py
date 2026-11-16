"""Zpracování tabulek MF do jedné tabulky dětí a žáků podle obcí.

Vstup:  data/RRRR-09-30 Počty dětí a žáků.xlsx (stahni_data.py)
        ciselniky/pscoco.csv, ciselniky/cnumnuts.csv (stahni_data.py)
Výstup: vystup/zaci_obce.csv a .xlsx      – jeden řádek = obec (zřizovatel) × rok
        vystup/zaci_svazky_obci.csv      – školy zřizované svazky obcí (bez kódu obce)
        vystup/castka_na_zaka.csv        – částka na žáka po rozpočtových letech (castky.py)
        vystup/kontrola_souctu.csv        – součty za rok proti řádku „celkem“ ze zdroje
        vystup/kontrola_radku.csv         – řádky, kde nesedí součet složek (jen když nějaké jsou)

Zdroj má u každého řádku kód obce ČSÚ (ZÚJ) zřizovatele, takže se nic nepáruje podle
názvů. V letech 2014 a 2015 jsou Praha, Brno, Ostrava a Liberec rozepsané po městských
částech; ty se sčítají na celé město podle sloupce statutárního města.

Použití:
    python zpracuj_data.py
"""
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CISELNIKY = ROOT / "ciselniky"
VYSTUP = ROOT / "vystup"

# Sloupce s počty v pořadí výstupu. Hlavičky zdroje se mapují podle klíčových slov (viz sloupec()).
POCTY = [
    "ms_bezne_tridy", "ms_specialni_tridy", "ms_celkem", "ms_individualni_34b",
    "zs_specialni_pripravny_stupen", "zs_pripravne_tridy",
    "zs_bezne_tridy", "zs_specialni_tridy", "zs_celkem",
    "zs_zahranici_38", "zs_individualni_41", "zs_hluboke_postizeni_42",
    "gym_nizsi_stupen", "gym_zahranici_38",
    "celkem", "pocet_rud",
]
# složky, které dávají dohromady sloupec celkem (ms_celkem a zs_celkem jsou mezisoučty)
SLOZKY_CELKEM = ["ms_celkem", "ms_individualni_34b", "zs_specialni_pripravny_stupen", "zs_pripravne_tridy",
                 "zs_celkem", "zs_zahranici_38", "zs_individualni_41", "zs_hluboke_postizeni_42",
                 "gym_nizsi_stupen", "gym_zahranici_38"]
MEZISOUCTY = {"ms_celkem": ["ms_bezne_tridy", "ms_specialni_tridy"],
              "zs_celkem": ["zs_bezne_tridy", "zs_specialni_tridy"]}


def klic(text):
    """Text malými písmeny, bez diakritiky a s jednotnými mezerami (pro hlavičky)."""
    if pd.isna(text):
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def sloupec(hlavicka):
    """Název výstupního sloupce pro hlavičku sloupce s počty, nebo None, když ji neznáme."""
    h = klic(hlavicka)
    # celkem první: od 2024 je v hlavičce „(včetně § 34b a § 38)“
    if h.startswith("deti a zaci celkem"):
        return "celkem"
    if "34b" in h:
        return "ms_individualni_34b"
    if "(§ 38)" in h or "§ 38" in h or "(38)" in h:
        return "gym_zahranici_38" if "gymnazi" in h else "zs_zahranici_38"
    if "§ 41" in h:
        return "zs_individualni_41"
    if "§ 42" in h:
        return "zs_hluboke_postizeni_42"
    if "ucely rud" in h:
        return "pocet_rud"
    if "nizsim stupni viceletych gymnazii" in h:
        return "gym_nizsi_stupen"
    if "pripravnem stupni zs specialni" in h:
        return "zs_specialni_pripravny_stupen"
    if "pripravne tride zs" in h:
        return "zs_pripravne_tridy"
    druh = "ms" if h.endswith(" ms") or h.endswith(" ms celkem") else "zs" if re.search(r"\bzs\b", h) else None
    if druh is None:
        return None
    if "celkem" in h:
        return f"{druh}_celkem"
    if "beznych tridach" in h:
        return f"{druh}_bezne_tridy"
    if "specialnich tridach" in h:
        return f"{druh}_specialni_tridy"
    return None


def je_kod_obce(x):
    try:
        return 500000 <= int(float(str(x).strip())) <= 999999
    except (TypeError, ValueError):
        return False


class StrukturaError(Exception):
    """Soubor MF má strukturu, kterou parser nezná (nový formát, přejmenované sloupce …)."""


def popis_struktury(cesta, radku=8):
    """Listy a začátek každého listu – do chybové zprávy, aby šlo parser rychle upravit."""
    try:
        xl = pd.ExcelFile(cesta, engine="openpyxl")
    except Exception as e:  # noqa: BLE001 – i nečitelný soubor chceme popsat
        return f"  soubor nejde otevřít: {e}"
    casti = [f"  {cesta.name}, listy: {xl.sheet_names}"]
    for list_ in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=list_, header=None, nrows=radku)
        casti.append(f"  --- list '{list_}' ({df.shape[1]} sloupců), prvních {radku} řádků:")
        for i, r in df.iterrows():
            bunky = [str(x).strip().replace("\n", " ") for x in r if pd.notna(x) and str(x).strip()]
            if bunky:
                casti.append(f"    {i}: " + " | ".join(bunky)[:400])
    return "\n".join(casti)


def nacti_soubor(cesta):
    """Vrátí (řádky obcí jako ve zdroji, řádky svazků obcí, řádek celkem ze zdroje nebo None)."""
    xl = pd.ExcelFile(cesta, engine="openpyxl")
    df = None
    for list_ in xl.sheet_names:
        d = pd.read_excel(xl, sheet_name=list_, header=None, dtype=object)
        if d.shape[0] > 100:
            df = d
            break
    if df is None:
        raise ValueError("žádný list s daty")

    radek = next(r for r in range(15) if klic(df.iat[r, 0]) in ("vusc", "nvusc") or klic(df.iat[r, 0]).startswith("kod nuts"))
    hlavicka = list(df.iloc[radek])
    prvni = [klic(x) for x in hlavicka[:5]]
    if not (("zriz" in prvni[1]) and ("stat" in prvni[3])):
        raise ValueError(f"neznámé popisné sloupce {prvni}")
    mapa = {}
    for i, h in enumerate(hlavicka[5:], start=5):
        if pd.isna(h) or not str(h).strip():
            continue
        jmeno = sloupec(h)
        if jmeno is None:
            raise ValueError(f"neznámý sloupec {i}: {h!r}")
        if jmeno in mapa.values():
            raise ValueError(f"sloupec {jmeno} je v hlavičce dvakrát ({h!r})")
        mapa[i] = jmeno
    for nutny in ("ms_celkem", "zs_celkem", "celkem"):
        if nutny not in mapa.values():
            raise ValueError(f"chybí sloupec {nutny}")

    data = df.iloc[radek + 1:]
    i_celkem = next(i for i, j in mapa.items() if j == "celkem")
    s_cislem = pd.to_numeric(data.iloc[:, i_celkem], errors="coerce").notna()
    obce = data[data.iloc[:, 1].map(je_kod_obce)]
    # dobrovolné svazky obcí (DSO): zřizovatel bez kódu obce („xxx“), ale s názvem a kódem kraje
    svazky = data[s_cislem & ~data.iloc[:, 1].map(je_kod_obce) & data.iloc[:, 2].notna()
                  & data.iloc[:, 0].astype(str).str.fullmatch(r"CZ0\d\d")]
    dso = pd.DataFrame({"kod_kraje": svazky.iloc[:, 0].astype(str).str.strip(),
                        "nazev_svazku": svazky.iloc[:, 2].astype(str).str.strip()})
    for i, jmeno in mapa.items():
        dso[jmeno] = pd.to_numeric(svazky.iloc[:, i], errors="coerce").fillna(0).astype(int)
    out = pd.DataFrame({
        "kod_kraje_zdroj": obce.iloc[:, 0].astype(str).str.strip(),
        "kod_zrizovatele": obce.iloc[:, 1].map(lambda x: int(float(x))),
        "nazev_zrizovatele": obce.iloc[:, 2].astype(str).str.strip(),
        "kod_statutarni": obce.iloc[:, 3].map(lambda x: int(float(x)) if je_kod_obce(x) else None),
        "nazev_statutarni": obce.iloc[:, 4].map(lambda x: str(x).strip() if pd.notna(x) else None),
    })
    for i, jmeno in mapa.items():
        hodnoty = pd.to_numeric(obce.iloc[:, i], errors="coerce")
        if hodnoty.isna().any():
            raise ValueError(f"sloupec {jmeno} má prázdné nebo nečíselné hodnoty u {int(hodnoty.isna().sum())} obcí")
        out[jmeno] = hodnoty.astype(int)

    # řádek celkem: za posledním řádkem obce nebo svazku, s číslem ve sloupci celkem
    konec = max(obce.index.max(), svazky.index.max() if len(svazky) else 0)
    soucty = data.loc[konec + 1:][s_cislem.loc[konec + 1:]]
    celkem = None
    if len(soucty):
        r = soucty.iloc[-1]
        celkem = {j: int(r.iloc[i]) for i, j in mapa.items()}
    return out, dso, celkem


def nacti_ciselnik():
    obce = pd.read_csv(CISELNIKY / "pscoco.csv")
    nuts = pd.read_csv(CISELNIKY / "cnumnuts.csv").set_index("NUMNUTS")
    obce = obce[obce.KRAJ.isin(nuts.index)]  # bez volebních okrsků v zahraničí
    obce = obce.drop_duplicates("OBEC_PREZ").copy()
    obce["kod_okresu"] = obce.OKRES.map(lambda k: "CZ0100" if k == 1100 else nuts.at[k, "NUTS"])
    obce["okres"] = obce.OKRES.map(lambda k: "Praha" if k == 1100 else nuts.at[k, "NAZEVNUTS"])
    obce["kod_kraje"] = obce.KRAJ.map(lambda k: nuts.at[k, "NUTS"])
    obce["kraj"] = obce.KRAJ.map(lambda k: nuts.at[k, "NAZEVNUTS"])
    kraje = nuts[nuts.NUTS.str.len() == 5].set_index("NUTS").NAZEVNUTS
    return obce.rename(columns={"OBEC_PREZ": "kod_obce"})[
        ["kod_obce", "kod_okresu", "okres", "kod_kraje", "kraj"]], kraje


def main():
    soubory = sorted(DATA.glob("????-09-30 Počty dětí a žáků.xlsx"))
    if not soubory:
        raise SystemExit("Ve složce data/ nejsou žádné tabulky, nejdřív spusť stahni_data.py")
    ciselnik, kraje = nacti_ciselnik()

    radky, svazky, kontrola, spatne_radky = [], [], [], []
    for cesta in soubory:
        rok = int(cesta.name[:4])
        try:
            zdroj, dso, celkem_zdroj = nacti_soubor(cesta)
        except Exception as e:
            raise StrukturaError(f"{rok}: nerozpoznaná struktura ({type(e).__name__}: {e})\n"
                                 f"{popis_struktury(cesta)}") from e
        sloupce = [c for c in POCTY if c in zdroj.columns]

        # kontrola řádků: mezisoučty a celkem jako součet složek
        for cil, slozky in [("celkem", SLOZKY_CELKEM), *MEZISOUCTY.items()]:
            slozky = [c for c in slozky if c in zdroj.columns]
            rozdil = zdroj[cil] - zdroj[slozky].sum(axis=1)
            for _, r in zdroj[rozdil != 0].iterrows():
                spatne_radky.append({"rok": rok, "kod_obce": r.kod_zrizovatele, "nazev": r.nazev_zrizovatele,
                                     "sloupec": cil, "hodnota": r[cil], "soucet_slozek": r[cil] - rozdil[_]})

        # městské části (2014–2015) na celé město
        zdroj["kod_obce"] = zdroj.kod_statutarni.fillna(zdroj.kod_zrizovatele).astype(int)
        zdroj["nazev_obce"] = zdroj.nazev_statutarni.where(zdroj.kod_statutarni.notna(), zdroj.nazev_zrizovatele)
        mc = int((zdroj.kod_obce != zdroj.kod_zrizovatele).sum())
        obce = zdroj.groupby("kod_obce", as_index=False).agg(
            nazev_obce=("nazev_obce", "first"), kod_kraje_zdroj=("kod_kraje_zdroj", "first"),
            **{c: (c, "sum") for c in sloupce})
        obce.insert(0, "rok", rok)
        obce.insert(1, "datum", f"{rok}-09-30")
        radky.append(obce)
        dso.insert(0, "rok", rok)
        dso.insert(1, "datum", f"{rok}-09-30")
        svazky.append(dso)

        k = {"rok": rok, "obci": len(obce), "radku_zdroje": len(zdroj), "mestskych_casti": mc, "svazku": len(dso)}
        for c in ("ms_celkem", "zs_celkem", "gym_nizsi_stupen", "celkem", "pocet_rud"):
            k[c] = int(obce[c].sum()) if c in obce else None
        k["celkem_svazky"] = int(dso.celkem.sum())
        k["celkem_zdroj"] = celkem_zdroj["celkem"] if celkem_zdroj else None
        k["rozdil"] = k["celkem"] + k["celkem_svazky"] - k["celkem_zdroj"] if celkem_zdroj else None
        # všechny sloupce (obce + svazky) proti řádku celkem, ne jen celkem
        k["sloupce_nesedi"] = ", ".join(
            c for c in sloupce if celkem_zdroj and int(obce[c].sum() + dso[c].sum()) != celkem_zdroj[c]) or ""
        k["radky_nesedi"] = sum(1 for s in spatne_radky if s["rok"] == rok)
        kontrola.append(k)
        print(f"{rok}: {len(zdroj)} řádků zdroje -> {len(obce)} obcí, celkem {k['celkem']:,}".replace(",", " ")
              + (f", řádek celkem ve zdroji {k['celkem_zdroj']:,}".replace(",", " ") if celkem_zdroj else ", bez řádku celkem"))

    vysledek = pd.concat(radky, ignore_index=True)
    # nejnovější název obce pro všechny roky (názvy se mezi roky občas liší zápisem)
    vysledek["nazev_obce"] = vysledek.groupby("kod_obce").nazev_obce.transform("last")
    vysledek = vysledek.merge(ciselnik, on="kod_obce", how="left")
    # obce, které už v aktuálním číselníku nejsou: kraj aspoň ze zdroje
    chybi = vysledek.kod_kraje.isna()
    vysledek.loc[chybi, "kod_kraje"] = vysledek.kod_kraje_zdroj[chybi]
    vysledek.loc[chybi, "kraj"] = vysledek.kod_kraje_zdroj[chybi].map(kraje)
    if chybi.any():
        print("bez okresu (nejsou v aktuálním číselníku obcí): "
              + ", ".join(sorted({f"{r.nazev_obce} ({r.kod_obce})" for r in vysledek[chybi].itertuples()})))
    jiny_kraj = vysledek[~chybi & (vysledek.kod_kraje != vysledek.kod_kraje_zdroj)]
    if len(jiny_kraj):
        print("pozor, kraj ve zdroji jiný než v číselníku: "
              + ", ".join(sorted({f"{r.nazev_obce} {r.rok}" for r in jiny_kraj.itertuples()})))

    vysledek[POCTY] = vysledek.reindex(columns=POCTY).astype("Int64")
    poradi = ["rok", "datum", "kod_obce", "nazev_obce", "kod_okresu", "okres", "kod_kraje", "kraj", *POCTY]
    vysledek = vysledek[poradi].sort_values(["rok", "kod_obce"])

    # částka na žáka (rozpočtový rok R počítá s žáky k 30. 9. roku R−1) a odhad prostředků obce
    import castky
    castka = castky.main(vysledek)
    na_zaka = {}
    if not castka.empty:
        obce_zak = castka[castka.prijemce.eq("obce") & castka.jednotka.eq("žák")]
        na_zaka = dict(zip(obce_zak.stav_zaku_k.str[:4].astype(int), obce_zak.castka_na_zaka_kc))
    vysledek["rok_rozpoctu"] = vysledek.rok + 1
    vysledek["odhad_prostredku_kc"] = (castky.pocet_pro_rud(vysledek)
                                       * vysledek.rok.map(na_zaka).astype("Int64")).astype("Int64")

    VYSTUP.mkdir(exist_ok=True)
    vysledek.to_csv(VYSTUP / "zaci_obce.csv", index=False, encoding="utf-8-sig")
    vysledek.to_excel(VYSTUP / "zaci_obce.xlsx", index=False, freeze_panes=(1, 0))
    svazky = pd.concat(svazky, ignore_index=True)
    svazky["kraj"] = svazky.kod_kraje.map(kraje)
    svazky = svazky[["rok", "datum", "nazev_svazku", "kod_kraje", "kraj",
                     *[c for c in POCTY if c in svazky.columns]]]
    svazky[POCTY] = svazky.reindex(columns=POCTY).astype("Int64")
    svazky.to_csv(VYSTUP / "zaci_svazky_obci.csv", index=False, encoding="utf-8-sig")
    kontrola = pd.DataFrame(kontrola)
    kontrola["zmena_celkem"] = kontrola.celkem.pct_change().round(4)
    kontrola = kontrola.astype({c: "Int64" for c in ("pocet_rud", "celkem_zdroj", "rozdil")})
    kontrola.to_csv(
        VYSTUP / "kontrola_souctu.csv", index=False, encoding="utf-8-sig")
    if spatne_radky:
        pd.DataFrame(spatne_radky).to_csv(VYSTUP / "kontrola_radku.csv", index=False, encoding="utf-8-sig")
    else:
        (VYSTUP / "kontrola_radku.csv").unlink(missing_ok=True)

    print(kontrola.to_string(index=False))
    print(f"Hotovo: {len(vysledek)} řádků -> {VYSTUP / 'zaci_obce.csv'}")

    import kontrola as kontrola_html
    kontrola_html.main()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except StrukturaError as e:
        VYSTUP.mkdir(exist_ok=True)
        (VYSTUP / "chyba_struktury.txt").write_text(str(e), encoding="utf-8")
        print(e, file=sys.stderr)
        sys.exit(1)
