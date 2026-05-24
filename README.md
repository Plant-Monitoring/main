## 🔧 Razvojna veja (develop)

### 📌 Pregled veje

Veja `develop` predstavlja primarno razvojno in integracijsko okolje projekta.  
V tej veji se združujejo in validirajo vse nove funkcionalnosti pred vključitvijo v stabilno produkcijsko vejo (`main`).

Gre za centralno integracijsko plast sistema, kjer se preverja skladnost, stabilnost in medsebojno delovanje vseh modulov.

<<<<<<< Updated upstream
### 🎯 Namen

Glavni cilj veje `develop` je:

- zagotoviti stabilno integracijo funkcionalnosti iz `feature/*` vej
- omogočiti sistemsko testiranje celotne aplikacije
- identificirati in odpraviti napake pred izdajo stabilne verzije
- pripraviti preverjeno kodo za prehod v produkcijsko vejo (`main`)

Veja deluje kot kontrolna točka pred produkcijsko izdajo.

### 🏗️ Vsebina veje
=======
### 🔐 Avtentikacija uporabnikov
- Prijava in registracija uporabnikov
- Podpora več uporabnikom (Anastasija, David, Damjan)
- Upravljanje uporabniških računov

### 📊 Nadzorna plošča (Dashboard)
- Prikaz trenutne svetlobne intenzitete za zadnjih 24 ur
- Grafični prikaz meritev z označenimi pragovi (nizka: 300 lux, optimalna: 800 lux)
- Izračun in prikaz povprečne, minimalne in maksimalne vrednosti
- Uvoz podatkov iz CSV datoteke prek gumba 📂 Add File
- Osvežitev podatkov prek gumba Refresh Data

### ⚠️ Opozorila (Alerts)
- Seznam zaznanih svetlobnih odstopanj razvrščenih po času
- Filtriranje opozoril po kategorijah:
  - Kritično (Low Light)
  - Opozorilo (High Light Level)
  - Informativno (Optimal Range)

### 🌿 Moje rastline (My Plants)
- Upravljanje zbirke rastlin (dodajanje, odstranjevanje)
- Simulacija novih svetlobnih meritev za posamezno rastlino
- Prikaz statusa vsake rastline (Optimal, Low Light, High)
- Galerija fotografij za vsako rastlino — dodajanje mape s slikami prek gumba 📷 Add Folder
- Fotografije so shranjene med sejami (plants_data.json)

### 📅 Zgodovina (History)
- 7-dnevni pregled povprečnih svetlobnih meritev
- Barvno kodiranje po statusu (zelena: optimalno, rdeča: nizko, rumena: visoko)
- Grafični prikaz tedenskih trendov

### 🔬 Zaznavanje zdravja rastlin (Detection)
- Nalaganje fotografije rastline in analiza z nevronsko mrežo EfficientNetB0
- Kombinacija CNN in barvne statistike za ~90% natančnost
- Prikaz diagnoze, simptomov in priporočil
- Prikaz zaupnosti modela (confidence %)

### 💡 Priporočila (Recommendations)
- Personalizirana priporočila glede na trenutni svetlobni status
- Tri kategorije: Optimal, Low Light, High
- Splošni nasveti za nego rastlin
>>>>>>> Stashed changes

Veja `develop` vključuje:

<<<<<<< Updated upstream
- integrirane funkcionalnosti iz posameznih modulov (uporabniški vmesnik, analiza podatkov, komunikacijski sloj)
- izboljšave obstoječih komponent
- eksperimentalne optimizacije
- začasne implementacije za validacijo delovanja sistema kot celote

### 📜 Pravila uporabe

Za ohranjanje pregledne razvojne strukture veljajo naslednja pravila:

- nove funkcionalnosti se razvijajo izključno v `feature/*` vejah
- veja `develop` služi kot integracijsko okolje
- združevanje (merge) v `main` je dovoljeno samo iz veje `develop`
- pred združitvijo v `main` mora biti zagotovljena stabilnost in osnovno testiranje sistema

### 🚀 Trenutno stanje

- aktivna integracija posameznih modulov
- sistemsko testiranje stabilnosti
- priprava na prvo stabilno izdajo v veji `main`
=======
### 🖥️ Celozaslonski način
- Preklop v celozaslonski način prek gumba ⛶ ali tipke F11
>>>>>>> Stashed changes
