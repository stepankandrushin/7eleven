# 7-Eleven App Automation via ADB

## Device & Screen

- **Phone**: Connected via USB/ADB
- **Get screen info before each run**:
  ```bash
  adb shell wm size && adb shell wm density
  ```

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

## ADB Tap Coordinates — CRITICAL

**Screenshots are scaled down when displayed.** The actual screen is 904x2316, but the screenshot image appears smaller. **NEVER estimate coordinates from the visual screenshot.** Always use one of these methods:

### Method 1: UI Automator (preferred)

```bash
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml /tmp/ui.xml
```

Then parse the XML to find the element's `bounds="[left,top][right,bottom]"` and tap the center:

```bash
# For bounds [624,698][716,751]:
# center_x = (624+716)/2 = 670, center_y = (698+751)/2 = 725
adb shell input tap 670 725
```

**Common issues with UI Automator:**
- `ERROR: could not get idle state` — the UI is still animating/loading. Wait a few seconds and retry.
- Very small XML output (~2845 bytes) — usually means a **popup overlay** is blocking the real UI. Dismiss the popup first.

### Method 2: Extract text and bounds together

```bash
grep -o 'text="[^"]*"\|content-desc="[^"]*"\|bounds="[^"]*"' /tmp/ui.xml | paste - - - | grep -i "keyword"
```

This finds elements by text content and gives their exact bounds for tapping.

### Why clicks miss

1. **Screenshot scaling**: The screenshot PNG is 904x2316 pixels but when viewed, your visual estimate of "where" something is gets scaled. A button that looks like it's at (200, 250) in the image viewer might actually be at (600, 750) in real screen coordinates.
2. **Popups/overlays**: Invisible campaign popups intercept all taps even when they appear transparent. The UI automator dump will show only the popup elements (small XML ~2845 bytes) instead of the real page.
3. **Wrong coordinate space**: Always use the actual 904x2316 coordinate space, not a scaled-down version.

**Rule: ALWAYS dump UI Automator XML and read the `bounds` attribute before tapping. Never guess coordinates from screenshots.**

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

### Popup loop

After dismissing a popup, the app may show another one. Always re-check with `uiautomator dump` + `wc -c` before proceeding.

## Standard Workflow

```bash
# 1. Launch app
adb shell monkey -p asuk.com.android.app -c android.intent.category.LAUNCHER 1

# 2. Wait for load
sleep 5

# 3. Dismiss any popup
adb shell input keyevent 4
sleep 2

# 4. Dump UI and find elements
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml /tmp/ui.xml

# 5. Find element by text
grep -o 'text="[^"]*"\|bounds="[^"]*"' /tmp/ui.xml | paste - - | grep "7 Delivery"

# 6. Tap center of bounds
adb shell input tap <center_x> <center_y>

# 7. Take screenshot to verify
adb shell screencap -p /sdcard/screen.png && adb pull /sdcard/screen.png /tmp/screen.png
```

## Other ADB Commands

```bash
# Type text
adb shell input text "evian"

# Press Enter/Search
adb shell input keyevent 66

# Press Back
adb shell input keyevent 4

# Press Home
adb shell input keyevent 3

# Swipe (scroll down)
adb shell input swipe 452 1500 452 500

# Check foreground app
adb shell dumpsys window | grep mCurrentFocus

# Force stop app
adb shell am force-stop asuk.com.android.app
```

## Email (IMAP)

The user's email is `your@email.com`, accessed via IMAP (not Gmail). Credentials and connection details are in `.env` (see `.env.sample` for the format).

```bash
python3 check_email.py       # latest 5 emails
python3 check_email.py 10    # latest 10 emails
```

OTP sender: `noreply@7eleven.co.th`, subject contains "แจ้งรหัสเพื่อยืนยัน"

## Web Ordering Reference

For ordering via the ALL Online website (Chrome + CDP), see docs/web_ordering.md. Note: the website does **NOT** support cash on delivery — that's why we use the app.

Also see docs/7eleven_order_findings.md for general product/store details.
