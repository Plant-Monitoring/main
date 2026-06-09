## Veja za neprekinjeno integracijo in dostavo (`feature/CI-CD`)

### Pregled veje

Veja vsebuje vzpostavitev poteka CI/CD (neprekinjena integracija in dostava) z orodjem GitHub Actions. Ob vsaki spremembi se koda samodejno preveri, zgradita se obe Docker sliki, ob izdaji v vejo `main` pa se sliki objavita v register vsebnikov. Veja izhaja iz veje `develop`.

### Namen

Glavni cilji te veje so:

- samodejno preverjanje kode ob vsakem potisku in zahtevku za združitev (pull request),
- zagotavljanje, da se aplikacija (API in GUI) uspešno zgradi,
- objava preverjenih slik ob izdaji (release),
- skrajšanje ročnega dela in zmanjšanje napak pri integraciji.

### Vsebina veje

Veja vključuje datoteko `.github/workflows/ci-cd.yml` z naslednjimi opravili (jobs):

- `lint` – preverjanje sintakse (flake8) in oblike kode (black, informativno),
- `build-images` – gradnja Docker slik za API in GUI (brez objave),
- `release` – ob potisku v vejo `main` objava slik v GitHub Container Registry (okolje `release`).

### Potek

1. Potisk ali zahtevek za združitev sproži opravili `lint` in `build-images`.
2. Ob potisku v vejo `main` se zažene še opravilo `release`, ki objavi sliki v register.
3. Objava poteka prek vgrajenega žetona `GITHUB_TOKEN`, zato dodatne skrivnosti niso potrebne.

### Pravila uporabe

Za ohranjanje pregledne razvojne strukture veljajo naslednja pravila:

- razvoj poteka CI/CD poteka izključno v tej veji `feature/*`,
- veja izhaja iz veje `develop` in se vanjo združi po dokončanju,
- objava (release) se izvede šele, ko sprememba doseže vejo `main`.

### Trenutno stanje

- potek CI/CD je vzpostavljen in deluje (`lint` in gradnja slik sta uspešna),
- opravilo `release` objavi sliki v GitHub Container Registry v okolju `release`,
- prvotna ročna objava na Docker Hub in namestitev prek SSH sta bili odstranjeni, saj za študentski projekt nista bili potrebni,
- veja je dokončana in pripravljena za združitev v vejo `develop`.

### Opomba

Okolje `release` v zavihku Environments prikazuje uspešne objave slik; prejšnje neuspešne objave v okolju `production` so bile odstranjene.
