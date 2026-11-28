# ANDROID - full pipeline (new tickets -> test plan -> automation -> run)

Your only job: add or edit files in `tickets/android/`, then paste this block into Claude Code.

```text
Run the android test pipeline for this repo. Follow CLAUDE.md.

1. python3 scripts/ticket_status.py android
   Work only on android tickets that are NEW, CHANGED or TO_GENERATE, newest first.
   If everything is DONE, say so and stop.
2. For each NEW or CHANGED ticket: follow docs/prompts/android/planner.md.
   If the ticket and the live app disagree, stop that ticket and report it.
3. Show me the plan summary (scenario id, title, source), then continue.
4. For each scenario not yet GENERATED: follow docs/prompts/android/generator.md.
5. Run the suite, invoke the verify-run-outputs skill, and if anything failed the
   triage-machine-failures skill. Run .venv/bin/python scripts/lint_suite.py.
6. python3 scripts/ticket_status.py android  and report: tickets handled, files
   changed, results per device, every failure with its triage label, open questions.

Do not commit or push unless I ask.
```
