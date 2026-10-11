# Driving the phone over ADB

How the phone is driven, whatever the task: the grid vision scripts that find what to tap, how to ask phone_status.py a question, the Verify-Act-Verify loop with its standard workflow, and the ADB commands with the long form of the input traps. AGENTS.md keeps the rules in short; the steps of an order in the app are in app_ordering.md.

## ADB Tap Coordinates — Grid Vision Method

The two rules of this method (never estimate coordinates from a screenshot, never read a screenshot PNG directly) and the short list of the scripts are in AGENTS.md.

### How it works

The vision model is configured via `VISION_MODEL` in `.env` (fallback: `gemma-4-26B-A4B-it-uncensored-heretic-Q8_0.gguf`). The server it is asked on is `VISION_API_URL`, an OpenAI-compatible endpoint (fallback: `http://localhost:8020/v1`).

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

## Asking Questions to phone_status.py

When using `phone_status.py` for verification, follow these guidelines:

- **Ask standalone questions** — don't assume context from previous calls. Each call is independent.
- **Bad**: `"Is the popup gone now?"` — implies temporal context the model may not have.
- **Good**: `"Is there a popup on screen?"` / `"What's on screen?"` / `"What page am I on?"`
- **Combine open-ended + specific**: `"What's on screen? Is the 7 Delivery button visible and tappable?"` — gives full context plus the specific answer you need.
- **Open-ended is often better**: `"What's on screen?"` gives a full picture and lets you decide next steps.

## Verify-Act-Verify Workflow

The rule that all ADB automation follows this loop, and the Key Rules of the loop, are in AGENTS.md.

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
