#!/bin/zsh
# Rendert das Video „Das Tor erwacht“ und baut daraus eine MP4.
# Aufruf (aus dem Projektordner):
#   blender/render.sh 16x9 50 vorschau   → blender/frames/vorschau-16x9/ und blender/vorschau-16x9.mp4
#   blender/render.sh 9x16 100 final     → blender/frames/final-9x16/ und blender/final-9x16.mp4
# Abbrechen mit Ctrl+C ist jederzeit möglich; beim nächsten Aufruf werden fertige Bilder übersprungen.
set -e
fmt=${1:-16x9}; pct=${2:-50}; name=${3:-vorschau}
dir=blender/frames/$name-$fmt
blender -b --factory-startup -P blender/scene.py -- --fmt $fmt --frames 1-390 --pct $pct --out $dir | grep BILD
ffmpeg -loglevel error -y -framerate 30 -i $dir/%04d.png -c:v libx264 -preset slow -crf 27 -pix_fmt yuv420p \
  -an -movflags +faststart blender/$name-$fmt.mp4
ls -lh blender/$name-$fmt.mp4
