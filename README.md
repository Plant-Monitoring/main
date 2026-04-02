# 🌱 Sistem za spremljanje in analizo svetlobnih razmer za zdravje rastlin

## Pregled projekta

Projekt obravnava razvoj integriranega sistema za spremljanje, analizo in interpretacijo svetlobnih pogojev, ki vplivajo na rast in fiziološko stanje rastlin.

Sistem omogoča:

- zajem svetlobnih podatkov s pomočjo strojnih senzorjev,
- digitalno obdelavo in filtriranje meritev,
- analizo svetlobnih parametrov,
- vizualizacijo rezultatov,
- podporo odločanju glede optimalnih pogojev za rast rastlin.

Cilj je vzpostaviti modularno, razširljivo in merljivo platformo za nadzor svetlobnih pogojev v nadzorovanih okoljih (npr. rastlinjaki, laboratoriji, notranji prostori).

## Tehnični cilji

- Implementacija zanesljivega zajema svetlobnih podatkov (real-time ali periodično vzorčenje)
- Kalibracija in validacija senzorjev
- Predobdelava podatkov (filtriranje šuma, normalizacija)
- Analiza svetlobnih pogojev glede na definirane pragove
- Vizualna predstavitev časovnih serij
- Modularna arhitektura sistema za nadaljnjo razširljivost

## Arhitektura sistema

Sistem je zasnovan modularno in je razdeljen na naslednje komponente:

### 1. Zajem podatkov
- Branje podatkov iz svetlobnih senzorjev
- Periodično vzorčenje
- Osnovna validacija meritev
- Shranjevanje surovih podatkov

### 2. Obdelava in analiza
- Filtriranje in glajenje signalov
- Izračun ključnih parametrov (intenziteta, povprečja, odstopanja)
- Primerjava z referenčnimi pragovi
- Identifikacija potencialnih odstopanj

### 3. Vizualizacija
- Grafični prikaz časovnih serij
- Prikaz povprečnih vrednosti in trendov
- Interpretacija rezultatov za uporabnika

### 4. Integracija sistema
- Povezava med strojno in programsko komponento
- Enotna podatkovna struktura
- Možnost nadaljnje nadgradnje (npr. avtomatsko prilagajanje svetlobe)

### 5. Testiranje in validacija
- Funkcionalno testiranje posameznih modulov
- Preverjanje stabilnosti sistema
- Dokumentacija delovanja

## Upravljanje verzij (Git struktura)

Projekt uporablja strukturiran razvojni model:

- `main` – stabilna, preverjena verzija
- `develop` – aktivna razvojna veja
- `feature/*` – implementacija posameznih funkcionalnosti
- `bugfix/*` – odprava napak


## Trenutno stanje

Projekt je v začetni fazi implementacije.

Trenutno je vzpostavljena:

- osnovna arhitektura repozitorija
- razvojna struktura (branching model)
- priprava okolja za zajem in obdelavo podatkov
