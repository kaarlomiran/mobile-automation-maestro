# Test Scope: Wikipedia Android - core suite (TC-01 to TC-12)

**Platform:** android
**Application under test:** Wikipedia for Android (`org.wikipedia`), Maestro sample APK
**Author:** QA   **Date:** 2026-11-26
**Source:** written down **after** automation, from the existing flows and the original request (top test cases:
happy path, functional, negative, search, boundary; later language change and scroll to end of article)

## Objective
A user can onboard, search, open and read articles, move between tabs and change the search language, and invalid input
is handled safely.

## Test data
| Field | Value |
|---|---|
| Search term | `Albert Einstein` |
| Short description | `German-born theoretical physicist` |
| No-match term | `zzqxjkvv` |
| Special input | `<script>alert(1)</script>` and `'; DROP TABLE users;--` |
| Query length limit | 300 characters |

## Preconditions
1. Fresh app state for each test. No account.

## Acceptance criteria

| ID | Priority / tags | Steps | Expected |
|---|---|---|---|
| TC-01 | P0 smoke, happy | Fresh launch, complete onboarding | Onboarding shown first; then the Explore feed and bottom tabs; onboarding gone |
| TC-02 | P0 smoke, search | Search the search term | The article and a related result are listed; no "No results" |
| TC-03 | P1 search | Open the top result | Article page with title, description and article actions |
| TC-04 | P1 functional | Visit each bottom tab | Each tab shows its screen; the first Activity visit shows its intro |
| TC-05 | P1 search | Search, then clear with X | Query and results are removed |
| TC-06 | P1 search | Search in lower case and upper case | Same top article both times |
| TC-07 | P1 negative | Search the no-match term | "No results"; no stale result rows |
| TC-08 | P1 negative | Enter the special input | Shown as plain text, treated as an ordinary search (results may be listed); no crash |
| TC-09 | P2 boundary | Search a single character | Suggestions are listed |
| TC-10 | P2 boundary | Enter 300, then 301 characters | 300 accepted; 301 rejected with an error naming the limit |
| TC-11 | P1 language | Add Spanish and switch the search language tab | Spanish results; switching back restores English |
| TC-12 | P2 article | Scroll a long article to the end | The end of the article (license text and browser link) is reached |

Every test also expects no crash or "not responding" dialog.
