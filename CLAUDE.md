# 7-Eleven App Automation via ADB

## Device & Screen

- **Phone**: Connected via USB/ADB

## 7-Eleven App

- **Package name**: `asuk.com.android.app`
- **App name on Play Store**: 7-Eleven TH (by CP ALL PUBLIC COMPANY LIMITED)
- **Launch**: `adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1`
- **Main activity**: `net.appsynth.allmember.main.presentation.main.MainActivity`
- **7 Delivery activity**: `net.appsynth.allmember.sevennow.presentation.landing.SevenNowLandingActivity` (not exported — cannot launch directly via `am start`)

### App Navigation

1. Launch app → lands on **app home** with icons for "7 Delivery", "ALL ONLINE", etc.
2. Tap **"7 Delivery"** / "สั่งเลย" to enter the delivery ordering section
3. First launch asks for **location permission** — grant "While using the app" (use precise location)
4. Inside 7 Delivery: search bar at top, "Delivery" / "Pick-up" tabs, banners, categories

## ADB Tap Coordinates — Grid Vision Method

**NEVER estimate coordinates from screenshots visually.** Use the grid-based vision method to get accurate click coordinates.

**NEVER read screenshot PNGs directly** (any file under `screenshots/`, including `_grid.png` overlays). Multimodal hosts that ingest the raw image cannot reliably resolve grid cells or pixel coordinates. Always go through our scripts:

- `phone_status.py` — "what's on screen" (description)
- `find_element.py` — "where is X" (returns cell + `(x, y)` pixel coords)
- `grid.py <path>` — overlays the labeled grid on an existing screenshot (used by `find_element.py`; not a substitute for it)
- `cell2coords.py <cell>` — converts a cell ref like `D12` into pixel coords

This rule applies to every agent operating in this repo (Claude Code, `.pi`, and any other CLI assistant).

### How it works

The vision model is configured via `VISION_MODEL` in `.env` (fallback: `gemma-4-26B-A4B-it-uncensored-heretic-Q8_0.gguf`).

Four scripts in the project directory handle coordinate finding and screen inspection:

1. **`grid.py <path>`** — Overlays a labeled 64px grid on the given screenshot, saves as `<stem>_grid.png` next to it. Columns labeled A–N at the bottom, rows 1–36 on the left.
2. **`find_element.py "<question>"`** — Automated: takes a timestamped screenshot under `screenshots/YYYY-mm-dd/`, generates the grid alongside it, sends it to the vision model, and returns the cell + pixel coordinates.
3. **`cell2coords.py <cell>`** — Converts a cell reference (e.g. `D12`) to center pixel `(x, y)` on the original 904x2316 screen.
4. **`phone_status.py [optional prompt]`** — Takes a timestamped screenshot under `screenshots/YYYY-mm-dd/` (no grid) and sends it to the vision model for a detailed description of the current screen state. Use this for verifying what's on screen before/after actions. Supports an optional extra prompt for specific questions.

All screenshots are saved to `screenshots/YYYY-mm-dd/screen-YYYY-mm-dd-HH-mm-ss-msc.png` (millisecond suffix) so each capture is preserved — nothing overwrites the previous shot.

```bash
# Describe current screen
python3 phone_status.py

# Ask a specific question about the screen
python3 phone_status.py "Is there a popup showing?"
python3 phone_status.py "What is the quantity displayed?"
```

### Wide elements (search bars, full-width buttons)

The vision model tends to return cells at the **left edge** of wide UI elements. For these, always ask for "center" in the prompt: `"What cell is the center of the Add to basket button?"`

### Quick method (automated — preferred)

```bash
# 1. Ask the vision model (takes screenshot automatically)
python3 find_element.py "What cell is the 7 Delivery button?"
# Output: Cell F5 -> click at (352, 288)

# 2. Tap the coordinates
adb shell input tap 352 288
```

### Manual method

Screenshots are saved to a dated folder with a timestamped filename so each capture is preserved (no overwrites). Path format: `screenshots/YYYY-mm-dd/screen-YYYY-mm-dd-HH-mm-ss-msc.png` (the `msc` suffix is milliseconds).

```bash
# 1. Take screenshot (timestamped, into dated folder)
# macOS `date` lacks `%N`, so build the millisecond suffix in Python.
TS=$(python3 -c 'from datetime import datetime as d; n=d.now(); print(n.strftime("%Y-%m-%d-%H-%M-%S-")+f"{n.microsecond//1000:03d}")')
DAY=${TS:0:10}
mkdir -p "screenshots/$DAY"
SHOT="screenshots/$DAY/screen-$TS.png"
DEV="/sdcard/screen-$TS.png"
adb shell screencap -p "$DEV" && adb pull "$DEV" "$SHOT" && adb shell rm -f "$DEV"

# 2. Generate grid overlay (writes <stem>_grid.png next to the input)
python3 grid.py "$SHOT"

# 3. View "screenshots/$DAY/screen-${TS}_grid.png" to identify the cell visually
#    (e.g. screenshots/2026-04-25/screen-2026-04-25-14-23-09-456_grid.png)

# 4. Get coordinates
python3 cell2coords.py D12
# Output: (224, 736)

# 5. Tap
adb shell input tap 224 736
```

## Google Play Update Popup

A **Google Play update popup** appears frequently when launching or navigating the app. It is a **system-level overlay** (package `com.android.vending`) that blocks all taps on the app.

When the popup appears, **update the app** by tapping the "Update" button.

### How to detect

Use `phone_status.py` — it will describe it as a "Google Play update notification" overlay.

### How to update

Use `find_element.py` to locate the Update button:

```bash
python3 find_element.py "What cell is the Update button?"
# Then tap the returned coordinates
```

## Campaign Popups

The app shows campaign/promotion popups frequently (on launch, when entering 7 Delivery, etc.). These are modal overlays that intercept all taps.

### How to detect popups

```bash
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml /tmp/ui.xml && wc -c /tmp/ui.xml
```

- **~2845 bytes** = popup is showing (only the overlay is in the UI tree)
- **Large file (10KB+)** = real page content is visible

### How to dismiss popups

**Method 1 (best)**: Press the Android back button:

```bash
adb shell input keyevent 4
```

**Method 2**: Find and tap the X/cancel button from UI dump:

```bash
# The popup typically has: resource-id="asuk.com.android.app:id/cancelButton"
# with an ImageView X icon inside. Get bounds from XML and tap center.
grep "cancelButton" /tmp/ui.xml  # find bounds
```

**Method 3**: If back button also dismisses the page, find the `cancelButton` bounds from the UI dump and tap the center of those bounds.

### Post-order popups (back button does NOT work)

After placing an order, a promotion popup appears over the order tracking page. Unlike other popups, **the back button does not dismiss it**. You must find and tap the `closeButton`:

```bash
grep "closeButton" /tmp/ui.xml | grep -o 'bounds="[^"]*"'
# Then tap the center of those bounds
```

This popup also has `resource-id="asuk.com.android.app:id/goToLinkButton"` (ช้อปเลย / Shop now) — do not tap that.

### Popup loop

After dismissing a popup, the app may show another one. Always re-check with `uiautomator dump` + `wc -c` before proceeding.

## Verify-Act-Verify Workflow

**All ADB automation MUST follow this loop.** Never assume an action succeeded — always verify.

### The Loop

1. **Pre-Action Check**: Before any tap/swipe, check the current screen to confirm you're on the correct page and no overlays are blocking the UI.
   ```bash
   python3 phone_status.py  # or with a specific question
   ```
2. **Precise Action**: Perform the ADB command (tap, swipe, text input, etc.).
3. **Post-Action Verification**: Immediately verify the action had the intended effect (e.g., if you tapped "+", verify the quantity actually increased; if you tapped a button, verify the next screen loaded).
   ```bash
   python3 phone_status.py "Did the quantity increase?"
   ```
4. **Error Handling**: If the state didn't change or a popup appeared, resolve the issue before retrying. Do NOT blindly repeat actions.

### Standard Workflow (with Verify-Act-Verify)

```bash
# 1. Launch app
adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1
sleep 5

# 2. VERIFY: Check what's on screen (popup? Play Store? correct page?)
adb shell dumpsys window | grep mCurrentFocus
python3 phone_status.py "Is there a popup or overlay showing?"

# 3. Handle popups if present
adb shell input keyevent 4
sleep 2
python3 phone_status.py  # verify popup is gone

# 4. Find element and get coordinates
python3 find_element.py "What cell is the 7 Delivery button?"

# 5. ACT: Tap the returned coordinates
adb shell input tap <x> <y>
sleep 2

# 6. VERIFY: Confirm the tap worked
python3 phone_status.py "Am I on the 7 Delivery page?"
```

### Key Rules

- **Never chain multiple taps without verifying each one.** Each action gets its own verify step.
- **Quantity changes**: Always verify the displayed number after each +/- tap. The app may silently cap at stock limits.
- **Page transitions**: After tapping a navigation button, verify you landed on the expected page before proceeding.
- **Use `phone_status.py`** for verification (detailed description), **`find_element.py`** for finding coordinates to tap.

## Other ADB Commands

```bash
# Type text (use %s for spaces!)
adb shell input text "My%sBuilding%s12"  # → "My Building 12"

# Press Enter/Search
adb shell input keyevent 66

# Press Back
adb shell input keyevent 4

# Press Home
adb shell input keyevent 3

# Swipe — SLOW for small movements (drag), FAST for fling
# Slow swipe (precise scroll — interpreted as 1:1 drag):
adb shell input swipe 452 1500 452 1000 1000  # 1000ms duration = drag
# Fast swipe (momentum scroll / fling — needs runway):
adb shell input swipe 452 1500 452 500         # default ~350ms = fling

# Check foreground app
adb shell dumpsys window | grep mCurrentFocus

# Force stop app
adb shell am force-stop asuk.com.android.app
```

### `adb shell input text` — Spaces
- **`adb input text` splits on spaces** — `adb shell input text "My Building"` only types "My".
- **Use `%s` for spaces**: `adb shell input text "My%sBuilding%s12"` → types "My Building 12".
- **Never type multi-word text without `%s`** — this is the #1 cause of corrupted text input.

### Swipe — Drag vs Fling
- **Fast swipe** (default ~350ms) = **fling** (momentum scroll). Needs room to build up speed. Near scroll boundaries, the fling may not register.
- **Slow swipe** (1000ms+) = **drag** (1:1 finger-follow). Use for small, precise scroll adjustments.
- **Rule**: When near the top/bottom of a scrollable area, always use slow swipe (`1000` duration).

### Dismissing the Keyboard — Don't Tap Randomly
- **Never tap at `(100, 200)` to dismiss the keyboard** — that's the **back button** area (`[0,87][126,213]`), which navigates away from the current page.
- **Use `adb shell input keyevent 4` (Back)** to dismiss the keyboard — it closes the keyboard without leaving the page (unless the field was the only focus target).
- **Verify text input WITHOUT tapping** — after typing, use `uiautomator dump` directly to check the field value. Don't tap "outside" first.

### EditText Hint Text vs Actual Value
- EditText fields show **hint/placeholder text** (e.g. "Room number 711" in the Address details field) when empty.
- **Don't try to delete hint text** — it's not real content. Just type directly; your input replaces the hint.
- If the field already has real content, delete it character-by-character with `adb shell input keyevent 67` (backspace, 200ms between each), then verify with `uiautomator dump` before typing new text.

## Email (IMAP)

The user's email is `your@email.com`, accessed via IMAP (not Gmail). Credentials and connection details are in `.env` (see `.env.sample` for the format).

```bash
python3 check_email.py       # latest 5 emails
python3 check_email.py 10    # latest 10 emails
```

OTP sender: `noreply@7eleven.co.th`, subject contains "แจ้งรหัสเพื่อยืนยัน"

## 7 Delivery Search Bar — How to Use

1. Use `python3 find_element.py "What cell is the center of the search bar?"` to find and tap the search bar (asking for "center" avoids the model returning a cell at the left edge, which may not activate the field)
2. **Type your query** with `adb shell input text "query"` — do NOT press Enter/keyevent 66 (it doesn't submit the search in this field)
3. **Search suggestions appear below** — use `python3 find_element.py "What cell is the first search suggestion?"` to find and tap suggestions. Always verify the result with a screenshot after tapping.

## Launching the App — Always Verify Focus

After launching with `monkey`, the app may occasionally land on the **Play Store page** instead of the app itself. **Always check `mCurrentFocus`** after launch:

```bash
adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1
sleep 5
adb shell dumpsys window | grep mCurrentFocus
```

- If it shows a Play Store activity → use `python3 find_element.py "What cell is the Open button?"` to find and tap it
- Expected: `MainActivity` for app home, `SevenNowLandingActivity` for 7 Delivery

## Checkout Flow (7 Delivery)

### Product Quantity & Packaging
- **Verify Packaging**: Before adjusting quantity (+/-), always check if the product is a single item or a pack/case.
- **Read Labels Carefully**: Look for keywords like "Pack", "Case", "ลัง" (Case), or "แพ็ก" (Pack) in the product title and image.
- **Calculate Total**: Ensure the `(Quantity selected) * (Items per pack)` equals the requested amount before adding to the basket.

### Order Flow Steps

1. **Product page**: Set quantity with +/- buttons, tap "Add to basket X.XX Baht"
2. **Search results**: Bottom bar shows basket count and "View basket" button → tap it
3. **Basket page**: Shows items, subtotal, total → tap "Next" (button `resource-id=asuk.com.android.app:id/cartOrderButton`, bounds `[53,2011][851,2103]`)
4. **Order summary** (`OrderSummaryActivity`):
   - **Address details field** (`resource-id=asuk.com.android.app:id/addressDetailEditText`): Shows hint text "Room number 711" when empty. **Tap to focus, type directly** (hint is not real content). Use `adb shell input text "My%sBuilding%s12"` with `%s` for spaces.
   - **Note to driver field** (`resource-id=asuk.com.android.app:id/valueEditText` under "Note to driver" title): Separate from Address details.
   - **Scroll down** to see product list, delivery time ("Now" / "Schedule"), coupons, payment options. The RecyclerView needs **slow swipes** (`1000ms duration`) to reveal content below the initial view:
     ```bash
     adb shell input swipe 452 1500 452 1000 1000
     ```
   - After scrolling, tap "Next" (`resource-id=asuk.com.android.app:id/placeOrderButton`, bounds `[42,2032][862,2103]`)
5. **Confirmation page** (bottom sheet overlay):
   - Shows: Payment method, Subtotal, Delivery fee, Discounts, Coupon/Promotion code, Net price
   - **"Place order" button** (`resource-id=asuk.com.android.app:id/confirmButton`, bounds `[32,1833][872,1980]`, center ≈ `452, 1907`)
   - **"Back" button** (`resource-id=asuk.com.android.app:id/cancelButton`, bounds `[32,1980][872,2103]`)
6. **Processing** (`OrderTrackingLoadingActivity`): "Please wait a moment... Sending orders to the store" — wait ~10 seconds
7. **Order tracking** (`OrderTrackingActivity`): Status flow (Awaiting order → Preparing → Preparing complete → On delivery → Delivered). Post-order promotion popup appears — dismiss with `closeButton` (NOT back button).

### Payment Options (in Order Summary)

The Order Summary page has a **long RecyclerView**. Initial view shows only up to "Delivery now" / "Schedule" section. **Payment options are below** — scroll with slow swipes:

```bash
# Slow swipe to reveal payment options (1000ms = drag)
adb shell input swipe 452 1500 452 1000 1000
adb shell input swipe 452 1500 452 1000 1000
```

Payment structure:
- **Pay now**: TrueMoney Wallet
- **Pay on Delivery**:
  - **Cash** — "Cash on delivery" (has `selectedCheckBoxView` when checked)
  - **TrueMoney Wallet** — "Pay by TrueMoney Wallet on delivery"

**Default selection**: TrueMoney Wallet (Pay now) is pre-selected. Tap the Cash cardview to switch.

**Verify selection**: Check for `selectedCheckBoxView` inside the Cash cardview in the UI dump:
```bash
grep "selectedCheckBoxView" /tmp/ui.xml  # present = Cash is selected
```

**Bottom bar** (always visible after scroll): `Subtotal 4,498.00 Baht` + `Exclude coupon discount and delivery fee` + **Next** button.

### Product Quantity Limits

The +/- quantity selector has a **stock-based maximum**. The app silently caps at available inventory. Check the product page text "Available units might vary upon the remaining stock" and verify final quantity in the basket.

## Web Ordering Reference

For ordering via the ALL Online website (Chrome + CDP), see docs/web_ordering.md. Note: the website does **NOT** support cash on delivery — that's why we use the app.

Also see docs/7eleven_order_findings.md for general product/store details.

## Asking Questions to phone_status.py

When using `phone_status.py` for verification, follow these guidelines:

- **Ask standalone questions** — don't assume context from previous calls. Each call is independent.
- **Bad**: `"Is the popup gone now?"` — implies temporal context the model may not have.
- **Good**: `"Is there a popup on screen?"` / `"What's on screen?"` / `"What page am I on?"`
- **Combine open-ended + specific**: `"What's on screen? Is the 7 Delivery button visible and tappable?"` — gives full context plus the specific answer you need.
- **Open-ended is often better**: `"What's on screen?"` gives a full picture and lets you decide next steps.

---

## Complete Order Checklist (App — 7 Delivery)

Use this as a reference for placing orders efficiently:

### 1. Launch & Navigate
```bash
adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1
sleep 5
adb shell dumpsys window | grep mCurrentFocus  # expect MainActivity
# Handle Play Store popup if needed
# Tap "7 Delivery" button → handle location permission → dismiss campaign popups
```

### 2. Search & Add Products
- Tap search bar (ask for **center** in find_element.py)
- Type query (no Enter needed)
- Tap search suggestion
- On product page: set quantity with +/-, verify displayed number, tap "Add to basket"
- Repeat for each product

### 3. Basket → Next
- On search results: tap "View basket" (bottom bar)
- Basket page: verify items, tap "Next" (`cartOrderButton`, `[53,2011][851,2103]`)

### 4. Order Summary — Address Details
- Tap Address details field (`addressDetailEditText`)
- **Type directly** (hint text "Room number 711" is placeholder, not real content)
- Use `%s` for spaces: `adb shell input text "My%sBuilding%s12"`
- **Dismiss keyboard**: `adb shell input keyevent 4` (Back)
- **Verify WITHOUT tapping**: `uiautomator dump` → check field value
- **NEVER tap `(100, 200)` to dismiss keyboard** — that's the back button!

### 5. Order Summary — Scroll to Payment
- Use **slow swipes** (1000ms duration) to reveal payment options:
```bash
adb shell input swipe 452 1500 452 1000 1000
adb shell input swipe 452 1500 452 1000 1000
```
- Payment options appear: Pay now (TrueMoney) / Pay on Delivery (Cash, TrueMoney)
- **Cash is NOT default** — tap Cash cardview to select it
- Verify: `grep "selectedCheckBoxView" /tmp/ui.xml` should show inside Cash cardview

### 6. Order Summary — Tap Next
- "Next" button: `placeOrderButton`, bounds `[42,2032][862,2103]`, center ≈ `(452, 2067)`

### 7. Confirmation — Place Order
- Bottom sheet shows: Payment method, Subtotal, Delivery fee, Net price
- "Place order" button: `confirmButton`, bounds `[32,1833][872,1980]`, center ≈ `(452, 1907)`
- Wait ~10 seconds for `OrderTrackingLoadingActivity`

### 8. Order Tracking
- `OrderTrackingActivity` appears
- Post-order promotion popup: dismiss with `closeButton` (NOT back button)
  ```bash
  grep "closeButton" /tmp/ui.xml | grep -o 'bounds="[^"]*"'
  # Tap center of those bounds
  ```

### Key Pitfalls to Avoid
| Pitfall | Fix |
|---------|-----|
| `adb input text` eats spaces | Use `%s`: `adb shell input text "A%sB%sC"` |
| Tapping `(100,200)` goes back | That's the back button area. Use `keyevent 4` instead |
| Fast swipe doesn't scroll near edges | Use slow swipe: add `1000` duration |
| Deleting hint text in Address details | Don't delete — hint is placeholder. Just type |
| Keyboard corrupts text on swipe | Dismiss keyboard BEFORE swiping |
| Cash payment not selected by default | Explicitly tap Cash cardview |
| "Place order" tap misses | Button center is `(452, 1907)`, not bottom of screen |
