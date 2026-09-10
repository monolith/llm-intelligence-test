#!/usr/bin/env bash
# One lane of the A/B experiment: for one model, run the requested repeats of both arms in
# alternating order (baseline r, plugin r, baseline r+1, ...) so that any interruption or
# rate limit lands on both arms alike; judge each run twice as soon as it lands.
#
#   AB_SEAM=none|hinted v3/ab/harness/ab_lane.sh <model> <first-rep> <last-rep> <plugin-dir> [plugin-name]
#
# Skips a (arm, rep) whose run dir already has score-2.json. Logs to $AB_LOGS/<model>-lane.log.
set -u
M=$1; R0=$2; R1=$3; PD=$4; PN=${5:-context-governor}; SEAM=${AB_SEAM:-none}; COND=$([ "$SEAM" = none ] && echo nohint || echo noisy)
ROOT=/home/anatoly/llm-intelligence-test
LOGS=${AB_LOGS:-/tmp/claude-1000/-home-anatoly/24e92440-efc2-4a14-97c2-ee126ebf0ca1/scratchpad/ab-logs}
mkdir -p "$LOGS"
cd "$ROOT"
for r in $(seq "$R0" "$R1"); do
  for arm in baseline plugin; do
    D=v3/ab/$arm/$M/$COND-r$r
    if [ -f "$D/score-2.json" ]; then echo "$(date -u +%H:%M) skip $arm $M r$r (scored)"; continue; fi
    if [ ! -f "$D/provenance.json" ]; then
      echo "$(date -u +%H:%M) run $arm $M r$r"
      rm -rf "/tmp/claude-1000/-home-anatoly/24e92440-efc2-4a14-97c2-ee126ebf0ca1/scratchpad/ab/$arm/$M/$COND-r$r"
      if [ "$arm" = plugin ]; then
        python3 v3/ab/harness/ab_run.py --arm plugin --model "$M" --rep "$r" --seam "$SEAM" --plugin-dir "$PD" --plugin-name "$PN" > "$LOGS/$arm-$M-r$r.log" 2>&1
      else
        python3 v3/ab/harness/ab_run.py --arm baseline --model "$M" --rep "$r" --seam "$SEAM" > "$LOGS/$arm-$M-r$r.log" 2>&1
      fi
      rc=$?; echo "$(date -u +%H:%M) run $arm $M r$r exit $rc: $(tail -n 1 "$LOGS/$arm-$M-r$r.log" | cut -c1-160)"
      [ $rc -ne 0 ] && continue
    fi
    if grep -q INVALID "$D/VERIFY.txt" 2>/dev/null; then echo "$(date -u +%H:%M) $arm $M r$r INVALID — not judging (see VERIFY.txt)"; continue; fi
    echo "$(date -u +%H:%M) judge $arm $M r$r"
    python3 v3/ab/harness/ab_judge.py "$D" > "$LOGS/judge-$arm-$M-r$r.log" 2>&1
    echo "$(date -u +%H:%M) judged $arm $M r$r: $(grep -o 'total=[^ ]*' "$LOGS/judge-$arm-$M-r$r.log" | tr '\n' ' ')"
  done
done
echo "$(date -u +%H:%M) lane $M done"
