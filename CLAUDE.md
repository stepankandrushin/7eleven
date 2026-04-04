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

## 7-Eleven Thailand

See [7eleven_order_findings.md](./7eleven_order_findings.md) for details.
