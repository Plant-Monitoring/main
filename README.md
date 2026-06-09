# Sistem za spremljanje in analizo svetlobnih razmer za zdravje rastlin

> **Razvojna veja (`develop`).** To je aktivna razvojna oziroma integracijska veja. Funkcijske veje (`feature/*`) se združujejo sem in se po preverjanju izdajo v vejo `main`.

## Pregled projekta

Projekt obravnava razvoj integriranega sistema za spremljanje, analizo in interpretacijo svetlobnih pogojev, ki vplivajo na rast in fiziološko stanje rastlin.

Sistem omogoča:

- zajem svetlobnih podatkov s pomočjo strojnih senzorjev,
- digitalno obdelavo in filtriranje meritev,
- analizo svetlobnih parametrov,
- vizualizacijo rezultatov,
- podporo pri odločanju glede optimalnih pogojev za rast rastlin.

Cilj je vzpostaviti modularno, razširljivo in merljivo platformo za nadzor svetlobnih pogojev v nadzorovanih okoljih (npr. rastlinjaki, laboratoriji, notranji prostori).

## Tehnični cilji

- implementacija zanesljivega zajema svetlobnih podatkov (vzorčenje v realnem času ali periodično),
- kalibracija in validacija senzorjev,
- predobdelava podatkov (filtriranje šuma, normalizacija),
- analiza svetlobnih pogojev glede na definirane pragove,
- vizualna predstavitev časovnih serij,
- modularna arhitektura sistema za nadaljnjo razširljivost.

## Arhitektura sistema

Sistem je zasnovan modularno in je razdeljen na naslednje komponente.

### 1. Zajem podatkov

- branje podatkov iz svetlobnih senzorjev (STM32),
- periodično vzorčenje,
- osnovna validacija meritev,
- shranjevanje surovih podatkov.

### 2. Obdelava in analiza

- filtriranje in glajenje signalov,
- izračun ključnih parametrov (intenziteta, povprečja, odstopanja),
- primerjava z referenčnimi pragovi,
- analiza višine in zdravstvenega stanja rastlin (model EfficientNetB0),
- napoved rasti in barve ter priporočilni sistem.

### 3. Vizualizacija

- grafični prikaz časovnih serij,
- prikaz povprečnih vrednosti in trendov,
- interpretacija rezultatov za uporabnika,
- namizni vmesnik (Tkinter) s svetlo in temno temo.

### 4. Integracija sistema

- povezava med strojno in programsko komponento,
- enotna podatkovna struktura,
- zaledni del (FastAPI), ki streže napovedi modelov,
- možnost nadaljnje nadgradnje (npr. samodejno prilagajanje svetlobe).

### 5. Testiranje in validacija

- funkcionalno testiranje posameznih modulov,
- preverjanje stabilnosti sistema,
- samodejni potek CI/CD (GitHub Actions),
- dokumentacija delovanja.

## Tehnologije

- Python (Tkinter, FastAPI, TensorFlow/Keras, Pillow),
- STM32 za zajem svetlobnih podatkov,
- Docker in docker-compose za kontejnerizacijo,
- GitHub Actions za CI/CD.

## Namestitev in zagon

```bash
git clone https://github.com/Plant-Monitoring/main.git
cd main
git checkout develop
```

Zagon grafičnega vmesnika:

```bash
cd ui
python main.py
```

Zagon zalednega strežnika (API):

```bash
python API/api.py
```

Zagon prek Dockerja:

```bash
docker compose -f docker/docker-compose.ubuntu.yml up
```

## Upravljanje različic (struktura Git)

Projekt uporablja strukturiran razvojni model (GitFlow):

- `main` – stabilna, preverjena različica,
- `develop` – aktivna razvojna veja (ta veja),
- `feature/*` – implementacija posameznih funkcionalnosti.

## Razvojni potek

1. Nova funkcionalnost se razvija v svoji veji `feature/*`, ki izhaja iz veje `develop`.
2. Ko je funkcionalnost dokončana, se združi nazaj v vejo `develop`.
3. Po preverjanju (CI: lint in gradnja slik) se veja `develop` združi v vejo `main`.

## Trenutno stanje

Projekt je zaključen. V veji `develop` so integrirane vse ključne komponente sistema:

- zajem svetlobnih podatkov s senzorji STM32,
- predobdelava in analiza svetlobnih razmer,
- analiza višine in zdravstvenega stanja rastlin (model EfficientNetB0),
- napoved rasti in barve ter priporočilni sistem,
- zaledni del (FastAPI) in namizni grafični vmesnik (Tkinter) s svetlo in temno temo,
- kontejnerizacija (Docker) in samodejni potek CI/CD (GitHub Actions).

## Avtorji

- Anastasija Temova
- David Boshevski
- Damjan Milenković

Mentor: Marko Bizjak

## Licenca

Projekt je objavljen pod licenco MIT (glej datoteko `LICENSE`).
