# COMtext.SR pseudonimizator

COMtext.SR pseudonimizator je programska biblioteka za pseudonimizaciju poverljivih podatka, tj. njihovu zamenu izmišljenim podacima istog tipa, u pravno-administrativnim tekstovima na srpskom jeziku. Ova biblioteka je razvijena u okviru projekta [COMtext.SR](https://github.com/ICEF-NLP/COMtext.SR).

COMtext.SR pseudonimizator je u stanju da izvrši pseudonimizaciju sledećih tipova poverljivih podataka:
- Imena i prezimena osoba
- Adresa i toponima
- Naziva kompanija i nevladinih organizacija
- Identifikatora fizičkih lica (JMBG, broj lične karte/pasoša) i pravnih lica (PIB, matični broj)
- Brojeva registarskih tablica
- Brojeva parcela
- Novčanih iznosa 
- Brojeva računa u banci
- Kontakt informacija - brojeva telefona, URLova i email adresa
- Datuma

Za izvršavanje biblioteke neophodno je korišćenje Python verzije 3.11. ili novije.
 
## Ulazni podaci
Rad pseudonimizatora se zasniva na pravilno obeleženim imenovanim entitetima za svaki od tipova poverljivih informacija koje treba pseudonimizovati. COMtext.SR pseudonimizator se stoga oslanja na prethodno korišćenje modela za prepoznavanje imenovanih entiteta u pravno-administrativnim tekstovima koji su izrađeni u okviru COMtext.SR projekta.

Priprema dokumenta za pseudonimizaciju podrazumeva da se sirov tekstualni sadržaj dokumenta prethodno tokenizuje i propusti kroz COMtext.SR.legal modele za morfosintaktičko obeležavanje reči, lematizaciju i prepoznavanje imenovanih entiteta radi dobijanja potrebnih oznaka. Alternativno, moguće je za te potrebe adaptirati neke druge modele istog tipa za obradu tekstova na srpskom, tako da njihov izlaz odgovara oznakama koje koriste COMtext.SR modeli.

Biblioteka očekuje da ulazni podaci budu formatirani u .conllu formatu, sa sledećim kolonama:
1. Redni broj tokena
2. Token
3. Lema
4. Morfosintaktički tag (po [MULTEXT-East v6](http://nl.ijs.si/ME/V6/) standardu)
5. Imenovani entiteti (prema šemi entiteta iz COMtext.SR projekta, obeleženi po IOB2 standardu)

Ukoliko ulazni .conllu fajl sadrži više dokumenata, početak svakog dokumenta bi trebalo da bude naznačen pomoću:
```
# newdoc id = DOC123
```
gde je **DOC123** proizvoljan identifikator posmatranog dokumenta.

## Način rada
COMtext.SR pseudonimizator se u radu oslanja na [srLex](http://hdl.handle.net/11356/1233), najveći javno dostupni flektivni leksikon srpskog jezika. To mu omogućava da izvrši zamenu imena i prezimena osoba i adresa u adekvatnom padežnom obliku u kome se originalni entitet nalazio. 

Identifikatori fizičkih i pravnih lica (JMBG, broj lične karte/pasoša, PIB, matični broj) se zamenjuju vodeći računa o zadržavanju validnog formata navedenih identifikatora. Isto važi i za brojeve registarskih tablica, parcela, računa u banci. Pritom, zamene identifikatora fizičkih i pravnih lica se uvek generišu sa pogrešnom kontrolnom cifrom, tako da se izbegne preklapanje sa nekim drugim realno postojećim vrednostima identifikatora.

COMtext.SR pseudonimizator koristi vreme pokretanja i ID ulaznog dokumenta kao *seed* vrednosti za interni generator slučajnih brojeva. To omogućava da zamene budu slučajne, tj. da se razlikuju između dva pokretanja pseudonimizatora nad istim ulaznim podacima, a da istovremeno budu konzistentne, tako da se u okviru istog dokumenta jedan isti ulazni entitet uvek zamenjuje fiksnim zamenskim entitetom.

## Ograničenja
* **Prisvojni pridevi:** Zbog izuzetno ograničene pokrivenosti prisvojnih prideva izvedenih iz ličnih imena u srLex leksikonu, COMtext.SR pseudonimizator trenutno nije u stanju da izvrši zamenu takvih oblika imenovanih entiteta. 
* **Toponimi:** Pseudonimizator je trenutno ograničen u zameni toponima na nazive 145 gradova i opština u Republici Srbiji. Pored toga, biblioteka trenutno ne vrši zamenu toponima koji se javljaju u okviru naziva institucija tj. u okviru imenovanih entiteta tog tipa, dok se za toponime u okviru zvaničnih naziva sudova vrši zamena.
* **Kompanije:** Zamena imena realnih kompanija i nevladinih organizacija je trenutno ograničena na njihov oblik u nominativu.
* **Pravna dokumenta:** Pseduonimizacija poverljivih informacija sadržanih u okviru pominjanja pravnih dokumenata, poput opštih i pojedinačnih pravnih akata, trenutno nije podržana.
 
## Instalacija i pokretanje
COMtext.SR pseudonimizator je dostupan u vidu PyPI paketa koji se može instalirati sledećom komandom:
 ```
pip install comtext-sr-pseudonymizer
```

### Pokretanje
Biblioteka se može pokrenuti direktno iz komandne linije komandom: `comtext-sr-pseudonymizer`
#### Argumenti 

| Argument | Skraćenica | Opis |
| :--- | :--- | :--- |
|  &#45;&#45;input | `-i` | **Obavezno.** Putanja do `.conllu` fajla koji se pseudonimizuje. |
| &#45;&#45;output | `-o` | Direktorijum za čuvanje rezultata (default: `results`). |
| &#45;&#45;types | `-t` | Opciona lista entiteta (npr. `PER ADR DATE`). Ako se izostavi, svi podržani tipovi se pseudonimizuju. |
#### Primer upotrebe
```bash
comtext-sr-pseudonymizer --input ./data/my_text.conllu --output ./my_results --types PER TOP ADR
```

### Izlazni podaci
Biblioteka generiše dva izlazna fajla prilikom svakog izvršavanja. Prvi fajl sadrži pseudonimizovane podatke, dok drugi sadrži spisak izvršenih zamena.

#### 1. Pseudonimizovani tekst - **File:** `[TIMESTAMP].conllu`
Ovo je glavni izlazni fajl. On zadržava strukturu ulaznog fajla, ali zamenjuje poverljive informacije pseudonimizovanim vrednostima.

* **Format**: Tabulatorom razdvojen format sa 3 kolone (Redni broj tokena u rečenici, pseudonimizovan token, NER tag po IOB2 formatu).
* **Metapodaci**: Svi originalni metapodaci (npr. # sent_id, # text) su sačuvani i modifikovani shodno unetim zamenskim vrednostima.
* **Logika**: Transformišu se samo tokeni koji pripadaju nekom imenovanom entitetu (B-X, I-X); tokeni sa oznakom "O" ostaju nepromenjeni.

Primer izlaznog formata:
```text
# sent_id = vA001-s1
# text = DUTAN S DOO ul. Božidara Korkocića 82 15300 Loznica
1	DUTAN	B-COM
2	S	I-COM
3	DOO	I-COM
4	ul.	B-ADR
5	Božidara	I-ADR
6	Korkocića	I-ADR
7	82	I-ADR
8	15300	I-ADR
9	Loznica	I-ADR
```

#### 2. Spisak izvršenih zamena - **File:** `[TIMESTAMP]_replacements.tsv`
Ovaj fajl služi kao izveštaj o mapiranju, omogućavajući direktno poređenje originalnih podataka sa generisanim zamenama.

Struktura fajla:
| Kolona | Opis |
| :--- | :--- |
| `doc_id` | Jedinstveni identifikator izvornog dokumenta (npr, `vA001`). |
| `sentence_id` | Identifikator konkretne rečenice (npr. `vA001-s1`). |
| `start_token_num` | Indeks prvog tokena u entitetu. |
| `end_token_num` | Indeks poslednjeg tokena u entitetu. |
| `original_text` | Izvorni tekst entiteta (može se sastojati od više reči). |
| `entity_group` | Kategorija imenovanih entiteta prema COMtext.SR šemi (npr. `COM`, `ADR`, `DATE`). |
| `anonymized_text` | Zamena koju je generisala biblioteka. |

Primer formata:
```text
doc_id	sentence_id	start_token_num	end_token_num	original_text	entity_group	anonymized_text
vA001	vA001-s1	1	4	Trans Impex Trade d.o.o.	COM	DUTAN S DOO
vA001	vA001-s1	5	11	Bul. Vojvode Stepe 123/2 21000 Novi Sad	ADR	ul. Božidara Korkocića 82 15300 Loznica
vA001	vA001-s12	2	3	Novom Sadu	TOP	Loznici
vA001	vA001-s12	5	9	dana 1. 2. 2011. godine	DATE	dana 20. 03. 2007. godine
vA001	vA001-s3	12	18	Trans Impex Trade d.o.o. iz Novog Sada	COM	DUTAN S DOO
vA001	vA001-s3	21	22	Petar Petrović	PER	Nemanja Kolarski
vA001	vA001-s3	24	25	Novog Sada	TOP	Loznice
```

## Autorstvo
COMtext.SR pseudonimizator je izrađen od strane članova Grupe za obradu prirodnih jezika u okviru [Inovacionog centra Elektrotehničkog fakulteta u Beogradu (ICEF)](https://www.ic.etf.bg.ac.rs/):
- [Aleksandra Todorović](mailto:aleksandra.todorovic@ic.etf.bg.ac.rs)
- [dr Vuk Batanović](mailto:vuk.batanovic@ic.etf.bg.ac.rs)

## Licenca
COMtext.SR pseudonimizator je dostupan pod licencom Apache 2.0, što znači da se može slobodno koristiti za bilo koje svrhe, uključujući i komercijalne, uz navođenje informacija o autorstvu.

## Zahvalnost
Izrada COMtext.SR pseudonimizatora je omogućena zahvaljujući podršci [Fondacije Registar nacionalnog internet domena Srbije - RNIDS](http://www.rnids.rs/). 
