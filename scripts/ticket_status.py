#!/usr/bin/env python3
"""Which tickets still need work? The prompts in docs/prompts/<platform>/ start from this.
Usage: ticket_status.py [android|ios ...]      list tickets, newest first, with their state
       ticket_status.py --sha <ticket.md>      print the value a plan must record as 'source-sha:'
States: NEW          ticket has no plan in specs/<platform>/<same file name>
        CHANGED      ticket was edited after the plan was written (source-sha differs or is missing)
        TO_GENERATE  plan is current but some scenario is not marked '**Status:** GENERATED'
        DONE         nothing pending
Files starting with '_' (templates) and README.md are ignored."""
import hashlib, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
sha = lambda p: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]

def state(ticket, plan):
    if not plan.exists(): return "NEW", ""
    text = plan.read_text()
    m = re.search(r"^source-sha:\s*([0-9a-f]+)", text, re.M)
    if not m or m.group(1) != sha(ticket): return "CHANGED", f"plan records {m.group(1) if m else 'no source-sha'}, ticket is {sha(ticket)}"
    parts = re.split(r"^#### (\d+\.\d+)\b.*$", text, flags=re.M)
    ids, blocks = parts[1::2], parts[2::2]
    if not ids: return "TO_GENERATE", "plan has no '#### N.N' scenarios"
    pending = [i for i, b in zip(ids, blocks) if "**Status:** GENERATED" not in b]
    return ("TO_GENERATE", "scenarios " + ", ".join(pending)) if pending else ("DONE", f"{len(ids)} scenarios generated")

if sys.argv[1:2] == ["--sha"]:
    print(sha(pathlib.Path(sys.argv[2]))); sys.exit(0)
for platform in sys.argv[1:] or ["android", "ios"]:
    if platform not in ("android", "ios"): sys.exit(f"unknown platform '{platform}' (use android or ios)")
    print(f"== {platform}")
    tickets = [p for p in (root / "tickets" / platform).glob("*.md") if not p.name.startswith("_") and p.name != "README.md"]
    if not tickets: print("   no tickets")
    for t in sorted(tickets, key=lambda p: p.stat().st_mtime, reverse=True):
        s, why = state(t, root / "specs" / platform / t.name)
        print(f"   {s:12} {t.relative_to(root)}  {why}")
