#!/usr/bin/env bash
# Usage: noisy_step.sh MODEL SEG TASK_OUTPUT_JSONL — capture + verify one noisy-mode segment against its instruction file.
set -u
M=$1; S=$2; OUT=$3
ROOT=/home/anatoly/llm-intelligence-test; D=$ROOT/v3/runs/$M/noisy; PY=$ROOT/v2/harness/.venv/bin/python
cd $ROOT
$PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript-seg$S.jsonl | tail -1
ALLOWED=$(grep -o '`[^`]*\.md`' $D/segment-$S.md | tr -d '`' | xargs -n1 basename | awk '!seen[$0]++' | sed 's/^/--allowed /' | tr '\n' ' ')
$PY v2/harness/verify_transcript.py --transcript $D/transcript-seg$S.jsonl --allowed segment-$S.md $ALLOWED || echo "VERIFY FAILED $M seg $S"
for f in $D/notes-after-r*.md; do [ -f "$f" ] && wc -w "$f" | awk '{print "notes:",$2,$1,"words"}'; done
