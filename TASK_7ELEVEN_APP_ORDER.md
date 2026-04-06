# Task: Order Evian Water via 7-Eleven App (Android/ADB)

## Goal
Order 3 cases (36 bottles) of Evian water through the **7-Eleven TH mobile app** on a Samsung Android phone connected via ADB, delivered to home address with **cash on delivery (เก็บเงินปลายทาง)**.

Prefer Evian 1L if available. Fallback: Evian 750ml Sport Cap, case of 12 (product code 420672010, ~895 THB/case).

## Before You Start

1. **Read CLAUDE.md** — it has all ADB automation instructions, UI Automator usage, popup handling, etc.
2. **Check ADB connection**: `adb devices` (must show "device", not "unauthorized")
3. **Get screen resolution**: `adb shell wm size && adb shell wm density`

## App Details

- **Package**: `asuk.com.android.app`
- **Launch**: `adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1`
- **Force stop**: `adb shell am force-stop asuk.com.android.app`

## Critical Rules

1. **NEVER guess tap coordinates from screenshots.** Always use UI Automator dump to get exact bounds, then tap center. See CLAUDE.md for details.
2. **Campaign popups appear frequently** — detect with `wc -c` on UI dump (~2845 bytes = popup). Dismiss with `adb shell input keyevent 4` (back button).
3. **Always verify state** after each action: dump UI or take screenshot.

## Account

- Email: your@email.com
- Login uses OTP sent to email — retrieve with `python3 check_email.py 1`
- OTP sender: noreply@7eleven.co.th
- Account name: Your Name
- Phone: 0XXXXXXXXX

## Delivery Address

```
<house no>, <building>, หมู่ <moo>, <sub-district>, <district>, <province>, <postcode>
```
GPS: `<latitude>, <longitude>`

## Nearest Store

- `<favorite store>` (saved as favorite)

## Payment

**Cash on delivery (เก็บเงินปลายทาง)** — this is only available in the app, not the website.

## Steps

1. Launch 7-Eleven app
2. Dismiss any campaign popups (back button)
3. From app home, tap **"7 Delivery"** / "สั่งเลย" to enter delivery section
4. Dismiss any more popups
5. Search for "evian" or "เอเวียง"
   - Previous attempt: searching "evian" in 7 Delivery returned empty. Try "เอเวียง" (Thai name), or browse water categories, or try **ALL ONLINE** section instead
6. Check if 1L is available — if yes, order 3 cases; if no, order 3 cases of 750ml
7. Set delivery address (should be saved already) with GPS coordinates
8. Select **cash on delivery** payment
9. Confirm and place order
10. Report order number and expected delivery date

## Known Issues & Learnings

- ~~Searching "evian" in 7 Delivery returned **no results**~~ **RESOLVED**: Typing "evian" shows autocomplete suggestions including "เอเวียง". Tap the suggestion (not Enter) to search. Evian IS available in 7 Delivery.
- **Evian products available in 7 Delivery** (as of 2026-04): Evian 1L (~65 Baht), Evian 500ml (~48 Baht), Evian 500ml case (1,080 Baht, Coming Soon), Evian Sparkling 330ml 4-pack (210 Baht, Coming Soon)
- **Stock limit**: Evian 1L had max 19 units available (store inventory based). The +/- quantity selector silently caps at available stock.
- The app shows campaign popups constantly — on launch, when entering sections, after dismissing one another may appear. Always check UI dump size before interacting.
- The 7 Delivery activity (`SevenNowLandingActivity`) cannot be launched directly via `am start` (not exported). Must navigate through the app home.
- First time entering 7 Delivery triggers a **location permission** dialog — grant "While using the app" with precise location.
- If COD is not available in ALL ONLINE, go back to 7 Delivery and try browsing categories instead of search.

## Context

- The ALL Online **website** does NOT support cash on delivery — that's why we use the app
- Shipping should be ~100 THB or free for home delivery
- Max 5 cases per product per day per member
