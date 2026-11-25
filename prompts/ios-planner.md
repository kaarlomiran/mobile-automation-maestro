# Prompt 1 - Planner (iOS test plan from the live app)

Replace the `<placeholders>`, then paste the block into Claude Code from this repo.

```text
Act as the Planner for the iOS Maestro suite.

INPUT - read these before touching the simulator:
1. tickets/<your-scope>.md   - acceptance criteria (the oracle for "correct")
2. sessions/*.md             - if an exploration report exists for this area,
                               read it next; plan ONLY its AUTOMATE rows

Explore the live app on a booted iOS simulator with Maestro (inspect_screen /
maestro hierarchy, take_screenshot). App id comes from config/ios.env.

Plan only what the scope file's test cases cover. Do not invent scenarios.

Rules:
- Read-only exploration. Do NOT write flows or page objects.
- Cite the source on every scenario: tickets/<your-scope>.md#TC-<id>
- If the scope and the app disagree about expected behaviour, STOP and report
  the disagreement - do not silently pick one.
- Save the plan to specs/ios/<area>.md
- Two-part scenario numbers (1.1, 1.2, ...)
- Each scenario: flow file path, priority, tags, preconditions, steps, and
  "expect:" bullets that are specific enough to become assertions
- Record the exact accessibility ids and labels you observed on screen.
  Never take an id from memory or from source code without seeing it live.
- Record anything surprising (timing, hidden elements, regex characters in ids)

Approach:
1. Boot a simulator and install apps/Wikipedia.app
2. launchApp (clearState) and inspect the hierarchy on each screen
3. Walk each test case, noting real behaviour, with a screenshot per outcome
4. Write the plan, then report open questions
```
