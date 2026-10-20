#!/usr/bin/env bash
# Crumpled-page trend reel.  usage: render_crumple.sh cfg.json out.mp4
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CFG_PATH=$(realpath "$1"); OUT=$(realpath -m "$2")
DUR=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('dur',10))" "$CFG_PATH")
WORK=$(mktemp -d)
python3 -c "import json,sys; json.dump(json.load(open(sys.argv[1]))['sfx'], open(sys.argv[2],'w'))" "$CFG_PATH" "$WORK/ev.json"
FRAMES_DIR="$WORK/frames" CFG="$CFG_PATH" python3 "$HERE/compose_crumple.py"
(cd "$WORK" && DUR=$DUR python3 "$HERE/music_v6.py" && DUR=$DUR EV="$WORK/ev.json" MUSIC="$WORK/music_v6.wav" OFFSET=0 python3 "$HERE/mix.py")
ffmpeg -v error -y -framerate 30 -i "$WORK/frames/%04d.jpg" -i "$WORK/mix.wav" -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -profile:v high -r 30 -c:a aac -b:a 192k -ar 44100 -movflags +faststart -t $DUR "$OUT"
rm -rf "$WORK"
echo "ok $OUT"
