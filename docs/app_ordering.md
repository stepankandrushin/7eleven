# Ordering in the app (7 Delivery)

The 7-Eleven TH app screen by screen: navigation, the launch check, the popups, the search bar, the checkout flow with its resource ids and bounds, and the complete order checklist with the pitfalls. AGENTS.md keeps the rules in short; how to find what to tap and the ADB commands themselves are in adb_automation.md.

## 7-Eleven App

The package name, the launch command and the two activities are in AGENTS.md.

### App Navigation

1. Launch app → lands on **app home** with icons for "7 Delivery", "ALL ONLINE", etc.
2. Tap **"7 Delivery"** / "สั่งเลย" to enter the delivery ordering section
3. First launch asks for **location permission** — grant "While using the app" (use precise location)
4. Inside 7 Delivery: search bar at top, "Delivery" / "Pick-up" tabs, banners, categories

## Launching the App — Always Verify Focus

After launching with `monkey`, the app may occasionally land on the **Play Store page** instead of the app itself. **Always check `mCurrentFocus`** after launch:

```bash
adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1
sleep 5
adb shell dumpsys window | grep mCurrentFocus
```

- If it shows a Play Store activity → use `python3 find_element.py "What cell is the Open button?"` to find and tap it
- Expected: `MainActivity` for app home, `SevenNowLandingActivity` for 7 Delivery

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

## 7 Delivery Search Bar — How to Use

1. Use `python3 find_element.py "What cell is the center of the search bar?"` to find and tap the search bar (asking for "center" avoids the model returning a cell at the left edge, which may not activate the field)
2. **Type your query** with `adb shell input text "query"` — do NOT press Enter/keyevent 66 (it doesn't submit the search in this field)
3. **Search suggestions appear below** — use `python3 find_element.py "What cell is the first search suggestion?"` to find and tap suggestions. Always verify the result with a screenshot after tapping.

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
