## Komunikacija STM32 (`feature/stm32_communications`)

### Pregled veje

Veja `feature/stm32_communications` implementira komunikacijski sloj med mikrokrmilnikom STM32 in programskim delom sistema. Modul predstavlja povezovalni vmesnik med strojno komponento (senzorji, mikrokrmilnik) in programsko komponento (analiza, vizualizacija), pri čemer zagotavlja zanesljiv, strukturiran in časovno usklajen prenos podatkov.

### Namen

Cilji komunikacijskega modula so:

- zanesljiv prenos senzornih meritev,
- sinhronizacija med strojno in programsko komponento,
- podpora zajemu podatkov v realnem času ali periodično,
- zagotavljanje integritete prenesenih podatkov.

Modul mora delovati robustno tudi v primeru motenj ali komunikacijskih napak.

### Funkcionalnosti

#### Serijska komunikacija
- komunikacija prek UART / USB (Serial),
- dvosmerni prenos podatkovnih paketov,
- definirani komunikacijski protokoli,
- inicializacija in upravljanje povezave.

#### Zajem podatkov
- branje svetlobnih meritev iz priključenih senzorjev,
- časovno označevanje meritev (timestamp),
- periodično ali sproženo pošiljanje podatkov.

#### Strukturiranje podatkov
- definiran format podatkovnih paketov (npr. JSON ali binarni zapis),
- serializacija in deserializacija podatkov,
- validacija strukture paketa pred nadaljnjo obdelavo.

#### Robustnost in varnost prenosa
- preverjanje integritete podatkov (npr. kontrolna vsota),
- zaznavanje poškodovanih ali nepopolnih paketov,
- obravnava izgubljenih podatkov,
- mehanizmi za ponovni prenos ali obveščanje o napaki.

### Arhitektura modula

**STM32 (strojni del):**
- zajem podatkov iz svetlobnih senzorjev,
- osnovna predobdelava (po potrebi),
- oblikovanje podatkovnih paketov,
- pošiljanje podatkov prek UART/USB.

**Računalniški del (programski sistem):**
- sprejem podatkov prek serijskega vmesnika,
- validacija in razčlenitev paketov,
- posredovanje podatkov analitičnemu modulu,
- beleženje morebitnih napak.

Komunikacijski sloj deluje kot vmesni most med vgrajenim (embedded) in aplikacijskim delom sistema.

### Uporabljene tehnologije

- mikrokrmilnik: STM32,
- komunikacija: UART / Serial (USB),
- programska implementacija: Python (knjižnice za serijsko komunikacijo),
- definicija podatkovnih paketov: strukturiran tekstovni ali binarni zapis.

### Pravila uporabe

- razvoj poteka izključno v tej veji `feature/*`,
- veja izhaja iz veje `develop` in se vanjo združi po dokončanju.

### Trenutno stanje

- serijska komunikacija (UART/USB) je vzpostavljena in deluje,
- prenos in rekonstrukcija senzornih meritev sta zanesljiva,
- implementirana je validacija strukture paketov,
- odpravljena je napaka pri razčlenjevanju zadnjega paketa,
- veja je dokončana in pripravljena za združitev v vejo `develop`.
