## Razvojna veja (develop)

### Pregled veje

Veja `develop` predstavlja primarno razvojno in integracijsko okolje projekta.
V njej se združujejo in validirajo vse nove funkcionalnosti pred vključitvijo v stabilno produkcijsko vejo (`main`).

Gre za centralno integracijsko plast sistema, kjer se preverjajo skladnost, stabilnost in medsebojno delovanje vseh modulov.

### Namen

Glavni cilji veje `develop` so:

- zagotoviti stabilno integracijo funkcionalnosti iz vej `feature/*`
- omogočiti sistemsko testiranje celotne aplikacije
- identificirati in odpraviti napake pred izdajo stabilne različice
- pripraviti preverjeno kodo za prehod v produkcijsko vejo (`main`)

Veja deluje kot kontrolna točka pred produkcijsko izdajo.

### Vsebina veje

Veja `develop` vključuje:

- integrirane funkcionalnosti iz posameznih modulov (uporabniški vmesnik, analiza podatkov, komunikacijski sloj)
- izboljšave obstoječih komponent
- eksperimentalne optimizacije
- začasne implementacije za validacijo delovanja sistema kot celote

### Pravila uporabe

Za ohranjanje pregledne razvojne strukture veljajo naslednja pravila:

- nove funkcionalnosti se razvijajo izključno v vejah `feature/*`
- veja `develop` služi kot integracijsko okolje
- združevanje (merge) v `main` je dovoljeno samo iz veje `develop`
- pred združitvijo v `main` morata biti zagotovljeni stabilnost in osnovno testiranje sistema

### Trenutno stanje

- aktivna integracija posameznih modulov
- sistemsko testiranje stabilnosti
- priprava na prvo stabilno izdajo v veji `main`
