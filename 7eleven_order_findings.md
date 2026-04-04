# 7-Eleven Thailand Online Order - Key Findings

## Website
- **URL**: https://www.allonline.7eleven.co.th
- **Description**: 7-Eleven Thailand official online shopping and delivery website

## Product Found
- **Item**: เอเวียง น้ำแร่ธรรมชาติ 750 มล. จุกสปอร์ต (ยกลัง 12 ขวด)
- **English**: Evian Natural Mineral Water 750ml Sport Cap (Case of 12 bottles)
- **Product Code**: 420672010
- **Price**: ฿895 per case (was ฿948, 6% discount)
- **Note**: 1L (1000ml) Evian not available; 750ml 12-bottle case is the closest option

## Order Details (3 cases = 36 bottles)
- **Total**: ฿2,685
- **Quantity**: 3 cases × 12 bottles = 36 bottles
- **Delivery**: To be selected at checkout

## Login Credentials
- **Email**: your@email.com
- **Password**: `<removed>`
- **Note**: Login required before checkout; uses 7-Eleven/7App membership account

## Checkout Flow
1. Add product to cart (button: "เพิ่มลงตะกร้า")
2. Go to basket: `/account/basket/`
3. Click "ดำเนินการชำระเงิน" (Proceed to checkout)
4. Select delivery method:
   - "รับที่เซเว่นอีเลฟเว่น" (Pick up at 7-Eleven)
   - "จัดส่งตามที่อยู่" (Delivery to address)
5. Fill in delivery address
6. Select payment method
7. Complete order

## Payment Options
- Pay on delivery (available)
- Credit/Debit card
- Bank transfer

## Delivery Address
```
<building> <house no> Moo <moo> <sub-district> <province> <postcode>
```
- **Location**: `<maps link>`
- **Province**: `<province>`
- **Postal Code**: `<postcode>`

## Session Info
- Chrome Remote Debugging: `localhost:9222`
- Browser: Chrome 146.0.7680.167

## Notes
- The site requires 7-Eleven membership (same account as 7App)
- Delivery to the home address is available
- Estimated delivery: 2-5 business days after payment
- 1L Evian not available; 750ml 12-bottle case is closest option

## Session State (as of today)
- **Cart**: 3 cases of Evian 750ml (ready for checkout)
- **Location**: On checkout page at `/checkout/shipping/`
- **Status**: Logged in, need to select delivery address and complete
- **Next step**: Fill in delivery address and select "ชำระเงินปลายทาง" (Pay on delivery)

## Key Selectors That Worked
- Product search: `input.header-search`
- Add to cart: `button.btn-addtocart`
- Proceed to checkout: `a.btn-proceed`
- Cart icon: `.cart-icon, .mini-basket-cls-mobile`
- Delivery radio: `input[type="radio"][1]` (second option)
