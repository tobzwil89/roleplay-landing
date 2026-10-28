# Projekt: Roleplay-Warteliste (Einstiegsseite)

Filmische Einstiegsseite mit Warteliste für die Rollenspiel-App (`../roleplay`). **Live** unter
https://roleplay.tobiaszwilling.me (GitHub Pages, Repo `tobzwil89/roleplay-landing`, jeder Push auf `main` geht live).
Im Desktop (`../tobiaszwilling-desktop`) mit `embed: false` verlinkt, öffnet im neuen Tab.

## Aufbau

- `index.html` – die ganze Seite: Text DE/EN, Anmeldung, Impressum und Datenschutz als Dialog. Kein Build.
- `assets/hero-16x9.mp4`, `assets/hero-9x16.mp4` – Hintergrundvideo quer/hoch (12 s, nahtlose Schleife).
- `assets/poster-*.jpg` – Standbilder (Ersatz bei „Bewegung reduzieren“ und solange das Video lädt).
- `assets/fonts/` – Cormorant Garamond und Manrope (OFL), lokal statt von Google (Datenschutz).
- `scene/scene.html` – die Szene „Das Tor“ als WebGL-Shader, live im Browser ansehbar.
- `scene/render.mjs` – nimmt die Szene Bild für Bild auf und baut Videos und Standbilder
  (`node scene/render.mjs`, Probe-Standbilder: `node scene/render.mjs still`). Braucht ffmpeg und Playwright
  aus `../tunnel-front/node_modules`.

## Das Hintergrundvideo: wie es gemacht ist

Komplett aus Code, keine KI-Videos, keine fremden Bilder:

1. **Szene als Fragment-Shader** (`scene/scene.html`, reines WebGL2, keine Bibliothek). Jeder Bildpunkt wird
   berechnet: Himmel mit Wolken und Sternen, Berge, Ruinen, Spitzbogen-Tor (zwei Kreise + Rechteck), Stufen,
   Wanderer mit Stab und Schatten, Bodennebel (Rauschen „fbm“), Lichtstrahlen (vom Bildpunkt zur Lichtquelle
   laufen und zählen, wie oft der Durchgang getroffen wird), 70 Glutfunken, Runen-Puls, Tonemapping.
2. **Nahtlose Schleife:** Alles hängt nur von der Phase `uT` (0–1) ab. Bewegungen nutzen ganzzahlige
   Frequenzen; treibender Nebel überblendet zwei versetzte Rauschfelder. Nach 12 s ist das Bild wieder identisch.
3. **Aufnahme:** `scene/render.mjs` öffnet die Szene in Playwright (Chromium), ruft `renderAt(t)` für jedes der
   360 Bilder auf, macht Screenshots, ffmpeg baut daraus H.264-MP4 (CRF 27, ca. 1 MB je Format).
4. **Zwei Formate:** Querformat (Tor rechts, Text links) und Hochformat (Szene kleiner und höher, Text unten).
   Die Seite wählt per `<source media="(orientation: portrait)">`. Filmkorn kommt per CSS, nicht im Video
   (spart Dateigröße).

### Wunsch für später: viel filmischer („wie ein kurzer Actionfilm-Ausschnitt“)

Tobias' Rückmeldung am 28.10.2026: „ist gut für jetzt“, soll aber deutlich cineastischer werden.
Das aktuelle Video ist ein ruhiges Standbild mit Bewegung, ohne Schnitte und echte Kamerafahrt; die
Formen sind flach (2D-Silhouetten). Ideen, grob nach Wirkung:

- **Echtes 3D statt 2D-Shader:** Blender (Open Source) mit freien Modellen (Poly Haven, Quaternius, Kenney, CC0)
  oder Three.js. Erst damit gibt es Tiefe, Licht auf Oberflächen, Perspektive bei Kamerafahrten.
  Wahrscheinlich der größte Sprung. Blender rendert offline, Ergebnis wieder als MP4.
- **Schnitte und Kamera:** 3–4 Einstellungen in 12–15 s (Totale → Fahrt auf das Tor → Nah auf den Wanderer →
  Lichtausbruch), Kameraschwenks, leichtes Wackeln, Zeitlupe.
- **Kinoeffekte:** Bewegungsunschärfe, Tiefenunschärfe, Linsenreflexe, Breitbild-Balken, stärkere Farbgebung,
  Blitze/Funkenregen, Staub im Gegenlicht.
- **Handlung:** z. B. das Tor öffnet sich, Licht flutet heraus, Figur tritt hindurch.
- Schleife ist dann schwerer: entweder Schnitt zurück auf die erste Einstellung oder Video nur einmal abspielen
  und auf dem letzten Bild stehen bleiben.
- Bisher ausgeschlossen auf Tobias' Wunsch: KI-Videogeneratoren (Higgsfield) und Stockvideos.

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
- 28.10.2026: Testanmeldung mit tobitobbs@gmail.com über die Seite erfolgreich (EmailOctopus: success).
  Der frühere Fehler lag an der example.com-Adresse. Doppel-Opt-in war in EmailOctopus aus, Tobias hat es
  eingeschaltet.
- 28.10.2026: Repo auf GitHub (Tobias hat es angelegt, weil das Anlegen für Claude gesperrt war), Pages und
  DNS laufen, Seite live. Desktop-Eintrag committet und gepusht, Klick öffnet neuen Tab (geprüft).

## Offen

- Anmeldung mit eingeschaltetem Doppel-Opt-in testen: kommt die Bestätigungsmail, steht die Adresse bis zum
  Klick auf „Pending“?
- Video filmischer machen mit Blender: Auftrag für einen neuen Chat steht in `BLENDER_AUFTRAG.md` (28.10.2026).
