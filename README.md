## Veja za napoved rasti (`feature/growth-color-model`)

### Pregled veje

Veja vsebuje model za napoved rasti rastline na podlagi izmerjenih svetlobnih razmer in drugih parametrov. Veja izhaja iz veje `develop`.

### Namen

Glavni cilji te veje so:

- napovedati pričakovano rast rastline glede na razmere,
- omogočiti prikaz napovedi v grafičnem vmesniku,
- ponuditi napoved prek zalednega API-ja.

### Vsebina veje

- model za napoved rasti (PyTorch, datoteka `.pt`) v mapi `models/`,
- integracija prek `API/api.py` (končna točka za napoved rasti in barve),
- prikaz rezultatov v grafičnem vmesniku.

### Pravila uporabe

- razvoj poteka izključno v tej veji `feature/*`,
- veja izhaja iz veje `develop` in se vanjo združi po dokončanju,
- spremembe se ne združujejo neposredno v vejo `main`.

### Trenutno stanje

- izdelani sta prva in končna različica modela za napoved rasti,
- model je integriran prek FastAPI in povezan z grafičnim vmesnikom,
- veja je dokončana in pripravljena za združitev v vejo `develop`.
