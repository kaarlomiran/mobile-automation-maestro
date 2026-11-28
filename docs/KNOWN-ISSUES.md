# Known issues

Defects and limitations found by the suite. Per-run evidence is in `runs/issues/<RUN>/` (local, not committed).

| ID | Platform / device | Test | Type | Issue | Status |
|---|---|---|---|---|---|
| IOS-01 | iOS 27.2, iPad Pro 11-inch | TC04 | App defect | App aborts on **Save**: assertion in `-[WMFArticle isAnyVariantSaved]` (`WMFArticle+Extensions.m:34`, "More than one article variant marked as saved") during the CoreData save. 1 of 2 attempts, Debug build | Open, raise with app team |
| IOS-02 | iOS, iPad | TC04 | Test gap | The iPad article screen has no home ("W") button used by `article_close` | Open, page object to be adapted |
| IOS-03 | iOS, iPad | TC05 | Undetermined | After hiding the Contents sidebar, tapping the Contents button does not show it again | Open, needs a manual check |
| IOS-04 | iOS 26.5 and 27.2 | TC01 | Undetermined (app or driver) | After onboarding **Skip**, Home and the tab bar show but the buttons are reported without their `Root Tab …` ids; the page object relaunches the app. (Earlier "empty screen" description was wrong.) | Worked around; try matching labels |
| IOS-05 | iOS 27.2, iPhone | TC04, TC05 | Possible app issue | Stopping the app seconds after **Skip** showed onboarding again | Observed in one run; raise with app team |
| IOS-06 | iOS 27.2, iPhone | TC01 | Undetermined, not investigated | The end screenshot shows Home with the tabs and **Community / For You** but an empty feed area (seen in every passing iPhone TC01 screenshot of 2026-11-25 to 11-27). TC01 asserts the tabs, not feed content | Open |
| AND-01 | Android 17 | TC12 | Limitation | Off-screen article text is in the accessibility tree, so the footer assertion cannot prove position; check the end screenshot | Documented in the page object |
| ENV-01 | Android emulator on the local Mac | Several | Environment | With the AVD's default software graphics the emulator stayed overloaded: driver start-up timeouts, 120 s device timeouts, tests stuck on onboarding (runs of 2026-11-26, 9/12 and 1/12) | Fixed 2026-11-27: `run-matrix.sh` uses hardware graphics on macOS, start-up timeout raised to 90 s; 12/12 on phone-small and tablet |
