## 🔧 Razvojna veja (develop)

### 📌 Pregled veje

Veja `develop` predstavlja primarno razvojno in integracijsko okolje projekta.  
V tej veji se združujejo in validirajo vse nove funkcionalnosti pred vključitvijo v stabilno produkcijsko vejo (`main`).

Gre za centralno integracijsko plast sistema, kjer se preverja skladnost, stabilnost in medsebojno delovanje vseh modulov.

### 🎯 Namen

Glavni cilj veje `develop` je:

- zagotoviti stabilno integracijo funkcionalnosti iz `feature/*` vej
- omogočiti sistemsko testiranje celotne aplikacije
- identificirati in odpraviti napake pred izdajo stabilne verzije
- pripraviti preverjeno kodo za prehod v produkcijsko vejo (`main`)

Veja deluje kot kontrolna točka pred produkcijsko izdajo.

### 🏗️ Vsebina veje

Veja `develop` vključuje:

- integrirane funkcionalnosti iz posameznih modulov (uporabniški vmesnik, analiza podatkov, komunikacijski sloj)
- izboljšave obstoječih komponent
- eksperimentalne optimizacije
- začasne implementacije za validacijo delovanja sistema kot celote

### 📜 Pravila uporabe

Za ohranjanje pregledne razvojne strukture veljajo naslednja pravila:

- nove funkcionalnosti se razvijajo izključno v `feature/*` vejah
- veja `develop` služi kot integracijsko okolje
- združevanje (merge) v `main` je dovoljeno samo iz veje `develop`
- pred združitvijo v `main` mora biti zagotovljena stabilnost in osnovno testiranje sistema

### 🚀 Trenutno stanje

- aktivna integracija posameznih modulov
- sistemsko testiranje stabilnosti
- priprava na prvo stabilno izdajo v veji `main`
