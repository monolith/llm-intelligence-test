#!/usr/bin/env bash
# Usage: reread_step.sh MODEL BATCH SEG TASK_OUTPUT_JSONL BUDGET
# One step of a long-reread chain: the model re-reads the whole corpus with ONE batch's questions
# in hand. Same segment schedule as that model's long-notes ingest, so the two cells are
# comparable read-for-read; only the notes directory and the reader's purpose differ.
set -u
M=$1; B=$2; S=$3; OUT=$4; BUD=${5:-110000}
ROOT=/home/anatoly/llm-intelligence-test
D=$ROOT/v3/runs/$M/long-reread/batch-$B/ingest
PY=$ROOT/v2/harness/.venv/bin/python
cd $ROOT
$PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript-seg$S.jsonl | tail -1
ALLOWED=$($PY v3/harness/plan_segments.py --root v3 --model $M --budget $BUD --max-lines 800 --out /dev/null --verify-allowed $S | tr -d '"' | tr '\n' ' ')
$PY v2/harness/verify_transcript.py --transcript $D/transcript-seg$S.jsonl --allowed batch-$B.md --allowed segment-$S.md $ALLOWED || echo "VERIFY FAILED $M b$B seg $S"
CAP=$(grep -c "exceeds maximum allowed tokens" $D/transcript-seg$S.jsonl)
[ "$CAP" != "0" ] && echo "!! $CAP read(s) hit the token cap in seg $S"
wc -w $D/notes-$S.md 2>/dev/null | awk '{print "notes words:",$1}'
N=$((S+1))
TOTAL=$($PY -c "import json;p=json.load(open('$ROOT/v3/runs/$M/long-notes/ingest/plan.json'));print(len(p if isinstance(p,list) else p['segments']))")
if [ "$N" -le "$TOTAL" ]; then
  $PY v3/harness/plan_segments.py --root v3 --model $M --budget $BUD --max-lines 800 --out /dev/null --render $N \
    | sed "s#Read \`v3/#Read \`$ROOT/v3/#; s#notes to \`v3/#notes to \`$ROOT/v3/#; s#long-notes/ingest#long-reread/batch-$B/ingest#g" > $D/segment-$N.md
  $PY v3/harness/split_big_reads.py $D/segment-$N.md --max-lines 300 --max-bytes 40000
  echo "rendered segment $N of $TOTAL"
else
  echo "CHAIN COMPLETE: $M batch $B finished at segment $S of $TOTAL"
fi
