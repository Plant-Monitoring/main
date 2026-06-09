## Uporabniški vmesnik (`feature/user-interface`)

### Pregled veje

Plant Monitor je namizna aplikacija za spremljanje svetlobnih pogojev rastlin, razvita v programskem jeziku Python z uporabo ogrodja Tkinter. Uporabniški vmesnik je zasnovan kot interaktivna nadzorna plošča (dashboard), ki omogoča pregled svetlobnih meritev, upravljanje rastlin ter konfiguracijo sistemskih nastavitev. Veja izhaja iz veje `develop`.

### Funkcionalnosti

#### Avtentikacija uporabnikov
- prijava in registracija uporabnikov,
- podpora več uporabnikom (Anastasija, David, Damjan),
- upravljanje uporabniških računov.

#### Nadzorna plošča (Dashboard)
- prikaz svetlobne intenzitete skozi čas,
- grafični prikaz meritev z označenimi pragovi (nizka: 300 lux, optimalna: 800 lux),
- izračun in prikaz povprečne, minimalne in maksimalne vrednosti,
- uvoz podatkov iz datoteke (.bin ali .npz) prek gumba Add File,
- ocena višine rastline iz fotografije z dvema modeloma (barvni in robni).

#### Moje rastline (My Plants)
- upravljanje zbirke rastlin (dodajanje, odstranjevanje),
- simulacija novih svetlobnih meritev za posamezno rastlino,
- prikaz statusa vsake rastline (Optimal, Low Light, Too Much Light),
- galerija fotografij za vsako rastlino (dodajanje mape s slikami prek gumba Add Folder),
- fotografije se ohranijo med sejami.

#### Zgodovina (History)
- pregled povprečnih svetlobnih meritev za zadnjih 10 dni,
- barvno kodiranje po statusu (zelena: optimalno, rdeča: nizko, rumena: visoko),
- grafični prikaz trendov za izbrano meritev.

#### Zaznavanje zdravja rastlin (Detection)
- nalaganje fotografije rastline in analiza z nevronsko mrežo EfficientNetB0,
- kombinacija modela CNN in barvne statistike (približno 90-odstotna natančnost),
- prikaz diagnoze, simptomov in priporočil,
- prikaz zaupnosti modela (confidence %).

#### Priporočila (Recommendation)
- priporočila rastlin glede na uporabnikove preference (potreba po vodi, svetlobi, temperaturi),
- upoštevanje dodatnih pogojev (prostor, varnost za hišne ljubljenčke, alergije),
- razvrščanje rezultatov po ujemanju (fuzzy matching).

#### Napoved rasti (Growth)
- vnos pogojev rastline in napoved prirasta višine,
- napoved barve rastline,
- povezava z napovednim modelom prek API-ja.

#### Nastavitve (Settings)
- nastavitve prikaza uporabniškega vmesnika,
- hranjenje zgodovine in vedenje ob nalaganju datotek,
- nastavitve modela CNN in napovednega API-ja,
- pregled uporabniškega računa.

#### Svetla in temna tema
- preklop med temno in svetlo (sivo) temo prek gumba v stranski vrstici,
- izbrana tema se ohrani med sejami.

#### Celozaslonski način
- preklop v celozaslonski način prek gumba v glavi ali tipke F11.

### Trenutno stanje

- vse funkcionalnosti vmesnika so implementirane in integrirane,
- vmesnik je povezan z modeli in zalednim API-jem,
- veja je dokončana in pripravljena za združitev v vejo `develop`.
