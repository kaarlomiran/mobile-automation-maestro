# ANDROID - Planner (test plan from the live app)

```text
Act as the Planner for the android Maestro suite.

INPUT: the ticket(s) in tickets/android/ that
`python3 scripts/ticket_status.py android` lists as NEW or CHANGED (or the file I name).
The ticket is the oracle for "correct". If sessions/android/*.md exploration notes
exist for this area, read them too.

Explore the live app on a booted Android emulator with Maestro (inspect_screen / maestro hierarchy,
take_screenshot). App id: config/android.env. Install apps/android.apk (adb install -r).

Plan only what the ticket covers. Do not invent scenarios.

Rules:
- Read-only exploration. Do NOT write flows or page objects.
- Save the plan to specs/android/<same file name as the ticket>.md
- Header lines, exactly:
    source: tickets/android/<file>.md
    source-sha: <output of: python3 scripts/ticket_status.py --sha tickets/android/<file>.md>
- One heading per scenario: "#### 1.1 <slug>  (TC-<id>)", followed by
  "**Status:** PENDING", flow file path, priority, tags, preconditions, numbered
  steps, and "expect:" bullets specific enough to become assertions.
- For a CHANGED ticket, update the existing plan: set the affected scenarios back
  to "**Status:** PENDING" and leave unaffected ones as they are.
- Record the ids and labels you actually observed. Never from memory or source code alone.
- Off-screen web view text can be in the accessibility tree (Android 17): visibility alone does not prove scrolling. Tablets show some panels side by side.
- If the ticket and the app disagree, STOP and report it; do not pick one silently.
- Finish with observations and open questions.
```
