#!/usr/bin/env python3
import json
import asyncio
import websockets
import urllib.request
import time

async def send_cmd(ws, method, params=None, msg_id=1):
    """Send a CDP command and return the response."""
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp, msg_id + 1
    return resp, msg_id + 1

async def get_tabs():
    """Get list of open tabs."""
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json/list").read())
    return tabs

async def find_tab(tabs, url_contains=None, title_contains=None):
    """Find a tab by URL or title."""
    for tab in tabs:
        if url_contains and url_contains in tab.get("url", ""):
            return tab
        if title_contains and title_contains in tab.get("title", ""):
            return tab
    return tabs[0] if tabs else None

async def navigate_to(ws, url, msg_id=1):
    """Navigate to a URL."""
    resp, msg_id = await send_cmd(ws, "Page.navigate", {"url": url}, msg_id)
    return resp, msg_id

async def evaluate_js(ws, expression, msg_id=1):
    """Execute JavaScript in the page context."""
    resp, msg_id = await send_cmd(ws, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    }, msg_id)
    return resp, msg_id

async def click_element(ws, selector, msg_id=1):
    """Click an element by CSS selector."""
    resp, msg_id = await evaluate_js(ws, f"""
        () => {{
            const el = document.querySelector('{selector}');
            if (el) {{
                el.click();
                return {{ success: true, text: el.textContent?.substring(0, 50) }};
            }}
            return {{ success: false }};
        }}
    """, msg_id)
    return resp, msg_id

async def fill_input(ws, selector, value, msg_id=1):
    """Fill an input field by CSS selector."""
    resp, msg_id = await evaluate_js(ws, f"""
        () => {{
            const el = document.querySelector('{selector}');
            if (el) {{
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return {{ success: true }};
            }}
            return {{ success: false }};
        }}
    """, msg_id)
    return resp, msg_id

async def get_page_info(ws):
    """Get page title, URL, and key elements."""
    resp, msg_id = await evaluate_js(ws, """
        () => {
            const html = document.body?.innerHTML || "";
            const searchInputs = Array.from(document.querySelectorAll('input[type="search"], input[placeholder*="search"], input[placeholder*="Search"], input[placeholder*="ค้นหา"]'));
            const loginBtns = Array.from(document.querySelectorAll('[class*="login"], [class*="Login"], button:contains("เข้าสู่ระบบ"), [class*="member"]')).slice(0, 5);
            const cartBtns = Array.from(document.querySelectorAll('[class*="cart"], [class*="Cart"], [class*="ตะกร้า"], [aria-label*="cart"]')).slice(0, 3);
            
            return {
                title: document.title,
                url: window.location.href,
                hasSearch: searchInputs.length > 0,
                searchPlaceholder: searchInputs[0]?.placeholder || "",
                searchSelector: searchInputs[0] ? getSelector(searchInputs[0]) : "",
                loginCount: loginBtns.length,
                cartCount: cartBtns.length,
                h1: document.querySelector("h1")?.textContent?.trim() || "",
                bodyClass: document.body?.className || ""
            };
        }
    """)
    return resp

def get_selector(el):
    """Get CSS selector for an element (JS function)."""
    return """
    (el) => {
        if (!el) return "";
        let sel = "";
        while (el && el.nodeType === 1 && el !== document.body) {
            let s = el.tagName.toLowerCase();
            if (el.id) {
                s += "#" + el.id;
                break;
            } else {
                let c = el.className?.trim();
                if (c) {
                    c = c.split(" ").slice(0, 2).join(".");
                    s += "." + c;
                }
                let p = el.parentElement?.querySelectorAll(s);
                if (p && p.length > 1) {
                    s += ":nth-of-type(" + (Array.from(p).indexOf(el) + 1) + ")";
                }
            }
            el = el.parentElement;
        }
        return s;
    }
    """

async def main():
    # Get tabs
    tabs = await get_tabs()
    print(f"Found {len(tabs)} tabs")
    
    # Find the 7-Eleven tab
    page_tab = await find_tab(tabs, url_contains="7del")
    if not page_tab:
        print("Opening new 7-Eleven tab...")
        urllib.request.urlopen("http://localhost:9222/json/new?https://www.7del.co.th")
        await asyncio.sleep(2)
        tabs = await get_tabs()
        page_tab = tabs[0]
    
    ws_url = page_tab["webSocketDebuggerUrl"]
    print(f"Connected to: {page_tab['title']}")
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        msg_id = 1
        
        # Enable DOM and Network
        await send_cmd(ws, "DOM.enable", msg_id=msg_id)
        await send_cmd(ws, "Network.enable", msg_id=msg_id+1)
        
        # Get initial page info
        print("\n=== Page Information ===")
        resp, msg_id = await get_page_info(ws)
        info = resp.get("result", {}).get("value", {})
        print(f"Title: {info.get('title')}")
        print(f"URL: {info.get('url')}")
        print(f"Has search: {info.get('hasSearch')}")
        print(f"Search placeholder: {info.get('searchPlaceholder')}")
        print(f"Cart buttons: {info.get('cartCount')}")
        
        # Check if we're on the homepage
        if info.get('hasSearch'):
            print(f"\n=== Search field found: {info.get('searchSelector')} ===")
            
            # Search for Evian
            search_selector = info.get('searchSelector', 'input[type="search"]')
            print("Searching for 'Evian'...")
            
            # Fill search input
            resp, msg_id = await evaluate_js(ws, f"""
                () => {{
                    const el = document.querySelector('{search_selector}');
                    if (el) {{
                        el.value = 'Evian';
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        // Try to find and click search button
                        const form = el.closest('form');
                        if (form) {{
                            const btn = form.querySelector('button[type="submit"], [class*="search"]');
                            if (btn) btn.click();
                        }}
                        return {{ success: true, value: el.value }};
                    }}
                    return {{ success: false }};
                }}
            """, msg_id)
            
            await asyncio.sleep(3)
            print("Search submitted, waiting for results...")
            
            # Get search results
            await asyncio.sleep(3)
            resp, msg_id = await evaluate_js(ws, """
                () => {
                    const products = Array.from(document.querySelectorAll('[class*="product"], [class*="Product"], [class*="item"], [class*="Item"], [data-product], [data-item]')).slice(0, 10);
                    return products.map(p => ({
                        text: p.textContent?.trim().substring(0, 100),
                        class: p.className,
                        selector: p.tagName.toLowerCase() + (p.className ? '.' + p.className.split(' ')[0] : '')
                    }));
                }
            """, msg_id)
            
            results = resp.get("result", {}).get("value", [])
            print(f"\n=== Found {len(results)} product elements ===")
            for i, r in enumerate(results[:5]):
                print(f"{i+1}. {r['text'][:80]}...")
            
            # Try to find Evian specifically
            resp, msg_id = await evaluate_js(ws, """
                () => {
                    const allText = document.body.textContent || "";
                    const evianElements = Array.from(document.querySelectorAll('[class*="evian"], [class*="Evian"], [class*="เอวาน"]'));
                    
                    // Also search by text content
                    const elements = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent?.toLowerCase().includes('evian') && 
                        el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE'
                    ).slice(0, 10);
                    
                    return {
                        hasEvianText: allText.toLowerCase().includes('evian'),
                        count: elements.length,
                        elements: elements.map(el => ({
                            tag: el.tagName,
                            class: el.className,
                            text: el.textContent?.trim().substring(0, 80)
                        }))
                    };
                }
            """, msg_id)
            
            evian_info = resp.get("result", {}).get("value", {})
            print(f"\n=== Evian search results ===")
            print(f"Has 'Evian' on page: {evian_info.get('hasEvianText')}")
            print(f"Elements found: {evian_info.get('count')}")
            for el in evian_info.get('elements', [])[:5]:
                print(f"  - {el['tag']}.{el['class']}: {el['text']}")
            
            # Wait for user to verify
            print("\n=== Check the browser ===")
            print("Please verify Evian products are showing...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
