# Chrome Remote Debugging

## Opening Chrome with Debug Port (Default Profile)

Chrome 136+ requires a non-default `--user-data-dir` for remote debugging. The workaround is to create a temporary data directory with symlinks to the real Default profile, so you get full access to cookies, sessions, and extensions.

### Step-by-step

1. **Kill all Chrome processes** (Chrome won't bind the debug port if another instance is running):

```bash
killall "Google Chrome" 2>/dev/null; killall "Google Chrome Helper" 2>/dev/null; sleep 3; kill -9 $(pgrep -f "Google Chrome") 2>/dev/null; sleep 2
```

2. **Create symlinked data dir and launch Chrome:**

```bash
rm -rf /tmp/chrome-debug-real && mkdir -p /tmp/chrome-debug-real && \
ln -sf "$HOME/Library/Application Support/Google/Chrome/Default" /tmp/chrome-debug-real/Default && \
ln -sf "$HOME/Library/Application Support/Google/Chrome/Local State" "/tmp/chrome-debug-real/Local State" && \
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="/tmp/chrome-debug-real" \
  --profile-directory="Default" \
  --remote-debugging-port=9222 \
  2>/dev/null &
```

3. **Verify the debug port is active** (wait a few seconds after launch):

```bash
sleep 5 && curl -s http://localhost:9222/json/version
```

Expected output includes `"Browser": "Chrome/..."` and a `webSocketDebuggerUrl`.

### Other profiles

Replace `"Default"` with the profile directory name (e.g. `"Profile 1"`, `"Profile 2"`). Check `~/Library/Application Support/Google/Chrome/Local State` for the mapping of profile directories to names.

---

## Navigating the DOM via Chrome DevTools Protocol (CDP)

Once Chrome is running with `--remote-debugging-port=9222`, you can control it programmatically.

### Key concepts

- **HTTP API** at `http://localhost:9222`:
  - `/json/version` — browser info and browser-level WebSocket URL
  - `/json/list` — list of all open tabs with their WebSocket URLs
  - `/json/new?url=...` — open a new tab

- **WebSocket API** (CDP): connect to a tab's `webSocketDebuggerUrl` to send commands.

### Common workflow (Python with `websockets`)

```python
import json, asyncio, websockets, urllib.request

async def main():
    # 1. List tabs and find the one you want
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json/list").read())
    page_tab = [t for t in tabs if "example.com" in t.get("url", "")][0]
    ws_url = page_tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        msg_id = 1

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg = {"id": msg_id, "method": method}
            if params:
                msg["params"] = params
            msg_id += 1
            await ws.send(json.dumps(msg))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == msg_id - 1:
                    return resp

        # 2. Navigate to a URL
        await send_cmd("Page.navigate", {"url": "https://example.com"})
        await asyncio.sleep(5)  # wait for page load

        # 3. Run JavaScript in the page context
        resp = await send_cmd("Runtime.evaluate", {
            "expression": "document.title",
            "returnByValue": True
        })
        print(resp["result"]["result"]["value"])

        # 4. Query DOM elements
        resp = await send_cmd("Runtime.evaluate", {
            "expression": """
                JSON.stringify(
                    Array.from(document.querySelectorAll('a'))
                        .map(a => ({text: a.textContent, href: a.href}))
                )
            """,
            "returnByValue": True
        })
        print(json.loads(resp["result"]["result"]["value"]))

asyncio.run(main())
```

### Creating a new tab

```python
# Via HTTP
urllib.request.urlopen("http://localhost:9222/json/new?https://example.com")

# Via browser WebSocket (Target.createTarget)
await send_cmd("Target.createTarget", {"url": "https://example.com"})
```

### Useful CDP methods

| Method | Purpose |
|--------|---------|
| `Runtime.evaluate` | Execute JS in page context — the most versatile tool |
| `Page.navigate` | Navigate to a URL |
| `DOM.getDocument` | Get the DOM tree root |
| `DOM.querySelectorAll` | Find elements by CSS selector |
| `Page.captureScreenshot` | Take a screenshot (base64 PNG) |
| `Network.enable` | Start capturing network requests |
| `Input.dispatchMouseEvent` | Simulate clicks |
| `Input.dispatchKeyEvent` | Simulate keyboard input |

### Tips for finding data in web pages

1. **Start with `Runtime.evaluate`** — it's the easiest way. Write a JS function that uses `document.querySelectorAll()` to find elements, extract `.textContent`, attributes, etc., and return `JSON.stringify(result)`.

2. **Search by text content**: use selectors like `[aria-label*="keyword"]`, `[title*="keyword"]`, or iterate elements and filter by `.textContent.includes("keyword")`.

3. **Search by structure**: inspect class names (e.g. `[class*="RoomTile"]`), roles (`[role="listitem"]`), or data attributes (`[data-testid="..."]`).

4. **Access app-level JS APIs**: many SPAs expose their data model on `window` (e.g. Element/Matrix exposes `window.mxMatrixClientPeg.get()` which gives access to all rooms, messages, members without parsing DOM).

5. **For large results**, use `returnByValue: True` in `Runtime.evaluate` params and always `JSON.stringify()` the result in the JS expression.

### Dependencies

```bash
uv pip install websockets  # Already installed
```

**Tip**: Work step by step interactively. Verify each action works before proceeding to the next step.

---

## Email (IMAP)

The user's email is `your@email.com`, accessed via IMAP (not Gmail). Credentials and connection details are in `.env` (see `.env.sample` for the format).

### Usage

```bash
python3 check_email.py       # latest 5 emails
python3 check_email.py 10    # latest 10 emails
```

---

## 7-Eleven Thailand

See [7eleven_order_findings.md](./7eleven_order_findings.md) for details.

### Login Flow (OTP-based, no password login)

The 7-Eleven ALL Online site uses **email OTP authentication** (not password). The login flow is:

1. Navigate to `https://www.allonline.7eleven.co.th/account/login/`
2. This redirects to `https://allmember-web-ext.cpall.co.th/weblogin/login/email-otp`
3. An OTP is sent to `your@email.com` automatically
4. The page shows 6 individual `<input type="text">` fields for the OTP digits
5. Retrieve the OTP from email (sender: `noreply@7eleven.co.th`, subject contains "แจ้งรหัสเพื่อยืนยัน")
6. Enter OTP digits into the 6 fields using native value setter + input/change events:

```javascript
const inputs = document.querySelectorAll('input[type="text"]');
const otp = '123456';
for (let i = 0; i < 6; i++) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(inputs[i], otp[i]);
    inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
    inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
}
```

7. **IMPORTANT: ALL member registration popup** — After OTP verification, the site redirects to `allmember-web-ext.cpall.co.th/weblogin/allmember/register/step1` showing an ALL member registration page. **Click "ข้าม" (Skip) to bypass registration** and proceed to the main site:

```javascript
const btns = Array.from(document.querySelectorAll('button, a'));
const skipBtn = btns.find(b => b.textContent.trim() === 'ข้าม');
if (skipBtn) skipBtn.click();
```

8. After skipping, you land on the main site logged in as **Your Name** at `allonline.7eleven.co.th/?status=success`

### Key Notes for Login

- The `/json/new?url=...` HTTP API returns 405 — **do NOT use it** to open new tabs. Instead, use an existing tab and `Page.navigate()`.
- The site uses **jQuery** — use `jQuery('#selector').val(value).trigger('change')` for dropdowns (province/district/sub-district cascade).
- Native `dispatchEvent(new Event('change'))` does NOT trigger the district/sub-district cascade. You must use jQuery `.trigger('change')`.
- OTP ref code shown on page (e.g. "REF. WENYMI") matches the ref in the email for verification.
- OTP expires in 5 minutes.

### Account Pages

| Page | URL |
|------|-----|
| Account home | `/account/` |
| Personal settings | `/account/settings/` |
| Addresses (delivery) | `/account/addresses/` |
| Favorite 7-Eleven store | `/account/favoritestore/` |
| Order history | `/account/order-history/` |
| Cart/basket | `/account/basket/` |
| Wishlist | `/account/wishlist/` |

### Address Form (at `/account/settings/`)

The address form uses cascading dropdowns. Fields and IDs:

| Field | ID | Example |
|-------|----|---------|
| House number | `new-address-addrno` | `<house no>` |
| Building/Floor | `new-address-floor` | `<building>` |
| Moo | `new-address-moo` | `<moo>` |
| Soi | `new-address-soi` | |
| Street | `new-address-street` | |
| Province | `new-address-province` | `<province>` |
| District | `new-address-district` | `<district>` |
| Sub-district | `new-address-sub-district` | `<sub-district>` |
| Postal code | `new-address-postal-code` | `<postcode>` (auto-fills) |

**Cascade order**: Set province → wait 3s → set district → wait 3s → set sub-district → postal code auto-fills.

**Submit button**: `#changePersonalData` (text: "ยืนยัน")

**Success alert**: "การตั้งค่าของคุณเปลี่ยนแปลงสำเร็จ"

### Favorite Store Page (`/account/favoritestore/`)

- Store number input: `#js-storefinderInput` (type: number)
- Verify button: `#js-storefinderButton` (text: "ยืนยันรหัสร้าน")
- After verify, a confirm popup appears with "ยกเลิก" (Cancel) and "ยืนยัน" (Confirm) — click `.btn-confirm.btn-green` to save.
- On success, redirects to `/account/addresses/`.
- Error "สาขาที่ท่านเลือกไม่เข้าร่วมรายการ" means the store is not eligible for the delivery program.
- Error "ปัญหาทางเทคนิค" (technical problem) — retry; may be transient.

### Store Locator API

Find nearby 7-Eleven stores programmatically:

```javascript
fetch('https://web-api-ro.7eleven.co.th/v1/Store/GetStoreByCurrentLocation', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({latitude: <latitude>, longitude: <longitude>, radius: 50})
}).then(r => r.json())
```

**Important**: The payload must use `latitude`/`longitude` (not `lat`/`lng`) — the short form returns empty results.

**Important**: Must call this API from the `7eleven.co.th` domain (navigate to `https://www.7eleven.co.th/find-store` first). Calling from `allonline.7eleven.co.th` returns 0 results.

Response: `{code: 0, msg: "success", data: [{id, code, name, address, lat, lng, products: [...]}]}`

### Stores Near Home

Based on the home GPS coordinates:

| Code | Name | Distance | Services | Eligible |
|------|------|----------|----------|----------|
| **`<code>`** | **`<store name>`** | **`<km>`** | Fresh, Food Place, All Cafe, Curated | **Yes (current)** |
| `<code>` | `<store name>` | `<km>` | Fresh, All Cafe, Curated, ALL Select | Untested |
| `<code>` | `<store name>` | `<km>` | Fresh, Food Place, All Cafe, Curated, ALL Select | Untested |
| `<code>` | `<store name>` | `<km>` | Fresh, Food Place, All Cafe, Curated, ALL Select | Untested |
| `<code>` | `<store name>` | `<km>` | Fresh, All Cafe, Curated | Yes |
| `<code>` | `<store name>` | `<km>` | Fresh, All Cafe, Curated, ALL Select | No (not in program) |

### Checkout Flow

#### Step 1: Cart (`/account/basket/`)

- Items listed with "ลบ" (Delete) links — be careful, the confirmation popup may target the wrong item (first in DOM, not the one clicked). Verify cart after removing.
- "ดำเนินการชำระเงิน" button to proceed.
- Product search: `/search/?q=evian`
- Product page: set quantity via `input[type="number"].form-control.text-center`, then click `.btn-addtocart`
- Max 5 cases per product per day per member.

#### Step 2: Shipping (`/checkout/shipping/`)

**Delivery method tabs** — these are **Bootstrap tabs**, NOT radio buttons:

```javascript
// Switch to store pickup (default)
jQuery('a.tab-store[href="#store"]').tab('show');

// Switch to home delivery
jQuery('a.tab-address[href="#address"]').tab('show');
```

**Store pickup tab (`#store`):**
- Free shipping
- Select store via radio: `#s-recent-{storeCode}` (e.g. `#s-recent-01234`)
- Phone field: `#second-phone-shipping` (pre-filled with the account phone)

**Home delivery tab (`#address`):**
- Same address form as account settings (same field IDs)
- **MUST set GPS coordinates** — without them, shipping cost is extremely high (฿700-1100+)
- GPS fields (hidden inputs, set via JS):
  - `#new-address-mapLocation-latitude` → `<latitude>`
  - `#new-address-mapLocation-longitude` → `<longitude>`
  - `#new-address-mapLocation-zipCode` → `<postcode>`
  - Also set `#userAddressBook0mapLocationLatitude`, `#userAddressBook0mapLocationLongitude`, `#userAddressBook0mapLocationZipCode`
- "กรุณาระบุตำแหน่ง" warning means GPS not set — shipping will be wrong
- Submit: `.btn-submit-shipping`

#### Step 3: Payment (`/checkout/payment/`)

**Available payment methods (website only):**
1. Credit/Debit card
2. TrueMoney Wallet
3. **ชำระเงินสด ที่ร้านเซเว่นอีเลฟเว่น (7-11)** — pay cash via barcode at any branch
4. QR Payment

**NO cash on delivery (ชำระเงินปลายทาง)** — COD is only available in the 7-Eleven mobile app, not the website.

For store pickup, option 3 is effectively COD: pick up at store, show barcode, pay cash.

Select payment: click `button.payment-option-trigger.COUNTERSERVICE_CASH-tab` for cash at 7-11.

Submit order: click "สั่งซื้อ" button.

### Home GPS Coordinates

```
Latitude:  <latitude>
Longitude: <longitude>
```
Source: Google Maps

### Current Saved Data

**Delivery address:**
```
<house no>, <building>, หมู่ <moo>, <sub-district>, <district>, <province>, <postcode>
```

**Favorite store:** `<favorite store>`

**Phone:** 0XXXXXXXXX

**Account name:** Your Name
