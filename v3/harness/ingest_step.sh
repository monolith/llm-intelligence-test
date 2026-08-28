#!/usr/bin/env bash
# Usage: ingest_step.sh MODEL SEG TASK_OUTPUT_JSONL BUDGET
# Captures+verifies segment SEG of MODEL's long-notes ingest, re-plans with the real notes size, renders SEG+1.
set -u
M=$1; S=$2; OUT=$3; B=${4:-110000}
ROOT=/home/anatoly/llm-intelligence-test
D=$ROOT/v3/runs/$M/long-notes/ingest
PY=$ROOT/v2/harness/.venv/bin/python
cd $ROOT
$PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript-seg$S.jsonl | tail -1
ALLOWED=$($PY v3/harness/plan_segments.py --root v3 --model $M --budget $B --max-lines 800 --out $D/plan.json --verify-allowed $S | tr -d '"' | tr '\n' ' ')
# the instruction file is the first prescribed read
$PY v2/harness/verify_transcript.py --transcript $D/transcript-seg$S.jsonl --allowed segment-$S.md $ALLOWED || echo "VERIFY FAILED seg $S"
wc -w $D/notes-$S.md | awk '{print "notes words:",$1}'
N=$((S+1))
$PY v3/harness/plan_segments.py --root v3 --model $M --budget $B --max-lines 800 --out $D/plan.json --render $N | sed "s#Read \`v3/#Read \`$ROOT/v3/#; s#notes to \`v3/#notes to \`$ROOT/v3/#" > $D/segment-$N.md
echo "rendered segment $N: $(grep -c '^[0-9]' $D/segment-$N.md) steps; total segments $($PY -c "import json;p=json.load(open('$D/plan.json'));print(len(p if isinstance(p,list) else p['segments']))")"
