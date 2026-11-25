# Wikipedia iOS core test plan

source: tickets/ios/wikipedia-core.md
source-sha: 4924a4f07275

## Application overview

Wikipedia for iOS (`org.wikimedia.wikipedia`), simulator Debug build of `main` @ `a3fe64194c`. Tabs: Home, Places,
Saved, Activity, Search. Articles have a bottom toolbar (Contents, Change language, Save, Find in page, Theme, More).

## Exploration method

Live walkthrough with Maestro 2.12.1 on an iPhone 18 Pro simulator (iOS 27.2) on 2026-11-25, reading the accessibility
hierarchy and a screenshot on each screen. The onboarding behaviour in observation 1 was also reproduced on an
iPhone 17 Pro (iOS 26.5). Every id below was seen on the running app. Selectors live in the POM repo
(`mobile-pom-maestro/ios/pages`).

## Observations (read before changing a test)

1. **Tab bar ids missing right after onboarding.** After **Skip**, the same Maestro session shows Home and the tab bar,
   but the tab bar buttons are reported **without** their `Root Tab …` ids, so id assertions fail (all five failure trees of
   run `2026-11-25_203635_cycle-01_ios_iphone-18-pro`). A new session or an app relaunch reports the ids. Whether the app
   or the test driver causes this is not determined. *(Corrected 2026-11-26: an earlier version said the screen was blank;
   it was not.)* The page object relaunches the app; matching the tab labels instead may make that unnecessary.
2. **Onboarding completion is not saved the instant Skip is tapped.** Stopping the app a few seconds after Skip showed
   onboarding again in two of five tests (run `2026-11-25_205828_cycle-02_ios_iphone-18-pro`, TC04 and TC05). Sending
   the app to the background before stopping it avoided this in the runs since. Worth raising with the app team.
3. **"No results found" appears only after the search is submitted.** While typing a no-match term the results area is
   blank, with no message.
4. **Maestro treats ids and text as regular expressions.** Contents item ids contain parentheses, for example
   `Article Table of Contents Item Touring_South_America_(1925)`; match with `Touring_South_America.*`.
5. The onboarding headline uses a curly apostrophe ("world’s").
6. The article is one web view; the whole text is in the hierarchy with positions far below the screen.
7. **Test setup uses an app launch argument.** TC-02 to TC-05 skip onboarding with `-DidShowOnboarding5.3 YES` (and
   suppress the Home announcement), the switches the app's own XCUITests use. Only TC-01 walks through onboarding.

## Test scenarios

**Precondition for 1.2 to 1.5:** fresh app state, onboarding skipped by launch argument, Home shown
(`flows/subflows/ios_start_on_home.yaml`).

### 1. Core journeys

#### 1.1 first-launch-onboarding  (TC-01)
**Status:** GENERATED, PASSING on iPhone and iPad (verified 2026-11-25).  
**File:** `flows/ios/TC01_happy_first_launch_onboarding.yaml`
**Priority:** P0   **Tags:** smoke, happy, functional
**Preconditions:** fresh install state.
**Steps:**
  1. Launch.
     - expect: `App Onboarding Intro View`, "All the world’s knowledge", `App Onboarding Learn More Link`, no `Root Tab .* Button`
  2. Tap `App Onboarding Next Button` three times.
     - expect: `App Onboarding Data Privacy View`, then `App Onboarding Languages View` with "English", then `App Onboarding Personalization Intro View`
  3. Tap `App Onboarding Skip Button`, background the app, relaunch (observations 1 and 2).
     - expect: `Root Tab Home|Places|Saved|Activity Button`, `Search Tab Button`, "For You", "Community", no `App Onboarding .*`
**Limit:** because of observation 1 this proves "onboarding completes and the app then opens on Home", not that Home
appears immediately after Skip. The feed content is not asserted.

#### 1.2 search-open-article  (TC-02)
**Status:** GENERATED, PASSING on iPhone and iPad (verified 2026-11-25).  
**File:** `flows/ios/TC02_happy_search_open_article.yaml`
**Priority:** P0   **Tags:** smoke, happy, search
**Steps:**
  1. Tap `Search Tab Button`.
     - expect: `Search Field`, "No history to show"
  2. Type "Albert Einstein".
     - expect: field shows the text; `Search Result Albert Einstein`; "German-born theoretical physicist"
  3. Tap that result.
     - expect: title and description, `Article Table of Contents Button`, `Article Languages Button`, `Article Save Button`, `Article Find In Page Button`

#### 1.3 search-no-results  (TC-03)
**Status:** GENERATED, PASSING on iPhone and iPad (verified 2026-11-25).  
**File:** `flows/ios/TC03_negative_search_no_results.yaml`
**Priority:** P1   **Tags:** regression, negative, search
**Steps:**
  1. Open Search.
     - expect: no "No results found"
  2. Type `zzqxjvkwq9871` and press the keyboard Search key.
     - expect: "No results found"; no `Search Result .*`; app still running

#### 1.4 save-article  (TC-04)
**Status:** GENERATED, PASSING on iPhone; FAILING on iPad (IOS-01, IOS-02) (verified 2026-11-25).  
**File:** `flows/ios/TC04_functional_save_article.yaml`
**Priority:** P1   **Tags:** regression, functional, saved
**Steps:**
  1. Tap `Root Tab Saved Button`.
     - expect: `Saved View`; no `Saved All Articles Row Albert Einstein`
  2. Search and open "Albert Einstein"; tap `Article Save Button`.
     - expect: label changes from "Save for later" to "Saved. Activate to unsave."
  3. Tap `Article Home Button`, then **Close** on the search, then the Saved tab.
     - expect: `Saved All Articles Row Albert Einstein` with its description

#### 1.5 contents-jump-to-section  (TC-05)
**Status:** GENERATED, PASSING on iPhone; FAILING on iPad (IOS-03) (verified 2026-11-25).  
**File:** `flows/ios/TC05_functional_contents_jump_to_section.yaml`
**Priority:** P2   **Tags:** regression, functional, article
**Steps:**
  1. Open the "Albert Einstein" article.
     - expect: "Touring South America…" not visible
  2. Tap `Article Table of Contents Button`.
     - expect: `Article Table of Contents View` and the item `Touring_South_America.*`
  3. Tap the item.
     - expect: Contents closes; heading visible; "German-born theoretical physicist" no longer visible

## Traceability

| Scope test case | Scenario | Flow |
|---|---|---|
| TC-01 | 1.1 | TC01 |
| TC-02 | 1.2 | TC02 |
| TC-03 | 1.3 | TC03 |
| TC-04 | 1.4 | TC04 |
| TC-05 | 1.5 | TC05 |

## Status

All five scenarios: **GENERATED, PASSING** (verified 2026-11-25, iPhone 18 Pro simulator, iOS 27.2).

| Run | Result | Output check | Note |
|---|---|---|---|
| `2026-11-25_203635_cycle-01_ios_iphone-18-pro` | 0/5 | video over 60 s | observation 1 (blank hierarchy); video text since capped |
| `2026-11-25_205828_cycle-02_ios_iphone-18-pro` | 3/5 | pass | observation 2 (TC04, TC05); setup changed to the launch argument |
| `2026-11-25_211639_cycle-03_ios_iphone-18-pro` | 5/5 | pass | final code |
| `2026-11-25_212532_cycle-04_ios_iphone-18-pro` | 5/5 | pass | final code, repeat (authoritative) |

**iPad** (iPad Pro 11-inch (M5), iOS 27.2), run `2026-11-25_223007_cycle-06_ios_ipad-pro-11`: **3/5**. TC-01 to TC-03 pass; TC-04 and TC-05 fail
(docs/KNOWN-ISSUES.md IOS-01 to IOS-03). A later iPhone run, `2026-11-25_215741_cycle-05_ios_iphone-18-pro`, also passed 5/5;
the Contents page objects changed afterwards for the iPad sidebar. TC-05 passed once on the iPhone with the changed page objects
(single check without evidence recording, not a recorded run).

One iPhone and one iPad have been covered. Two consecutive passes do not show that TC-01 can never hit observation 2.
