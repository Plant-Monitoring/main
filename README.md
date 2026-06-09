## Veja za kontejnerizacijo (`dockerization`)

### Pregled veje

Veja vsebuje kontejnerizacijo sistema z orodjem Docker. Zaledni del (API) in grafični vmesnik (GUI) sta zapakirana v ločena vsebnika, ki ju povezuje `docker-compose`. Veja izhaja iz veje `develop` in se vanjo združi po dokončanju.

### Namen

Glavni cilji te veje so:

- zagotoviti enako delovanje aplikacije v vseh okoljih (razvoj, testiranje, izvajanje),
- poenostaviti namestitev in zagon brez ročnega nameščanja odvisnosti,
- omogočiti ponovljive gradnje slik (images),
- pripraviti slike za objavo prek poteka CI/CD.

### Vsebina veje

Veja vključuje mapo `docker/` z naslednjimi datotekami:

- `Dockerfile.api` – slika zalednega dela (FastAPI),
- `Dockerfile.gui` – slika grafičnega vmesnika (Tkinter),
- `docker-compose.ubuntu.yml` – hkraten zagon obeh vsebnikov,
- `requirements-*.txt` – odvisnosti za posamezno sliko,
- `run-ubuntu.sh` – pomožna skripta za zagon v okolju Ubuntu/Linux.

### Pravila uporabe

Za ohranjanje pregledne razvojne strukture veljajo naslednja pravila:

- razvoj kontejnerizacije poteka izključno v tej veji `feature/*`,
- veja izhaja iz veje `develop` in se vanjo združi po dokončanju,
- spremembe se ne združujejo neposredno v vejo `main`,
- pred združitvijo se preveri, da se obe sliki uspešno zgradita.

### Zagon

Hkraten zagon API-ja in grafičnega vmesnika prek Dockerja:

```bash
docker compose -f docker/docker-compose.ubuntu.yml up --build
```

Zaledni strežnik (API) privzeto teče na vratih 5000, grafični vmesnik pa v ločenem vsebniku.

### Trenutno stanje

- zaledni del (API) in grafični vmesnik (GUI) sta kontejnerizirana,
- vzpostavljen je `docker-compose` za hkraten zagon obeh vsebnikov,
- gradnja slik je vključena v potek CI/CD (objava v GitHub Container Registry),
- veja je dokončana in pripravljena za združitev v vejo `develop`.

### Opomba

Trenutna kontejnerizacija je prilagojena okolju Ubuntu/Linux.
