#!/usr/bin/env bash
# Render the 9-second "situation skit" reel (v4).  usage: render_reel4.sh cfg.json out.mp4 [music_offset_seconds]
# cfg keys: sticky,label1,q1,q2,label2,h1,h2,fix1,fix2,gloss_de,gloss_ua,cta  (see examples/kita.json)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CFG_PATH=$(realpath "$1"); OUT=$(realpath -m "$2"); OFFSET=${3:-20}
WORK=$(mktemp -d)
FRAMES_DIR="$WORK/frames" CFG="$CFG_PATH" python3 "$HERE/compose_v4.py"
(cd "$WORK" && DUR=9 EV="$HERE/ev_v4.json" MUSIC="$HERE/in/ai_44k.wav" OFFSET="$OFFSET" python3 "$HERE/mix.py")
ffmpeg -v error -y -framerate 30 -i "$WORK/frames/%04d.jpg" -i "$WORK/mix.wav" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -profile:v high -r 30 -c:a aac -b:a 192k -ar 44100 -movflags +faststart -t 9 "$OUT"
rm -rf "$WORK"
echo "ok $OUT"
