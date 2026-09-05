#!/usr/bin/env bash
# Usage: tail_verify.sh MODEL SEG TASK_OUTPUT_JSONL
# Verifies a hand-built tail segment (see tail_segments.py) against its own segment file:
# captures the transcript, checks every tool use is a prescribed read (in order) or a benign
# own-output write, and checks the noise document's coverage is contiguous over the segment's span.
set -u
M=$1; S=$2; OUT=$3
ROOT=/home/anatoly/llm-intelligence-test
D=$ROOT/v3/runs/$M/long-notes/ingest
PY=$ROOT/v2/harness/.venv/bin/python
cd $ROOT
$PY v2/harness/capture_transcript.py "$OUT" --out $D/transcript-seg$S.jsonl | tail -1
# ordered, de-duplicated file sequence: instruction file, each prescribed file in first-seen order, the notes written
ALLOWED=$( { grep -E '^[0-9]+\. (Read|Write)' $D/segment-$S.md | sed -E 's/^[0-9]+\. (Read|Write your retention notes to) `([^`]+)`.*/\2/' | xargs -n1 basename | awk '!seen[$0]++'; } | sed 's/^/--allowed /' | tr '\n' ' ')
$PY v2/harness/verify_transcript.py --transcript $D/transcript-seg$S.jsonl --allowed segment-$S.md $ALLOWED || echo "VERIFY FAILED seg $S"
CAP=$(grep -c "exceeds maximum allowed tokens" $D/transcript-seg$S.jsonl)
[ "$CAP" != "0" ] && echo "!! $CAP read(s) hit the token cap in seg $S"
$PY - "$D/segment-$S.md" "$D/transcript-seg$S.jsonl" <<'PYEOF'
import json, re, sys
seg, tr = sys.argv[1], sys.argv[2]
want = {}
for line in open(seg, encoding="utf-8"):
    m = re.match(r"^\d+\. Read `([^`]+)` lines (\d+)–(\d+)", line)
    if m and "notes-" not in m.group(1):
        want.setdefault(m.group(1), []).append((int(m.group(2)), int(m.group(3))))
got = {}
for line in open(tr, encoding="utf-8"):
    try: o = json.loads(line)
    except Exception: continue
    for m in re.finditer(r"\[tool_use Read: (\{.*?\})\]", o.get("text") or "", flags=re.S):
        try: i = json.loads(m.group(1))
        except Exception: continue
        f = i.get("file_path", "")
        if f in want:
            off = int(i.get("offset", 1)); lim = int(i.get("limit", 10**9))
            got.setdefault(f, []).append((off, off + lim - 1))
for f, spans in want.items():
    lo, hi = min(s[0] for s in spans), max(s[1] for s in spans)
    reads = sorted(got.get(f, []))
    covered, cur = [], lo
    for a, b in reads:
        if a <= cur <= b: cur = b + 1
    ok = cur > hi
    print(f"coverage {f.rsplit('/',1)[-1]} {lo}-{hi}: {'complete' if ok else 'GAP at line %d' % cur} ({len(reads)} reads)")
PYEOF
wc -w $D/notes-$S.md | awk '{print "notes words:",$1}'
