#!/usr/bin/env bash
# Render the 12-second "notebook comes alive" reel (v5).  usage: render_reel5.sh cfg.json out.mp4 [music_offset_seconds]
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CFG_PATH=$(realpath "$1"); OUT=$(realpath -m "$2"); OFFSET=${3:-20}
WORK=$(mktemp -d)
FRAMES_DIR="$WORK/frames" CFG="$CFG_PATH" python3 "$HERE/compose_v5.py"
(cd "$WORK" && DUR=12 EV="$HERE/ev_v5.json" MUSIC="$HERE/in/ai_44k.wav" OFFSET="$OFFSET" python3 "$HERE/mix.py")
ffmpeg -v error -y -framerate 30 -i "$WORK/frames/%04d.jpg" -i "$WORK/mix.wav" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -profile:v high -r 30 -c:a aac -b:a 192k -ar 44100 -movflags +faststart -t 12 "$OUT"
rm -rf "$WORK"
echo "ok $OUT"
