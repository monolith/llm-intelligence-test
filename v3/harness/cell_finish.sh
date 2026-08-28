#!/usr/bin/env bash
# Usage: cell_finish.sh MODEL MODE TASK_OUTPUT_JSONL — assemble 3-part answers, capture the transcript, verify prescribed reads.
set -u
M=$1; MODE=$2; OUT=$3; ROOT=/home/anatoly/llm-intelligence-test; D=$ROOT/v3/runs/$M/$MODE; PY=$ROOT/v2/harness/.venv/bin/python
cd $ROOT
cat $D/answers-part1.md $D/answers-part2.md $D/answers-part3.md > $D/answers.md && wc -w $D/answers.md | awk '{print "answers words:",$1}'
if [ "$MODE" = "single" ]; then
  $PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript.jsonl | tail -1
  $PY v2/harness/verify_transcript.py --transcript $D/transcript.jsonl --allowed bundle-single.md --allowed answers-part1.md --allowed answers-part2.md --allowed answers-part3.md || echo "VERIFY FAILED $M $MODE"
elif [ "$MODE" = "sequential" ]; then
  $PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript.jsonl | tail -1
  ALLOWED=$(grep -o '`[^`]*\.md`' $D/instructions.md | tr -d '`' | xargs -n1 basename | awk '!seen[$0]++' | sed 's/^/--allowed /' | tr '\n' ' ')
  $PY v2/harness/verify_transcript.py --transcript $D/transcript.jsonl --allowed instructions.md $ALLOWED || echo "VERIFY FAILED $M $MODE"
else
  $PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript-seg3.jsonl | tail -1
  ALLOWED=$(grep -o '`[^`]*\.md`' $D/segment-3.md | tr -d '`' | xargs -n1 basename | awk '!seen[$0]++' | sed 's/^/--allowed /' | tr '\n' ' ')
  $PY v2/harness/verify_transcript.py --transcript $D/transcript-seg3.jsonl --allowed segment-3.md $ALLOWED || echo "VERIFY FAILED $M $MODE seg3"
  cat $D/transcript-seg1.jsonl $D/transcript-seg2.jsonl $D/transcript-seg3.jsonl > $D/transcript.jsonl
fi
