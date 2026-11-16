# Děti a žáci ve školách zřizovaných obcemi

Počty dětí v mateřských školách a žáků v základních školách (a v nižším stupni víceletých
gymnázií), které zřizují obce, po obcích za roky 2014–2024, vždy ke stavu k 30. září.
Zdrojem jsou tabulky Ministerstva financí ČR, podle kterých se obcím rozděluje část sdílených
daní (kritérium „počet dětí a žáků navštěvujících školu zřizovanou obcí“ v zákoně
č. 243/2000 Sb., o rozpočtovém určení daní). Data do tabulek dodává MŠMT ze školních výkazů.
K tomu je tu částka, kterou obce za jedno dítě nebo žáka dostávají ze sdílených daní
(rozpočtové roky 2013–2026), a odhad těchto prostředků pro každou obec.

- **Web s daty ke stažení:** https://opendatabrno.github.io/zaci/
- **Zdroj MF:** [Financování mateřských a základních škol](https://mf.gov.cz/cs/rozpoctova-politika/uzemni-rozpocty/hospodareni-uzemnich-rozpoctu/financovani-materskych-a-zakladnich-skol/2026)
  (stránky po letech, tabulka se stavem k 30. 9. roku R je na stránce roku R+1)
- Sesterské sady: [obyvatelé obcí](https://github.com/opendatabrno/obyvatele) ·
  [cizinci](https://github.com/opendatabrno/cizinci)

**Obsah:** [Datové sady](#datové-sady) · [Sloupce](#sloupce) · [Částka na žáka](#částka-na-žáka) · [Na co si dát pozor](#na-co-si-dát-pozor) ·
[Aktualizace dat](#aktualizace-dat) · [Kontroly](#kontroly) · [Soubory v repozitáři](#soubory-v-repozitáři) ·
[Jak se data zpracovávají](#jak-se-data-zpracovávají)

---

## Datové sady

| Soubor | Co obsahuje | Jeden řádek | Klíč |
|---|---|---|---|
| [`vystup/zaci_obce.csv`](vystup/zaci_obce.csv) | obce, které zřizují aspoň jednu MŠ nebo ZŠ (~3 350–3 430 ročně) | obec × rok | `rok` + `kod_obce` |
| [`vystup/zaci_svazky_obci.csv`](vystup/zaci_svazky_obci.csv) | školy zřizované dobrovolnými svazky obcí (0–10 svazků ročně) | svazek × rok | `rok` + `nazev_svazku` |
| [`vystup/castka_na_zaka.csv`](vystup/castka_na_zaka.csv) | kolik obce dostávají ze sdílených daní na jedno dítě nebo žáka, rozpočtové roky 2013–2026 | rok × příjemce | `rok` + `prijemce` |

- Formát: CSV, UTF-8 (s BOM, aby se správně otevřelo v Excelu), oddělovač čárka. Na
  [webu](https://opendatabrno.github.io/zaci/) jsou všechny sady ke stažení i jako Excel (`.xlsx`),
  lokálně vzniká `vystup/zaci_obce.xlsx` při zpracování.
- `kod_obce` je šestimístný kód obce ČSÚ, takže sadu jde spojit s
  [obyvateli obcí](https://github.com/opendatabrno/obyvatele) přes `kod_obce` (a rok – viz níže).
  Všechny obce z této sady v `obyvatele` jsou.
- **Obec, která v tabulce v daném roce není, nezřizuje žádnou MŠ ani ZŠ** (počet je 0).
  Děti z ní chodí do škol jiných obcí, svazků, krajů, církví nebo soukromých zřizovatelů.
- **Součet za ČR = `zaci_obce` + `zaci_svazky_obci`.** Tak se rovná řádku „celkem“ ve zdroji.

### Kolik dětí a žáků (celá ČR, obce + svazky)

| Stav k 30. 9. | MŠ celkem | ZŠ celkem | celkem | z toho svazky obcí |
|---|---:|---:|---:|---:|
| 2014 | 352 519 | 817 276 | 1 182 334 | 1 495 |
| 2015 | 351 047 | 842 221 | 1 207 320 | 1 473 |
| 2016 | 346 218 | 866 768 | 1 227 242 | – (ve zdroji chybí) |
| 2017 | 345 437 | 885 178 | 1 246 291 | 1 257 |
| 2018 | 346 026 | 896 988 | 1 259 532 | 1 703 |
| 2019 | 346 683 | 906 335 | 1 271 425 | 1 767 |
| 2020 | 339 360 | 913 792 | 1 271 824 | 1 795 |
| 2021 | 341 221 | 913 132 | 1 274 985 | 1 881 |
| 2022 | 348 933 | 952 059 | 1 323 027 | 2 163 |
| 2023 | 343 933 | 942 056 | 1 306 631 | – (ve zdroji chybí) |
| 2024 | 339 345 | 941 159 | 1 306 019 | 2 444 |

MŠ a ZŠ celkem jsou jen za obce (bez svazků). Celkem zahrnuje i přípravné třídy,
§ 38, § 41 a gymnázia, proto je vyšší než součet MŠ a ZŠ.

## Sloupce

| Sloupec | Význam | Roky |
|---|---|---|
| `rok` | rok stavu (data k 30. 9. tohoto roku) | vše |
| `datum` | datum stavu, `RRRR-09-30` | vše |
| `kod_obce`, `nazev_obce` | kód ČSÚ a název obce, která školy zřizuje (název podle posledního roku) | vše |
| `kod_okresu`, `okres`, `kod_kraje`, `kraj` | okres a kraj podle aktuálního číselníku obcí (volby.gov.cz) | vše |
| `ms_bezne_tridy` | děti v běžných třídách MŠ | vše |
| `ms_specialni_tridy` | děti ve speciálních třídách MŠ (§ 16 odst. 9 školského zákona) | vše |
| `ms_celkem` | děti v MŠ celkem | vše |
| `ms_individualni_34b` | děti s individuálním předškolním vzděláváním (§ 34b) | od 2024 |
| `zs_specialni_pripravny_stupen` | děti v přípravném stupni ZŠ speciální | vše |
| `zs_pripravne_tridy` | děti v přípravných třídách ZŠ | vše |
| `zs_bezne_tridy` | žáci v běžných třídách ZŠ | vše |
| `zs_specialni_tridy` | žáci ve speciálních třídách ZŠ | vše |
| `zs_celkem` | žáci v ZŠ celkem | vše |
| `zs_zahranici_38` | žáci ZŠ vzdělávající se v zahraničí nebo v zahraniční škole (§ 38) | vše |
| `zs_individualni_41` | žáci ZŠ v individuálním (domácím) vzdělávání (§ 41) | vše |
| `zs_hluboke_postizeni_42` | žáci s hlubokým mentálním postižením (§ 42) | 2014–2018 |
| `gym_nizsi_stupen` | žáci nižšího stupně víceletých gymnázií zřizovaných obcí | vše |
| `gym_zahranici_38` | žáci nižšího stupně víceletých gymnázií podle § 38 | vše |
| `celkem` | děti a žáci celkem (sloupec zdroje) | vše |
| `pocet_rud` | počet pro účely rozpočtového určení daní (bez § 38) | od 2023 |
| `rok_rozpoctu` | rozpočtový rok, ve kterém obec za tyto děti a žáky dostává peníze (`rok + 1`) | vše |
| `odhad_prostredku_kc` | odhad, kolik obec v roce `rok_rozpoctu` dostala ze sdílených daní za děti a žáky: počet pro RUD × částka na žáka (viz [Částka na žáka](#částka-na-žáka)); prázdné, dokud MF částku nezveřejní | vše |

Prázdná hodnota = sloupec v tom roce ve zdroji není (není to nula).
Tabulka svazků má místo obce `nazev_svazku` a `kod_kraje`, `kraj`, sloupce s počty jsou stejné.

**Jak se sloupce sčítají** (ověřeno u každého řádku):

```
ms_celkem = ms_bezne_tridy + ms_specialni_tridy
zs_celkem = zs_bezne_tridy + zs_specialni_tridy
celkem    = ms_celkem + ms_individualni_34b + zs_specialni_pripravny_stupen + zs_pripravne_tridy
          + zs_celkem + zs_zahranici_38 + zs_individualni_41 + zs_hluboke_postizeni_42
          + gym_nizsi_stupen + gym_zahranici_38
```

## Částka na žáka

Od roku 2013 nedostávají obce na školy zvláštní příspěvek. Část sdílených daní (DPH a daně
z příjmů) se mezi ně dělí podle počtu dětí a žáků ve školách, které zřizují: 7 % do roku 2017,
**9 % od roku 2018**. MF každý rok zveřejňuje, kolik to vyšlo na jedno dítě nebo žáka.
Peníze nejsou účelové, obec s nimi naloží, jak chce. Částka pro rozpočtový rok R se počítá
z počtu dětí a žáků k 30. 9. roku R−1.

| Rozpočtový rok | Kč na žáka | Změna | Žáci k 30. 9. | Odhad objemu za ČR |
|---|---:|---:|---|---:|
| 2013 | 7 780 | | 2012 | |
| 2014 | 8 020 | +3,1 % | 2013 | |
| 2015 | 8 246 | +2,8 % | 2014 | 9,7 mld. Kč |
| 2016 | 8 806 | +6,8 % | 2015 | 10,6 mld. Kč |
| 2017 | 9 506 | +7,9 % | 2016 | 11,6 mld. Kč |
| 2018 | 13 706 | +44,2 % | 2017 | 16,9 mld. Kč |
| 2019 | 14 462 | +5,5 % | 2018 | 18,1 mld. Kč |
| 2020 | 13 626 | −5,8 % | 2019 | 17,2 mld. Kč |
| 2021 | 15 309 | +12,4 % | 2020 | 19,3 mld. Kč |
| 2022 | 17 665 | +15,4 % | 2021 | 22,3 mld. Kč |
| 2023 | 19 644 | +11,2 % | 2022 | 25,8 mld. Kč |
| 2024 | 19 716 | +0,4 % | 2023 | 25,6 mld. Kč |
| 2025 | 20 845 | +5,7 % | 2024 | 26,9 mld. Kč |
| 2026 | 36 786 obce / 18 179 kraje | – | 2025 | předběžné, na přepočteného žáka |

Sloupce `castka_na_zaka.csv`:

| Sloupec | Význam |
|---|---|
| `rok` | rozpočtový rok |
| `prijemce` | `obce`; od 2026 i `kraje` |
| `castka_na_zaka_kc` | částka v Kč na jedno dítě nebo žáka (MF ji uvádí v tis. Kč na tři desetinná místa) |
| `jednotka` | `žák`; od 2026 `přepočtený žák` |
| `stav_zaku_k` | ke kterému dni se počítají děti a žáci |
| `udaj` | `skutečnost` (z daní skutečně převedených obcím za rok) nebo `předběžný` (z predikce daní) |
| `zdroj` | stránka MF |
| `zmena_proti_minulemu_roku` | meziroční změna částky (jen obce, jednotka žák) |
| `pocet_zaku_rud_cr` | počet dětí a žáků pro RUD za všechny obce z této sady |
| `objem_kc_odhad` | `pocet_zaku_rud_cr` × `castka_na_zaka_kc`, tedy kolik obce za děti a žáky dostaly celkem |

**Na co si dát pozor u částek:**
- **2018 +44 %:** váha kritéria se zvýšila ze 7 na 9 % a zároveň rostly daně. Jinak částka
  sleduje výnos daní (pokles 2020 kvůli covidu, růst 2021–2023 s inflací).
- **2026 není srovnatelné:** od roku 2026 přešlo do RUD i financování nepedagogických
  pracovníků a kritérium je „děti, žáci a studenti ve školách“ i pro kraje. Částka je na
  *přepočteného* žáka (počet podle vyhlášky, ne skutečný počet žáků) a zatím jen předběžná.
  `odhad_prostredku_kc` se pro žáky k 30. 9. 2025 proto zatím nepočítá.
- **`odhad_prostredku_kc` je odhad.** Do roku 2022 není ve zdroji počet pro RUD, bere se
  `celkem` bez žáků podle § 38 (a od 2024 bez § 34b). Obec dostává peníze podle počtů
  ve vyhlášce MF, které se po opravách obcí mohou od tabulky lišit. Svazky obcí peníze
  nedostávají, ty jdou členským obcím podle vyhlášky.
- MF stránky s částkami průběžně aktualizuje (předběžný údaj → skutečnost). `stahni_data.py`
  proto stránky posledních dvou let stahuje vždy znovu.

## Na co si dát pozor

- **Počty jsou podle zřizovatele, ne podle bydliště dětí ani polohy školy.** Obec se
  spádovou školou má mnohem víc žáků, než kolik dětí v ní bydlí; obec bez školy tu není vůbec.
  Pro podíl „žáků na obyvatele“ proto počítej spíš za okresy nebo ORP než za malé obce.
- **Jen školy zřizované obcemi a jejich svazky.** Školy krajů (hlavně speciální ZŠ a MŠ),
  církevní, soukromé a státní tu nejsou.
- **Rok a spojení s obyvateli:** `rok` je rok stavu k 30. 9. Počet obyvatel MV je k 1. 1.,
  nejbližší je tedy stav k 1. 1. následujícího roku (`obyvatele.rok = zaci.rok + 1`).
- **Svazky obcí ve zdroji chybí v letech 2016 a 2023** (podle okolních let 2016 asi 1,2–1,5 tis.,
  2023 asi 2,2–2,4 tis. dětí). Celkem za ČR je v těchto letech o tolik nižší. V jiných letech
  jsou svazky v samostatné tabulce, protože je nejde přiřadit jedné obci.
- **Převod školy na svazek obcí** se projeví poklesem u obce: např. Ondřejov (Praha-východ)
  od 2018 (Svazková škola Ondřejov) a Tursko (Praha-západ) od 2022 (ZŠ Tursko-Holubice).
- **Městské části 2014–2015:** zdroj má Prahu, Brno, Ostravu a Liberec rozepsané po
  městských částech (zřizovatelem škol jsou MČ). Ty jsou tu sečtené na celé město, od 2016 je
  zdroj má vcelku. Po MČ data za další roky nejsou.
- **Zlom 2022:** +48 tis. dětí a žáků (+3,8 %) – děti z Ukrajiny s dočasnou ochranou.
- **Zlom 2024:** nový sloupec `ms_individualni_34b` (2,3 tis. dětí), MF ho započítává
  i do `celkem`. Pro srovnání se staršími roky ho odečti.
- **§ 42** (žáci s hlubokým mentálním postižením, 20–32 ročně) je ve zdroji jen do 2018,
  pak se tito žáci vykazují v ZŠ speciální.
- **`pocet_rud`** (od 2023) je počet, podle kterého se obci skutečně rozdělují daně;
  nezahrnuje žáky podle § 38.
- **Od roku 2026 se kritérium v zákoně mění** na „počet dětí, žáků a studentů ve školách“
  (i pro kraje, včetně středních škol). Tabulka se stavem k 30. 9. 2025 zatím nevyšla
  a nejspíš bude mít jinou strukturu – viz [Aktualizace dat](#aktualizace-dat).
- Okres a kraj jsou podle aktuálního číselníku obcí, i pro starší roky.

---

## Aktualizace dat

### Automaticky (GitHub Actions)

Workflow [**Aktualizace dat MF**](.github/workflows/aktualizace.yml) hlídá stránky MF:
od ledna do června každé pondělí, zbytek roku 1. den v měsíci. Spustit se dá i ručně
(*Actions → Aktualizace dat MF → Run workflow*).

| Co se stane | Co udělá workflow | Co uděláš ty |
|---|---|---|
| Nic nového | nic | nic |
| MF zveřejnilo novou tabulku | založí **pull request** `aktualizace-dat` se souhrnem kontrol | projdi souhrn a přehled kontrol (artefakt `kontrola` u běhu) a PR slouč |
| Data se načetla, ale kontrola nesedí | PR s názvem začínajícím **„⚠️ Kontrola nesedí“** | zjisti příčinu v přehledu kontrol, PR neslučuj bez opravy |
| MF změnilo strukturu tabulky | založí **issue** `zmena-struktury` s ukázkou souboru | upravit `zpracuj_data.py` (funkce `sloupec()` a `nacti_soubor()`) podle ukázky v issue |

Po sloučení PR workflow [**GitHub Pages**](.github/workflows/pages.yml) automaticky
aktualizuje web.

**Jednorázové nastavení na GitHubu:**
1. *Settings → Pages → Source:* **GitHub Actions**
2. *Settings → Actions → General → Workflow permissions:* **Read and write permissions**
   a zaškrtnout **Allow GitHub Actions to create and approve pull requests**

> GitHub vypíná plánované workflows po 60 dnech bez aktivity v repozitáři (pošle e-mail).
> Před lednem zkontroluj v záložce *Actions*, že workflow je zapnuté.

### Ručně

```bash
pip install -r requirements.txt   # jen poprvé
python stahni_data.py             # stáhne chybějící tabulky MF do data/
python zpracuj_data.py            # zpracuje vše do vystup/ a vytvoří přehled kontrol
python web.py                     # volitelně: web do _site/
```

Nové tabulky hledá `stahni_data.py` na stránkách MF sám (článek „Počty dětí a žáků …“
s přílohou xlsx, článek „Informace o výši prostředků …“ s částkou na žáka). Tabulku jde stáhnout i ručně a uložit jako `data/RRRR-09-30 Počty dětí a žáků.xlsx`.

## Kontroly

Po zpracování vznikne **`vystup/kontrola.html`** (online na [webu](https://opendatabrno.github.io/zaci/kontrola.html))
a kontrolní CSV. Semafory: zelená = v pořádku, modrá = známý rozdíl, oranžová = ověřit ručně, červená = nesedí.

| Kontrola | Co hlídá | Podklad |
|---|---|---|
| Součty proti zdroji | součet obcí + svazků v každém sloupci = řádek celkem ve zdroji (chyba, když nesedí); zdroj 2015–2018 řádek celkem nemá | `vystup/kontrola_souctu.csv` |
| Součty v řádcích | mezisoučty MŠ, ZŠ a `celkem` = součet složek (varování) | `vystup/kontrola_radku.csv` (jen když něco nesedí) |
| Meziroční změna za ČR | změna `celkem` nad 5 % mimo známé zlomy (varování) | `vystup/kontrola_souctu.csv` |
| Částka na žáka | přehled částek po letech; souhrn upozorní, když k některému roku žáků částka chybí | `vystup/castka_na_zaka.csv` |
| Skoky obcí | obce se změnou aspoň o 100 dětí a 30 % proti předchozímu roku – k ručnímu projití | `vystup/kontrola_skoky.csv` |

Aktuální stav: všechny roky se zdrojem sedí, v řádcích nesedí nic. Skoků obcí je 11,
jde o rostoucí obce u Prahy (Chýně, Sulice), Březovou (Uherské Hradiště), převody škol
na svazky (Ondřejov, Tursko) a podobně.

---

## Soubory v repozitáři

| Soubor | Účel |
|---|---|
| `stahni_data.py` | stažení tabulek MF (známé odkazy + hledání nových), článků s částkou na žáka a číselníků obcí |
| `zpracuj_data.py` | zpracování do tabulky obcí a svazků, spouští i kontroly |
| `castky.py` | částka na žáka z článků MF „Informace o výši prostředků …“ |
| `web.py` | sestavení webu pro GitHub Pages do `_site/` (úvodní stránka, grafy, CSV a xlsx ke stažení) |
| `kontrola.py` | přehled kontrol `vystup/kontrola.html` a souhrn pro PR |
| `ciselniky/pscoco.csv`, `ciselniky/cnumnuts.csv` | číselník obcí, okresů a krajů (volby.gov.cz) |
| `.github/workflows/aktualizace.yml` | automatická aktualizace |
| `.github/workflows/pages.yml` | publikace webu na GitHub Pages |

## Jak se data zpracovávají

1. V každé tabulce se najde řádek hlavičky (první buňka `VUSC`, `NVUSC` nebo „Kód NUTS 3“).
   Prvních pět sloupců je vždy kraj (NUTS 3), kód a název obce zřizovatele, kód a název
   statutárního města. Sloupce s počty se přiřadí podle klíčových slov v hlavičce; neznámý
   sloupec zastaví zpracování (→ issue), aby se nová data nenačetla špatně.
2. Řádky s kódem obce jsou obce. Řádky s kódem `xxx` a názvem „DSO …“ jsou svazky obcí.
   Poslední řádek s čísly bez kódu je řádek celkem ze zdroje.
3. Kde je vyplněné statutární město (2014–2015 u MČ), řádek se přičte k celému městu.
4. Okres a kraj se doplní z číselníku obcí podle `kod_obce`.
5. Z článků MF „Informace o výši prostředků, které obce získávají z RUD …“ se vytáhnou věty
   „… pro rok R v částce X tis. Kč na žáka“ (i se stavem žáků a tím, zda jde o skutečnost,
   nebo předběžný údaj). Když je stejný rok na více stránkách, přednost má skutečnost.
