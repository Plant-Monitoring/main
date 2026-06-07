# Dockerizacija za Ubuntu / Linux (celoten sistem)

Na Linuxu lahko v Dockerju poženemo tako API kot grafični vmesnik, ker lahko
kontejner uporablja gostiteljev zaslon (X11) in USB naprave.

## Hitri zagon

Iz korena repozitorija:

```bash
./docker/run-ubuntu.sh
```

Skripta nastavi dovoljenje za X11 (`xhost +local:docker`) in zažene oba servisa.
Ročno:

```bash
xhost +local:docker
docker compose -f docker/docker-compose.ubuntu.yml up --build
```

- API: `http://localhost:8000`
- GUI: odpre se okno aplikacije Plant Monitor.

## Kako deluje

| Servis | Opis |
|---|---|
| `api`  | FastAPI strežnik z modeli (vrata 8000). |
| `gui`  | Tkinter vmesnik. Uporablja gostiteljev zaslon prek `/tmp/.X11-unix` in gostiteljevo omrežje (`network_mode: host`), zato doseže API na `localhost:8000`. |

Podatkovne datoteke (`plants_data.json`, `history_data.json`, `theme_data.json`)
se ohranijo, ker je mapa `ui/` priklopljena kot volume.

## Senzor STM32 (po želji)

V `docker-compose.ubuntu.yml` odkomentirajte razdelek `devices` in nastavite
pravo napravo (preverite z `ls /dev/ttyUSB* /dev/ttyACM*`):

```yaml
    devices:
      - "/dev/ttyACM0:/dev/ttyACM0"
```

Po potrebi dodajte uporabnika v skupino `dialout` ali zaženite z ustreznimi
pravicami za dostop do serijskih vrat.

## Težave z zaslonom

Če se okno ne odpre:

```bash
echo $DISPLAY              # mora biti nastavljen (npr. :0 ali :1)
xhost +local:docker        # ponovno nastavite dovoljenje
```

Pri nekaterih namestitvah je treba dodati še `XAUTHORITY`:

```yaml
    environment:
      - DISPLAY=${DISPLAY}
      - XAUTHORITY=${XAUTHORITY}
    volumes:
      - ${XAUTHORITY}:${XAUTHORITY}
```