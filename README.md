<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/ML-TensorFlow%20%7C%20Keras-FF6F00?logo=tensorflow&logoColor=white" alt="TensorFlow Keras">
  <img src="https://img.shields.io/badge/Model-EfficientNetB0-8E24AA" alt="EfficientNetB0">
  <br>
  <img src="https://img.shields.io/badge/GUI-Tkinter-4B8BBE" alt="Tkinter">
  <img src="https://img.shields.io/badge/Sensors-STM32-03234B?logo=stmicroelectronics&logoColor=white" alt="STM32">
  <img src="https://img.shields.io/badge/Database-SQL-336791?logo=postgresql&logoColor=white" alt="Database">
  <img src="https://img.shields.io/badge/Deploy-Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white" alt="CI/CD">
  <br>
  <img src="https://img.shields.io/badge/Domain-Plant%20Health-2E7D32" alt="Domain">
  <img src="https://img.shields.io/badge/Analysis-Light%20Conditions-F9A825" alt="Analysis">
  <img src="https://img.shields.io/badge/Reproducibility-Docker%20%2B%20GHCR-43A047" alt="Reproducibility">
  <img src="https://img.shields.io/badge/Status-Done-4CAF50" alt="Status">
</p>
# Sistem za spremljanje in analizo svetlobnih razmer za zdravje rastlin

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

Projekt uporablja strukturiran razvojni model:

- `main` – stabilna, preverjena različica,
- `develop` – aktivna razvojna veja,
- `feature/*` – implementacija posameznih funkcionalnosti.

## Trenutno stanje

Projekt je zaključen. Implementirane in integrirane so vse ključne komponente sistema:

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
