#!/usr/bin/env bash
# Render the 16-second "night sketchbook" reel (v6).  usage: render_reel6.sh cfg.json out.mp4
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CFG_PATH=$(realpath "$1"); OUT=$(realpath -m "$2")
WORK=$(mktemp -d)
FRAMES_DIR="$WORK/frames" CFG="$CFG_PATH" python3 "$HERE/compose_v6.py"
(cd "$WORK" && DUR=16 python3 "$HERE/music_v6.py" && DUR=16 EV="$HERE/ev_v6.json" MUSIC="$WORK/music_v6.wav" OFFSET=0 python3 "$HERE/mix.py")
ffmpeg -v error -y -framerate 30 -i "$WORK/frames/%04d.jpg" -i "$WORK/mix.wav" -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -profile:v high -r 30 -c:a aac -b:a 192k -ar 44100 -movflags +faststart -t 16 "$OUT"
rm -rf "$WORK"
echo "ok $OUT"
