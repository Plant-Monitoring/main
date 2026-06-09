## Veja za priporočilni sistem (`feature/recommendation-system`)

### Pregled veje

Veja vsebuje priporočilni sistem, ki na podlagi analiziranih razmer (svetloba, temperatura) predlaga ukrepe za boljšo nego rastline. Sistem uporablja mehko (fuzzy) logiko za določanje pripadnosti razmer in tehtanje priporočil. Veja izhaja iz veje `develop`.

### Namen

Glavni cilji te veje so:

- na podlagi izmerjenih razmer predlagati konkretne ukrepe za nego rastline,
- upoštevati mehke (fuzzy) prehode med razmerami namesto ostrih pragov,
- ponuditi priporočila prek zalednega API-ja in v grafičnem vmesniku.

### Vsebina veje

- modul priporočilnega sistema (mehka logika, pravila in uteži),
- integracija prek `API/api.py` (končna točka za priporočila),
- prikaz priporočil v grafičnem vmesniku.

### Delovanje

1. Sistem prejme analizirane razmere (npr. svetloba, temperatura).
2. Z mehko (fuzzy) logiko določi pripadnost razmer posameznim območjem.
3. Na podlagi pravil in uteži sestavi priporočila za nego rastline.

### Pravila uporabe

- razvoj poteka izključno v tej veji `feature/*`,
- veja izhaja iz veje `develop` in se vanjo združi po dokončanju,
- spremembe se ne združujejo neposredno v vejo `main`.

### Trenutno stanje

- izdelani sta prva in končna različica priporočilnega sistema,
- sistem je integriran prek FastAPI in povezan z grafičnim vmesnikom,
- veja je dokončana in pripravljena za združitev v vejo `develop`.
