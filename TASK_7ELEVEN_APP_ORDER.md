# Task: Order Evian Water via 7-Eleven App (Android)

## Goal
Order 3 cases (36 bottles) of Evian 750ml water through the **7-Eleven mobile app** on a Samsung Android phone, delivered to home address with **cash on delivery (ชำระเงินปลายทาง / เก็บเงินปลายทาง)**.

If Evian 1L is available in the app, order that instead (3 cases / 36 bottles).

## Device
- Samsung Android phone connected via USB/ADB
- 7-Eleven app (7App) installed

## Account
- Email: your@email.com
- Login uses OTP sent to email — check OTP via `python3 check_email.py 1` (IMAP script in this repo)
- OTP sender: noreply@7eleven.co.th
- Account name: Your Name

## Delivery Address
```
<house no>, <building>, หมู่ <moo>, <sub-district>, <district>, <province>, <postcode>
```
GPS: `<latitude>, <longitude>`

## Nearest Store
- `<favorite store>` (currently saved as favorite)
- Address: `<store address>`

## Phone
0XXXXXXXXX

## Payment
**Cash on delivery (เก็บเงินปลายทาง)** — this option is available in the app but NOT on the website.

## Product Details
- **Preferred**: Evian 1L (เอเวียง 1 ลิตร) — may not be available
- **Fallback**: Evian 750ml Sport Cap, case of 12 (เอเวียง น้ำแร่ธรรมชาติ 750 มล. จุกสปอร์ต ยกลัง 12 ขวด) — product code 420672010, ฿895/case
- **Quantity**: 3 cases = 36 bottles
- Max 5 cases per product per day per member

## Steps
1. Connect to Samsung phone via ADB
2. Open 7-Eleven app
3. Log in (if not already) — email OTP flow, retrieve OTP from email using `check_email.py`
4. Search for "Evian" or "เอเวียง"
5. Check if 1L is available → if yes, order 3 cases; if no, order 3 cases of 750ml
6. Set delivery address (should be saved already) with GPS coordinates
7. Select **cash on delivery** payment
8. Confirm and place order
9. Report order number and expected delivery date

## Context
- The ALL Online website does NOT support cash on delivery — that's why we're using the app
- Shipping for home delivery should be cheaper 100 THB or free
- The app (7Delivery) uses local store delivery with COD support
