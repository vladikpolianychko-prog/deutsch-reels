#!/usr/bin/env bash
# Render a 16-second v7 reel (own cast/props per cfg).  usage: render_reel7.sh cfg.json out.mp4
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CFG_PATH=$(realpath "$1"); OUT=$(realpath -m "$2")
WORK=$(mktemp -d)
python3 -c "import json,sys; json.dump(json.load(open(sys.argv[1]))['sfx'], open(sys.argv[2],'w'))" "$CFG_PATH" "$WORK/ev.json"
FRAMES_DIR="$WORK/frames" CFG="$CFG_PATH" python3 "$HERE/compose_v7.py"
(cd "$WORK" && DUR=16 python3 "$HERE/music_v6.py" && DUR=16 EV="$WORK/ev.json" MUSIC="$WORK/music_v6.wav" OFFSET=0 python3 "$HERE/mix.py" && CFG="$CFG_PATH" python3 "$HERE/voice_mix.py")
ffmpeg -v error -y -framerate 30 -i "$WORK/frames/%04d.jpg" -i "$WORK/mix.wav" -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -profile:v high -r 30 -c:a aac -b:a 192k -ar 44100 -movflags +faststart -t 16 "$OUT"
rm -rf "$WORK"
echo "ok $OUT"
