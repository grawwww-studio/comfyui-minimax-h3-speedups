#!/bin/bash
# Face check on every finished clip in clips/<setting>/<shot>_s<seed>.mp4 (CPU only, resumable: names already in review/face/face_scores.jsonl are skipped).
# Metric and constants as frozen in RULE.md section 4. References: a face close-up and a full-body front view of your test character.
# Needs python3 with numpy, opencv-python and onnxruntime, and the three model files in scripts/weights/ (see README, "Face check").
# Usage: scripts/score_clips.sh FACE_REF.png FRONT_REF.png     then: python3 -I scripts/bench.py --aggregate
set -eu
cd "$(dirname "$0")/.."
FACE=${1:?face close-up reference}; FRONT=${2:?front full-body reference}
specs=()
for f in clips/*/*.mp4; do
  [ -e "$f" ] || continue
  s=$(basename "$(dirname "$f")"); b=$(basename "$f" .mp4); shot=${b%%_s*}; seed=${b##*_s}
  specs+=("${s}__${shot}__s${seed}|${f}|${f}|${shot}")
done
[ ${#specs[@]} -gt 0 ] || { echo "no clips"; exit 0; }
mkdir -p review/face
exec python3 -I scripts/score_face.py --refs "$FACE" "$FRONT" --out review/face "${specs[@]}"
