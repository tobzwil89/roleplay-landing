# Projekt: Roleplay-Warteliste (Einstiegsseite)

Filmische Einstiegsseite mit Warteliste für die Rollenspiel-App (`../roleplay`). Soll unter
`roleplay.tobiaszwilling.me` laufen und im Desktop (`../tobiaszwilling-desktop`) mit `embed: false` verlinkt werden.

## Aufbau

- `index.html` – die ganze Seite: Text DE/EN, Anmeldung, Impressum und Datenschutz als Dialog. Kein Build.
- `assets/hero-16x9.mp4`, `assets/hero-9x16.mp4` – Hintergrundvideo quer/hoch (12 s, nahtlose Schleife).
- `assets/poster-*.jpg` – Standbilder (Ersatz bei „Bewegung reduzieren“ und solange das Video lädt).
- `assets/fonts/` – Cormorant Garamond und Manrope (OFL), lokal statt von Google (Datenschutz).
- `scene/scene.html` – die Szene „Das Tor“ als WebGL-Shader, live im Browser ansehbar.
- `scene/render.mjs` – nimmt die Szene Bild für Bild auf und baut Videos und Standbilder
  (`node scene/render.mjs`, Probe-Standbilder: `node scene/render.mjs still`). Braucht ffmpeg und Playwright
  aus `../tunnel-front/node_modules`.

## Entscheidungen

- Video wird aus Code erzeugt (kein Higgsfield, kein Stockmaterial), auf Tobias' Wunsch.
- Video statt Live-3D auf der Seite: läuft auf jedem Handy gleich, schont Akku.
- Querformat: Tor rechts, Text links. Hochformat: Szene nach oben geschoben, Text unten.
- Warteliste über EmailOctopus (kostenlos bis ca. 2.500 Abonnenten, Daten in Irland). Brevo verworfen (Konto ging
  nicht / nicht kostenlos). Unser eigenes Formular sendet direkt an den EmailOctopus-Endpunkt (`EO_FORM_ACTION`,
  Felder `field_0` und Honeypot) statt deren Skript einzubinden: deren Skript lädt Google reCAPTCHA (Datenschutz)
  und bringt eigenes Aussehen mit.
- Kein fremder Markenname („Character AI“) auf der Seite: Abmahnrisiko bei abwertendem Vergleich.
- Produktname steht noch nicht fest; die Seite kommt ohne Namen aus.

## Verlauf

- 28.10.2026: Szene, Videos (je ca. 1 MB, Schleifennaht gemessen: so glatt wie ein normaler Bildwechsel),
  Seite, Rechtstexte gebaut. Per Playwright geprüft: Rechner (1440×900) und Handy (390×844), DE und EN,
  kein seitliches Verrutschen, keine Konsolenfehler, Formularprüfung funktioniert („startet in Kürze“ ohne Brevo).
  Lokal ansehen: `python3 -m http.server 8765` im Projektordner, dann http://127.0.0.1:8765
  (nicht als Datei öffnen, sonst lädt die Schrift nicht).

- 28.10.2026: Umstieg Brevo → EmailOctopus, Datenschutztext angepasst (Three Hearts Digital Ltd, London; Adresse
  aus deren Datenschutzerklärung von 2020). Verbindung geprüft: Anfrage kommt an, EmailOctopus antwortet mit
  INVALID_PARAMETERS für eine example.com-Testadresse. Unklar, ob wegen der Adresse oder weil reCAPTCHA verlangt wird.

## Offen

- EmailOctopus: reCAPTCHA im Formular ausschalten, Doppel-Opt-in prüfen, dann Testanmeldung mit echter Adresse.
  Falls reCAPTCHA sich nicht abschalten lässt: neu entscheiden (reCAPTCHA = Google, bräuchte Einwilligung).
- Repository `tobzwil89/roleplay-landing` anlegen, GitHub Pages, Subdomain `roleplay.` (CNAME-Eintrag beim Domainanbieter).
- Eintrag in `../tobiaszwilling-desktop/src/apps.json` mit `embed: false`.
