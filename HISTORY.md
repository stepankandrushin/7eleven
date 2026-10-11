# History

What was done in this repo and when, newest first: changes to the instructions and docs, results of past runs, states that no longer hold. AGENTS.md and docs/ say what is true now. This file is not loaded at the start of a session; read it to find out how something got the way it is.

## 2026-10-11 — AGENTS.md cut from 20.8 KB to 9.2 KB: the reference moved to docs/adb_automation.md and docs/app_ordering.md

The owner's reason: "It doesn't make sense to load such a large AGENTS.md each time. Less tokens go to work then and more expensive." AGENTS.md is loaded whole into every session started in this repo, and it was 20,847 bytes (435 lines), most of it procedures, code examples and the order checklist. It is 9,156 bytes (101 lines) now. The text moved as it stood, cut by line number; only what stays in AGENTS.md is written shorter.

- **docs/adb_automation.md** (new, 8,467 bytes) holds, from "ADB Tap Coordinates — Grid Vision Method", the parts "How it works", "Wide elements", "Quick method" and "Manual method"; the section "Asking Questions to phone_status.py"; from "Verify-Act-Verify Workflow", "The Loop" with its examples and "Standard Workflow"; and the section "Other ADB Commands" whole, with the four input traps in their long form.
- **docs/app_ordering.md** (new, 10,839 bytes) holds "App Navigation", "Launching the App — Always Verify Focus", "Google Play Update Popup", "Campaign Popups", "7 Delivery Search Bar — How to Use", "Checkout Flow (7 Delivery)" and "Complete Order Checklist (App — 7 Delivery)" with the table "Key Pitfalls to Avoid".
- **AGENTS.md** keeps as they stood: the app's package, launch command and activities, the two NEVER rules of the grid vision method with the list of the four scripts, the Key Rules of the loop, and the section "Email (IMAP)". Every other rule and trap is there in a line or two under its old title: the loop, the popups (under one heading, "Popups"), the four input traps, the launch check, the search bar, the checkout traps. The section "Web Ordering Reference" became two lines of the list "Docs", which says when to read each doc, and the reason it gave for using the app (the website does not support cash on delivery) is in the first paragraph. A new line, "Keep this file under 12 KB", says where new text goes.
- **TASK_7ELEVEN_APP_ORDER.md**: its two references to AGENTS.md name the docs that now have the instructions.
- The old AGENTS.md held no dated events, so nothing else was moved into this file.
