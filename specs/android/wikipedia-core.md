# Wikipedia Android core test plan

source: tickets/android/wikipedia-core.md
source-sha: 2f950538e922

## How this plan was made
Written on 2026-11-26 **from the existing flows**, not from a new live exploration. The flows are the exact steps and
assertions; selectors are in the POM repo (`mobile-pom-maestro/android/pages`). New plans must come from the live app
(see `docs/prompts/android/planner.md`).

## Verification status
Each scenario last passed in a full local run on 2026-11-16 (tablet, Android 12 baseline) and 2026-11-17 (small and
large phone), 12/12 per device. Run scripts changed afterwards (issue filing, dialog settling, triage) without a new
local run. The CI baseline (Android 14) passed 12/12 on 2026-11-25 (UTC), GitHub run 45662715331, code `8bdd2e3`.

## Known behaviour
- Injection-like input is searched as ordinary text; the app can list matching articles (seen in CI for the SQL-like input).
- First visit to the Activity tab shows "Introducing Activity"; Android 17 may show a "Customize your toolbar" coach-mark.
- Search accepts at most 300 characters; long text is typed in 50-character chunks (120 s device timeout).
- Android 17 exposes off-screen article text, so TC-12 uses the collapsing toolbar and the native Contents list as proof.

## Test scenarios

### 1. Core suite

#### 1.1 happy-launch-and-onboarding  (TC-01)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC01_happy_launch_and_onboarding.yaml`  
**Tags:** smoke, happy, functional  
**Purpose / expected:** Fresh install: onboarding completes and the Explore feed is shown.  
**Page objects:** onboarding_assert_first_launch, onboarding_complete, home_assert_feed_and_tabs, app_assert_no_crash

#### 1.2 happy-search-returns-results  (TC-02)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC02_happy_search_returns_results.yaml`  
**Tags:** smoke, happy, search  
**Purpose / expected:** Searching "Albert Einstein" lists the matching article with its description.  
**Page objects:** search_enter_query, search_assert_query_text, search_assert_results_list, search_assert_results_for_einstein, search_assert_result_listed, app_assert_no_crash

#### 1.3 happy-open-article-from-search  (TC-03)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC03_happy_open_article_from_search.yaml`  
**Tags:** regression, happy, search  
**Purpose / expected:** Tapping a search result opens the article page.  
**Page objects:** search_enter_query, search_assert_results_list, search_open_top_result, article_assert_loaded, article_assert_title_and_actions, app_assert_no_crash

#### 1.4 functional-bottom-navigation  (TC-04)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC04_functional_bottom_navigation.yaml`  
**Tags:** regression, functional  
**Purpose / expected:** Every bottom-nav tab opens its screen.  
**Page objects:** onboarding_complete, home_assert_loaded, nav_go_to_tab, saved_assert_loaded, activity_assert_intro, activity_close_intro, nav_assert_tab_visible, app_assert_no_crash

#### 1.5 functional-clear-search-query  (TC-05)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC05_functional_clear_search_query.yaml`  
**Tags:** regression, functional, search  
**Purpose / expected:** The X button clears the query and removes the results.  
**Page objects:** search_enter_query, search_assert_results_for_einstein, search_assert_clear_available, search_clear_query, search_assert_not_listed, search_assert_empty, search_assert_field_alive, app_assert_no_crash

#### 1.6 functional-search-case-insensitive  (TC-06)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC06_functional_search_case_insensitive.yaml`  
**Tags:** regression, functional, search  
**Purpose / expected:** Lower-case and upper-case queries return the same top article.  
**Page objects:** search_enter_query, search_assert_results_list, search_assert_results_for_einstein, app_assert_no_crash

#### 1.7 negative-no-results  (TC-07)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC07_negative_no_results.yaml`  
**Tags:** regression, negative, search  
**Purpose / expected:** A nonsense query shows the "No results" state.  
**Page objects:** search_enter_query, search_assert_no_results, search_assert_query_text, search_assert_not_listed, app_assert_no_crash

#### 1.8 negative-special-characters  (TC-08)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC08_negative_special_characters.yaml`  
**Tags:** regression, negative, search  
**Purpose / expected:** Markup / injection-like input is handled safely: no crash, input echoed as plain text.  
**Page objects:** search_enter_query, search_assert_query_text, search_assert_field_alive, app_assert_no_crash

#### 1.9 boundary-single-character  (TC-09)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC09_boundary_single_character.yaml`  
**Tags:** regression, boundary, search  
**Purpose / expected:** Minimum length: a single-character query returns suggestions.  
**Page objects:** search_enter_query, search_assert_query_text, search_assert_results_list, search_assert_field_alive, app_assert_no_crash

#### 1.10 boundary-very-long-query  (TC-10)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC10_boundary_very_long_query.yaml`  
**Tags:** regression, boundary, search  
**Purpose / expected:** Max length is 300: exactly 300 chars is accepted, 301 is rejected with a clear error.  
**Page objects:** search_enter_query, search_append_text, search_assert_field_alive, search_assert_query_within_limit, app_assert_no_crash, search_assert_query_too_long

#### 1.11 functional-change-search-language  (TC-11)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC11_functional_change_search_language.yaml`  
**Tags:** regression, functional, search, language  
**Purpose / expected:** Adding Spanish and switching the search tab returns Spanish-language results.  
**Page objects:** search_assert_default_language, language_add, search_assert_language_tabs, search_enter_query, search_select_language_tab, search_assert_spanish_results, search_assert_results_for_einstein, app_assert_no_crash

#### 1.12 functional-scroll-to-article-end  (TC-12)
**Status:** GENERATED, PASSING (last full pass 2026-11-16/17).  
**File:** `flows/android/TC12_functional_scroll_to_article_end.yaml`  
**Tags:** regression, functional, article  
**Purpose / expected:** Scrolling a long article reaches the end of the page (footer license + browser link).  
**Page objects:** search_enter_query, search_open_top_result, article_assert_loaded, article_scroll_to_end, app_assert_no_crash

## Traceability

| Ticket | Scenario |
|---|---|
| TC-01 | 1.1 |
| TC-02 | 1.2 |
| TC-03 | 1.3 |
| TC-04 | 1.4 |
| TC-05 | 1.5 |
| TC-06 | 1.6 |
| TC-07 | 1.7 |
| TC-08 | 1.8 |
| TC-09 | 1.9 |
| TC-10 | 1.10 |
| TC-11 | 1.11 |
| TC-12 | 1.12 |
