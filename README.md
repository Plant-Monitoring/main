## Veja za zaznavanje zdravja rastlin (`feature/detection`)

### Pregled veje

Veja vsebuje sistem za zaznavanje zdravstvenega stanja rastline iz slike. Uporablja naučen konvolucijski model EfficientNetB0 (binarna klasifikacija: zdrava / nezdrava), ob zaznani nezdravi rastlini pa s pomočjo barvne hevristike oceni možen vzrok. Veja izhaja iz veje `develop`.

### Namen

Glavni cilji te veje so:

- oceniti zdravstveno stanje rastline iz naložene slike,
- pri nezdravi rastlini predlagati možen vzrok (barvna analiza),
- integrirati zaznavo v zaledni del (API) in grafični vmesnik.

### Vsebina veje

- `models/detection.py` – sklepanje z modelom in barvna hevristika,
- `plant_health_cnn.keras` – naučen model (EfficientNetB0, binarna klasifikacija),
- integracija prek `API/api.py` (končna točka `/api/detect`) in strani za zaznavo v grafičnem vmesniku.

### Delovanje

1. Uporabnik naloži sliko rastline.
2. Model EfficientNetB0 napove, ali je rastlina zdrava ali nezdrava.
3. Pri nezdravi rastlini barvna hevristika oceni možen vzrok (npr. pomanjkanje vode, pomanjkanje hranil).

### Pravila uporabe

- razvoj poteka izključno v tej veji `feature/*`,
- veja izhaja iz veje `develop` in se vanjo združi po dokončanju,
- spremembe se ne združujejo neposredno v vejo `main`.

### Trenutno stanje

- model je naučen na podatkih celotnih rastlin (binarno: zdrava / nezdrava), z natančnostjo približno 90 % na testni množici,
- ocena vzroka je hevristična (orientacijska, ne diagnostična),
- zaznava je integrirana v API in grafični vmesnik,
- veja je dokončana in pripravljena za združitev v vejo `develop`.

### Opomba

Napoved zdravja je binarna; ocenjeni vzrok temelji na barvni analizi slike in je informativne narave.
