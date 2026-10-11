# 7-Eleven App Automation via ADB

Orders in the 7-Eleven TH app (7 Delivery) on an Android phone, driven over ADB with a vision model that finds what to tap. The app and not the ALL Online website, because the website does **NOT** support cash on delivery.

This file holds the rules and traps in short; the procedures, examples and tables are in docs/, listed at the end with when to read each.

## Device & Screen

- **Phone**: Connected via USB/ADB

## 7-Eleven App

- **Package name**: `asuk.com.android.app`
- **App name on Play Store**: 7-Eleven TH (by CP ALL PUBLIC COMPANY LIMITED)
- **Launch**: `adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1`
- **Main activity**: `net.appsynth.allmember.main.presentation.main.MainActivity`
- **7 Delivery activity**: `net.appsynth.allmember.sevennow.presentation.landing.SevenNowLandingActivity` (not exported — cannot launch directly via `am start`)
- **Navigation**: from the app home tap "7 Delivery" / "สั่งเลย"; the first launch asks for location permission: grant "While using the app" (use precise location).

## ADB Tap Coordinates — Grid Vision Method

**NEVER estimate coordinates from screenshots visually.** Use the grid-based vision method to get accurate click coordinates.

**NEVER read screenshot PNGs directly** (any file under `screenshots/`, including `_grid.png` overlays). Multimodal hosts that ingest the raw image cannot reliably resolve grid cells or pixel coordinates. Always go through our scripts:

- `phone_status.py` — "what's on screen" (description)
- `find_element.py` — "where is X" (returns cell + `(x, y)` pixel coords)
- `grid.py <path>` — overlays the labeled grid on an existing screenshot (used by `find_element.py`; not a substitute for it)
- `cell2coords.py <cell>` — converts a cell ref like `D12` into pixel coords

This rule applies to every agent operating in this repo (Claude Code, `.pi`, and any other CLI assistant).

- The vision model and the server it is asked on are `VISION_MODEL` and `VISION_API_URL` in `.env`.
- **Wide elements (search bars, full-width buttons)**: the vision model tends to return cells at the left edge of them, so always ask for "center" in the prompt.
- **Asking Questions to phone_status.py**: ask standalone questions, because each call is independent and has no context from previous calls: "Is there a popup on screen?", not "Is the popup gone now?". Open-ended ("What's on screen?") is often better, alone or combined with the specific question.

## Verify-Act-Verify Workflow

**All ADB automation MUST follow this loop.** Never assume an action succeeded — always verify.

1. **Pre-Action Check**: before any tap/swipe, check with `python3 phone_status.py` that you're on the correct page and no overlays are blocking the UI.
2. **Precise Action**: the ADB command (tap, swipe, text input, etc.).
3. **Post-Action Verification**: immediately verify the intended effect (the quantity actually increased, the next screen loaded).
4. **Error Handling**: if the state didn't change or a popup appeared, resolve the issue before retrying. Do NOT blindly repeat actions.

### Key Rules

- **Never chain multiple taps without verifying each one.** Each action gets its own verify step.
- **Quantity changes**: Always verify the displayed number after each +/- tap. The app may silently cap at stock limits.
- **Page transitions**: After tapping a navigation button, verify you landed on the expected page before proceeding.
- **Use `phone_status.py`** for verification (detailed description), **`find_element.py`** for finding coordinates to tap.

## Popups

- **Google Play Update Popup**: appears frequently when launching or navigating the app; a system-level overlay (package `com.android.vending`) that blocks all taps on the app. When it appears, **update the app** by tapping the "Update" button, found with `find_element.py`.
- **Campaign Popups**: shown frequently (on launch, when entering 7 Delivery, etc.); modal overlays that intercept all taps. Detect with `uiautomator dump` + `wc -c`: ~2845 bytes = popup is showing, 10KB+ = real page content. Dismiss with the Android back button, `adb shell input keyevent 4`; if back also dismisses the page, tap the center of the `cancelButton` bounds from the UI dump.
- **Post-order popups (back button does NOT work)**: the promotion popup over the order tracking page goes only by tapping its `closeButton`. Do not tap its `goToLinkButton` (ช้อปเลย / Shop now).
- **Popup loop**: after dismissing a popup the app may show another one, so always re-check with `uiautomator dump` + `wc -c` before proceeding.

## Other ADB Commands

- **`adb shell input text` — Spaces**: `adb input text` splits on spaces, so `"My Building"` only types "My". Use `%s`: `adb shell input text "My%sBuilding%s12"`. Never type multi-word text without `%s` — this is the #1 cause of corrupted text input.
- **Swipe — Drag vs Fling**: a fast swipe (default ~350ms) is a fling and may not register near scroll boundaries; a slow swipe (1000ms+) is a 1:1 drag. Near the top/bottom of a scrollable area always use a slow swipe: `adb shell input swipe 452 1500 452 1000 1000`.
- **Dismissing the Keyboard — Don't Tap Randomly**: never tap at `(100, 200)` — that's the back button area (`[0,87][126,213]`), which navigates away from the current page. Use `adb shell input keyevent 4` (Back), and dismiss the keyboard BEFORE swiping, because the keyboard corrupts text on swipe. Verify text input WITHOUT tapping "outside" first: check the field value with `uiautomator dump`.
- **EditText Hint Text vs Actual Value**: hint text (e.g. "Room number 711" in the Address details field) is not real content, so don't try to delete it: just type. Real content is deleted character-by-character with `adb shell input keyevent 67` (backspace, 200ms between each), then verified with `uiautomator dump` before typing new text.

## Launching the App — Always Verify Focus

After launching with `monkey`, the app may occasionally land on the **Play Store page** instead of the app itself. **Always check `mCurrentFocus`** after launch (`adb shell dumpsys window | grep mCurrentFocus`): expected is `MainActivity` for app home, `SevenNowLandingActivity` for 7 Delivery; on a Play Store activity find and tap the "Open" button.

## 7 Delivery Search Bar

Ask `find_element.py` for the **center** of the search bar (a cell at the left edge may not activate the field), type the query, and do NOT press Enter/keyevent 66: it doesn't submit the search in this field. Tap a search suggestion below instead and verify the result.

## Checkout Flow (7 Delivery)

- **Verify Packaging**: before adjusting quantity (+/-), check if the product is a single item or a pack/case ("Pack", "Case", "ลัง" (Case), "แพ็ก" (Pack) in the product title and image). `(Quantity selected) * (Items per pack)` must equal the requested amount before adding to the basket.
- **Product Quantity Limits**: the +/- selector has a stock-based maximum and the app silently caps at available inventory, so verify the final quantity in the basket.
- **Cash is NOT default**: TrueMoney Wallet (Pay now) is pre-selected. The payment options are below the initial view of the Order Summary, reached with slow swipes; tap the Cash cardview and verify `selectedCheckBoxView` inside it in the UI dump.
- **"Place order" tap misses**: the button center is `(452, 1907)`, not the bottom of the screen. After it wait ~10 seconds for the order tracking page.

## Email (IMAP)

The user's email is `your@email.com`, accessed via IMAP (not Gmail). Credentials and connection details are in `.env` (see `.env.sample` for the format).

```bash
python3 check_email.py       # latest 5 emails
python3 check_email.py 10    # latest 10 emails
```

OTP sender: `noreply@7eleven.co.th`, subject contains "แจ้งรหัสเพื่อยืนยัน"

## Docs

- docs/adb_automation.md — read before the first tap of a session, and when a tap, a swipe or typed text did not do what was expected: how the four scripts work (the grid, the screenshot paths), the quick and the manual method, the loop with its examples and the standard workflow from launch to a verified tap, the ADB commands with the long form of the four input traps, how to phrase a question to `phone_status.py`.
- docs/app_ordering.md — read before placing an order in the app, and when a screen is not the expected one: app navigation, the launch check, the commands that detect and dismiss each popup, the search bar, the checkout flow step by step with resource ids and bounds, the payment options, the complete order checklist and the table of pitfalls.
- docs/web_ordering.md — for ordering via the ALL Online website (Chrome + CDP).
- docs/7eleven_order_findings.md — general product/store details.
- HISTORY.md — what was done when; not loaded at the start of a session.

**Keep this file under 12 KB**: every session loads it whole. A new rule or trap goes here in a line or two with its reason, its procedure and examples into docs/, what was done when into HISTORY.md.
