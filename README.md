# MyClub — Home Assistant integraatio

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![version](https://img.shields.io/badge/versio-1.1.0-blue)

Tuo MyClub-seurasi tulevat tapahtumat suoraan Home Assistantiin. Toimii kaikkien myclub.fi-pohjaisten seurojen kanssa.

---

## Mitä tämä tekee?

Integraatio hakee seuran kalenterin iCal-syötteen ja luo kaksi sensoria:

| Sensori | Tila | Käyttö |
|---|---|---|
| `sensor.<nimi>_seuraava_tapahtuma` | Seuraavan tapahtuman nimi | Logtaulu, dashboardilla |
| `sensor.<nimi>_tulevat_tapahtumat` | Tulevien tapahtumien määrä | Automaatiot, kortit |

### Attribuutit — seuraava tapahtuma
```
date: "pe 23.5."
time: "18:00–19:30"
start_iso: "2026-05-23T18:00:00+03:00"
end_iso: "2026-05-23T19:30:00+03:00"
location: "Liikuntahalli A"
description: "Joukkueharjoitus"
all_day: false
count: 7   ← tulevien tapahtumien kokonaismäärä
```

### Attribuutit — tulevat tapahtumat (lista)
```yaml
events:
  - title: "Joukkueharjoitus"
    date: "pe 23.5."
    time: "18:00–19:30"
    location: "Liikuntahalli A"
    start_iso: "2026-05-23T18:00:00+03:00"
  - title: "Ottelu: FC Testi"
    date: "su 25.5."
    ...
```

---

## Asennus HACS:n kautta

### 1. Lisää custom repository

1. Avaa Home Assistant → **HACS → Integrations**
2. Paina yläkulman **⋮ (kolme pistettä)** → **Custom repositories**
3. Syötä URL:
   ```
   https://github.com/pjaaskel/hacs-myclub
   ```
4. Valitse kategoria: **Integration**
5. Paina **Add**

### 2. Asenna integraatio

1. Etsi HACS:sta "MyClub"
2. Paina **Download** → **Download**
3. **Käynnistä Home Assistant uudelleen**

### 3. Lisää integraatio HA:han

1. Mene **Asetukset → Laitteet ja palvelut → + Lisää integraatio**
2. Etsi "MyClub"
3. Täytä lomake:

| Kenttä | Esimerkki | Kuvaus |
|---|---|---|
| **Nimi** | `Liikuntaseura` | Vapaa nimi, näkyy sensorien nimissä |
| **iCal-osoite** | `https://id.myclub.fi/flow/calendar_subscriptions/12345.ics?token=abc...` | Kopioi MyClubista (ks. alla) |
| **Päivitysväli** | `30` | Minuuttia, oletuksena 30 min |

---

## iCal-osoitteen löytäminen MyClubista

1. Kirjaudu sisään osoitteessa [id.myclub.fi](https://id.myclub.fi) tai seurasi omassa osoitteessa
2. Mene **Kalenteri** → **Tilaa kalenteri** tai etsi "iCal" / "Tilaa" -painike
3. Kopioi URL joka alkaa `https://...myclub.fi/flow/calendar_subscriptions/...`

> **Huom:** URL sisältää henkilökohtaisen tokenin. Pidä se salaisena.

---

## Käyttö dashboardilla

### Markdown-kortti (seuraava tapahtuma)

```yaml
type: markdown
title: Seuraava harjoitus
content: >
  {% set e = state_attr('sensor.liikuntaseura_seuraava_tapahtuma', 'date') %}
  {% set t = state_attr('sensor.liikuntaseura_seuraava_tapahtuma', 'time') %}
  {% set loc = state_attr('sensor.liikuntaseura_seuraava_tapahtuma', 'location') %}

  **{{ states('sensor.liikuntaseura_seuraava_tapahtuma') }}**

  📅 {{ e }}{% if t %}  🕐 {{ t }}{% endif %}

  {% if loc %}📍 {{ loc }}{% endif %}
```

### Entities-kortti (lista kaikista)

```yaml
type: markdown
title: Tulevat tapahtumat
content: >
  {% set events = state_attr('sensor.liikuntaseura_tulevat_tapahtumat', 'events') %}
  {% if events %}
    {% for e in events %}
  **{{ e.title }}** — {{ e.date }}{% if e.time %} klo {{ e.time }}{% endif %}
    {% endfor %}
  {% else %}
  Ei tulevia tapahtumia.
  {% endif %}
```

---

## Automaatioesimerkki — ilmoitus ennen harjoitusta

```yaml
automation:
  - alias: "MyClub harjoitusmuistutus"
    trigger:
      - platform: template
        value_template: >
          {% set start = state_attr('sensor.liikuntaseura_seuraava_tapahtuma', 'start_iso') %}
          {% if start %}
            {% set t = as_datetime(start) %}
            {{ (t - now()).total_seconds() | int in range(3300, 3900) }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "⚽ Harjoitusmuistutus"
          message: >
            {{ states('sensor.liikuntaseura_seuraava_tapahtuma') }}
            klo {{ state_attr('sensor.liikuntaseura_seuraava_tapahtuma', 'time') }}
            — alkaa noin tunnin kuluttua
```

---

## Useampi seura

Voit lisätä integraation useita kertoja eri nimillä ja iCal-osoitteilla:

- `sensor.jalkapallo_seuraava_tapahtuma`
- `sensor.taitoluistelu_seuraava_tapahtuma`
- jne.

---

## Vianmääritys

| Ongelma | Syy | Ratkaisu |
|---|---|---|
| Sensori näyttää "Ei tulevia tapahtumia" | Kalenterissa ei ole tulevia tapahtumia | Tarkista MyClub-portaali |
| `cannot_connect`-virhe asennuksessa | URL ei toimi | Testaa URL selaimella |
| Tapahtumat eivät päivity | Päivitysväli liian pitkä | Muuta asetuksissa (5–1440 min) |
| Väärä aikavyöhyke | iCal-lähde käyttää eri aikavyöhykettä | Luo issue GitHubissa |

### Debug-lokit

Lisää `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.myclub: debug
```

---

## Kehitys ja palaute

- **Bugiraportit ja ehdotukset:** [GitHub Issues](https://github.com/pjaaskel/hacs-myclub/issues)
- **Lisenssi:** MIT

Integraatio toimii kaikkien myclub.fi-pohjaisten seurojen kanssa: joukkueurheiluseurat, tanssi, taitoluistelu, kamppailulajit jne.
