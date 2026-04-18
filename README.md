## 🔌 Komunikacija STM32 (feature/stm32_communications)

### 📌 Pregled veje

Veja `feature/stm32_communications` implementira komunikacijski sloj med mikrokrmilnikom STM32 in programskim delom sistema.

Modul predstavlja povezovalni vmesnik med strojno (senzorji, mikrokrmilnik) in programsko komponento (analiza, vizualizacija), pri čemer zagotavlja zanesljiv, strukturiran in časovno usklajen prenos podatkov.

### 🎯 Namen

Cilji komunikacijskega modula so:

- zanesljiv prenos senzornih meritev
- sinhronizacija med strojno in programsko komponento
- podpora real-time ali periodičnemu zajemu podatkov
- zagotavljanje integritete prenesenih podatkov

Modul mora delovati robustno tudi v primeru motenj ali komunikacijskih napak.

### ⚙️ Funkcionalnosti

#### 📡 Serijska komunikacija

- komunikacija preko UART / USB (Serial)
- dvosmerni prenos podatkovnih paketov
- definirani komunikacijski protokoli
- inicializacija in upravljanje povezave

#### 📥 Zajem podatkov

- branje svetlobnih meritev iz priključenih senzorjev
- časovno označevanje meritev (timestamp)
- periodično ali sproženo pošiljanje podatkov

#### 🧾 Strukturiranje podatkov

- definiran format podatkovnih paketov (npr. JSON ali binarni zapis)
- serializacija in deserializacija podatkov
- validacija strukture paketa pred nadaljnjo obdelavo

#### 🛡️ Robustnost in varnost prenosa

- preverjanje integritete podatkov (npr. checksum)
- zaznavanje poškodovanih ali nepopolnih paketov
- obravnava izgubljenih podatkov
- mehanizmi ponovnega prenosa ali obveščanja o napaki

### 🏗️ Arhitektura modula

**STM32 (strojni del):**
- zajem podatkov iz svetlobnih senzorjev
- osnovna predobdelava (po potrebi)
- oblikovanje podatkovnih paketov
- pošiljanje podatkov preko UART/USB

**Računalniški del (programski sistem):**
- sprejem podatkov preko serijskega vmesnika
- validacija in razčlenitev paketov
- posredovanje podatkov analitičnemu modulu
- beleženje morebitnih napak

Komunikacijski sloj deluje kot vmesni most med embedded in aplikacijskim delom sistema.

### 🧰 Uporabljene tehnologije

- Mikrokrmilnik: STM32
- Komunikacija: UART / Serial (USB)
- Programska implementacija: Python (serial knjižnice)
- Definicija podatkovnih paketov: strukturiran tekstovni ali binarni zapis

### 🚀 Trenutno stanje

- osnovna serijska komunikacija vzpostavljena
- uspešen prenos testnih meritev
- implementirana osnovna validacija paketov
- testiranje stabilnosti prenosa v teku
- nadgradnja robustnosti in izboljšava obravnave napak
