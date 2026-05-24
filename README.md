## 🖥️ Uporabniški vmesnik (feature/user-interface)

### Plant Monitor

Plant Monitor je namizna aplikacija za spremljanje svetlobnih pogojev rastlin, razvita v programskem jeziku Python z uporabo ogrodja Tkinter.
Uporabniški vmesnik je zasnovan kot interaktivna nadzorna plošča (dashboard), ki omogoča pregled nad svetlobnimi meritvami, upravljanje rastlin ter konfiguracijo sistemskih nastavitev.

## Funkcionalnosti

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

### ⚙️ Nastavitve (Settings)
- Nastavitev pragov svetlobne intenzitete
- Vklop/izklop obvestil
- Prilagoditev prikaza uporabniškega vmesnika

### 🖥️ Celozaslonski način
- Preklop v celozaslonski način prek gumba ⛶ ali tipke F11
