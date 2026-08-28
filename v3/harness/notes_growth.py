"""Retention-notes growth per model across long-variant ingest segments (a compaction-capacity signal)."""
import glob, os, re, sys
root = sys.argv[1] if len(sys.argv) > 1 else "v3/runs"
print(f"{'model':8s} {'segment word counts (in order)'}")
for m in sorted(os.listdir(root)):
    d = os.path.join(root, m, "long-notes", "ingest")
    if not os.path.isdir(d):
        continue
    files = sorted(glob.glob(os.path.join(d, "notes-*.md")),
                   key=lambda p: int(re.search(r"notes-(\d+)", p).group(1)))
    counts = [len(open(f, encoding="utf-8").read().split()) for f in files]
    flat = ""
    if len(counts) >= 3 and len(set(counts[-3:])) == 1:
        flat = "  <- saturated (last three identical)"
    print(f"{m:8s} " + " ".join(f"{c:,}" for c in counts) + flat)
