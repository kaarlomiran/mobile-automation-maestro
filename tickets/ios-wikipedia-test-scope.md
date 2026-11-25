# Test Scope: Wikipedia iOS - onboarding, search, saved articles, article contents

**Application under test:** Wikipedia for iOS (`org.wikimedia.wikipedia`), simulator Debug build from
https://github.com/wikimedia/wikipedia-ios (`main` @ `a3fe64194c`, local checkout with uncommitted changes in the
Xcode project file)
**Test type:** End-to-end functional, UI automation with Maestro (Page Object Model)
**Author:** QA
**Date:** 2026-11-25

---

## 1. Objective

Verify that a new user can get through onboarding, find and open an article, gets a clear empty state for a search with
no matches, can save an article and find it again, and can jump to a section from the article's Contents list.

## 2. Notes / assumptions

- Content is live Wikipedia. Expected values use stable facts only (the article "Albert Einstein" and its short
  description "German-born theoretical physicist").
- Device language is English (US). The app opens English Wikipedia.
- Each test starts from a fresh app state (`clearState`). No account is used; no test signs in.

## 3. In scope

| # | Area |
|---|------|
| 1 | First-launch onboarding and Home tab bar |
| 2 | Search: results, opening an article |
| 3 | Search: no matches |
| 4 | Saving an article and the Saved tab |
| 5 | Article Contents (table of contents) navigation |

## 4. Out of scope (this batch)

Account/login, editing, notifications, widgets, Places map, Activity, reading lists, offline mode, accessibility audit,
performance, iPad layouts, real devices.

## 5. Test data

| Field | Value |
|---|---|
| Search term | `Albert Einstein` |
| Expected short description | `German-born theoretical physicist` (followed by the dates) |
| No-match search term | `zzqxjvkwq9871` |
| Contents section | `Touring South America (1925)` |

## 6. Preconditions

1. Booted iOS simulator with network access to wikipedia.org.
2. The app is installed (`apps/Wikipedia.app`, not committed).

## 7. Test cases

### TC-01 - First launch and onboarding (P0, smoke)
| | |
|---|---|
| **Steps** | 1. Launch with cleared state <br> 2. Go through the onboarding pages with **Next** <br> 3. On "Follow your curiosity" tap **Skip** |
| **Expected** | Intro page shows "All the world's knowledge" and a "Learn more about Wikipedia" link; no tab bar yet <br> Pages appear in order: intro, Data & Privacy, languages (English listed), personalization <br> App opens on Home with tabs Home, Places, Saved, Activity, Search and the Community / For You switch <br> Onboarding is not shown again |

### TC-02 - Search and open an article (P0, smoke)
| | |
|---|---|
| **Steps** | 1. Open the **Search** tab <br> 2. Type `Albert Einstein` <br> 3. Tap the result "Albert Einstein" |
| **Expected** | Before typing: "No history to show" <br> A result titled "Albert Einstein" with the expected description <br> The article opens with title, description and the toolbar (Contents, Change language, Save, Find in page) |

### TC-03 - Search with no matches (P1, negative)
| | |
|---|---|
| **Steps** | 1. Open **Search** <br> 2. Type `zzqxjvkwq9871` <br> 3. Press the keyboard **Search** key |
| **Expected** | "No results found" is shown; no result rows; app does not crash |

### TC-04 - Save an article (P1, functional)
| | |
|---|---|
| **Steps** | 1. Open **Saved** and confirm the article is not there <br> 2. Search and open "Albert Einstein" <br> 3. Tap **Save for later** <br> 4. Close the article and the search <br> 5. Open **Saved** |
| **Expected** | The save control changes from "Save for later" to "Saved. Activate to unsave." <br> Saved > All articles lists "Albert Einstein" with its description |

### TC-05 - Jump to a section from Contents (P2, functional)
| | |
|---|---|
| **Steps** | 1. Open the "Albert Einstein" article <br> 2. Tap the **Table of contents** button <br> 3. Tap "Touring South America (1925)" |
| **Expected** | Before: that heading is not on screen <br> After: Contents closes, the heading is on screen, the top of the article has scrolled away |

## 8. Entry and exit criteria

**Entry:** simulator booted, app installed, page objects synced.
**Exit:** TC-01 to TC-05 executed with a complete evidence set (output guard passes); every failure explained.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Live content or search ranking changes | Assert the exact article title id and a stable part of the description |
| Feature announcement cards appear (for example "Discover" on Saved) | Assert rows by id; do not depend on position |
| Test driver loses the screen after onboarding | Documented relaunch in the page object (see the test plan) |

## 10. Candidates for the next batch (not created yet)

Create these only after TC-01 to TC-05 are accepted: unsave an article; recent searches and clearing them; change article
language; find in page; theme and text size; Home / Places / Activity tab checks; landscape and iPad layout.
