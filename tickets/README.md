# Tickets: your only input

Put **new acceptance criteria / action items** here, one Markdown file per feature or batch:

- Android: `tickets/android/<name>.md`
- iOS: `tickets/ios/<name>.md`

1. Copy the platform's `_TEMPLATE.md` to a new file (or add items to an existing ticket).
2. Paste the matching prompt from `docs/prompts/<platform>/pipeline.md` into Claude Code.
3. The prompt runs `python3 scripts/ticket_status.py <platform>` and picks up whatever is new or changed, newest first.

The test plan is written to `specs/<platform>/<same file name>.md`. Files starting with `_` are ignored.
Never put credentials or personal data in a ticket.
