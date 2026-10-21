# MH Sale Pricelist Lot Integration

## Overview

This module extends Odoo 18's pricelist system to support **lot-based pricing rules**. It allows you to create pricelist items that apply specifically to:
- **Base Lot Groups** - All lots sharing the same base name (e.g., all CARRARA_WHITE lots)
- **Lot Price Groups** - Lots with specific dimensions (e.g., CARRARA_WHITE 3.00x1.50x0.02)

## Features

### 🎯 Lot-Based Pricelist Rules

Add two new "Apply On" options in pricelist items:
- **Base Lot Group** - Target all lots in a base group
- **Lot Price Group** - Target lots with specific dimensions

### 🔄 Hybrid Pricing System

The module implements a smart pricing priority:

1. **Pricelist with lot-specific rules** (if defined)
   - Lot Price Group rules (most specific)
   - Base Lot Group rules

2. **Direct lot price** (fallback to existing behavior)
   - Uses `stock.lot.list_price_lot`

3. **Standard pricelist** (product/category/global rules)

### ✅ Full Pricelist Features Support

All standard Odoo pricelist features work with lot groups:
- ✅ Fixed prices
- ✅ Percentage discounts
- ✅ Markup pricing
- ✅ Formulas based on cost/other pricelists
- ✅ Minimum quantities
- ✅ Date ranges (start/end dates)
- ✅ Rounding methods
- ✅ Min/max margins

### 🔌 Zero Breaking Changes

- ✅ Existing sales continue to work
- ✅ Direct lot pricing still works as fallback
- ✅ No migration required
- ✅ Gradual adoption possible

## Installation

1. Place this module in your Odoo addons directory
2. Update the app list: `Settings → Apps → Update Apps List`
3. Search for "MH Sale Pricelist Lot Integration"
4. Click **Install**

## Dependencies

- `product` - Base pricelist functionality
- `sale` - Sale order pricing
- `mh_sale` - Provides `lot_id` field in sale.order.line
- `mh_picking` - Provides `base.lot.group` and `lot.price.group` models

## Usage

### Creating Lot-Based Pricelist Rules

#### Example 1: VIP Customer Discount on Carrara Marble

**Scenario:** Give 10% discount to VIP customers on all Carrara lots

**Steps:**
1. Go to `Sales → Configuration → Pricelists`
2. Create or edit a pricelist (e.g., "VIP Customers")
3. Click **Add a line** in pricelist items
4. Configure:
   - **Apply On:** Base Lot Group
   - **Base Lot Group:** CARRARA_WHITE
   - **Computation:** Percentage (discount)
   - **Percentage Price:** 10%
5. Save

**Result:** All lots in CARRARA_WHITE base group automatically get 10% off for VIP customers

---

#### Example 2: Premium Pricing for Large Slabs

**Scenario:** Charge 20% more for extra large slabs (3.00 x 1.50 meters)

**Steps:**
1. Go to `Sales → Configuration → Pricelists`
2. Create or edit a pricelist
3. Click **Add a line**
4. Configure:
   - **Apply On:** Lot Price Group
   - **Lot Price Group:** CARRARA_WHITE-3.00x1.50 (select the specific dimension group)
   - **Computation:** Percentage (markup)
   - **Percentage Price:** 20%
5. Save

**Result:** Only lots with those exact dimensions get premium pricing

---

#### Example 3: Volume Discount

**Scenario:** Buy 10+ lots from same base group → 5% discount

**Steps:**
1. Create pricelist item
2. Configure:
   - **Apply On:** Base Lot Group
   - **Base Lot Group:** CARRARA_WHITE
   - **Min. Quantity:** 10
   - **Computation:** Percentage (discount)
   - **Percentage Price:** 5%
3. Save

**Result:** Bulk purchases of 10+ Carrara lots get automatic discount

---

#### Example 4: Seasonal Promotion

**Scenario:** Black Friday sale - 15% off all marble lots for one week

**Steps:**
1. Create pricelist item
2. Configure:
   - **Apply On:** Base Lot Group (or multiple items for each base group)
   - **Start Date:** 2024-11-24
   - **End Date:** 2024-11-30
   - **Computation:** Percentage (discount)
   - **Percentage Price:** 15%
3. Save

**Result:** Time-limited promotion applies automatically, then reverts to normal pricing

---

#### Example 5: Native Pricelist with Lot Price Support (NEW)

**Scenario:** Standard product-level discount that respects individual lot prices

**Configuration:**
```
Product: CARRARA_WHITE marble
Product.lst_price = 1000.00 (base product price)

Pricelist Rule:
- Apply On: Product Variant (native Odoo type)
- Product: CARRARA_WHITE
- Computation: Percentage (discount)
- Percentage Price: 10%

Sale Order Line:
- Product: CARRARA_WHITE
- Lot: LOT-PREMIUM-001
- Lot.list_price_lot = 1500.00 (premium lot with special dimensions)
```

**BEFORE this module's enhancement:**
- ❌ Base price = 1000.00 (from product.lst_price)
- ❌ Final price = 1000.00 with 10% discount
- ❌ Result: Customer charged wrong price (500.00 too low!)

**AFTER this module's enhancement:**
- ✅ Base price = 1500.00 (from lot.list_price_lot)
- ✅ Final price = 1500.00 with 10% discount
- ✅ Result: Correct lot-specific pricing honored

**Key Benefit:** You can now use standard Odoo pricelist types (product, category, global) and they will automatically respect individual lot prices when lots are present. This provides maximum flexibility without requiring special lot-based rules for every scenario.

---

#### Example 6: Cost-Based Pricing with Lot-Specific Costs (NEW)

**Scenario:** Apply 50% markup over actual lot cost (useful when lots have different acquisition costs)

**Configuration:**
```
Product: CARRARA_WHITE marble
Product.standard_price = 800.00 (base product cost)

Pricelist Rule:
- Apply On: Product Variant (native Odoo type)
- Product: CARRARA_WHITE
- Computation: Formula
- Base: Cost (standard_price)
- Price Discount: -50% (negative = markup)

Sale Order Line:
- Product: CARRARA_WHITE
- Lot: LOT-IMPORTED-PREMIUM
- Lot.standard_price = 1200.00 (higher import cost)
```

**BEFORE this enhancement:**
- ❌ Base cost = 800.00 (from product.standard_price)
- ❌ Final price = 800.00 * 1.5 = 1200.00
- ❌ Result: Underpriced! (should be 1800.00)

**AFTER this enhancement:**
- ✅ Base cost = 1200.00 (from lot.standard_price)
- ✅ Final price = 1200.00 * 1.5 = 1800.00
- ✅ Result: Correct markup on actual lot cost

**Special Feature - PCMP Support:**
For products using PCMP (Average Weighted Cost) method:
- System automatically uses `lot.pcmp` (most accurate cost)
- Falls back to `lot.standard_price` if PCMP not available
- Ultimate fallback to `product.standard_price`

**Cost Hierarchy:**
```
1. lot.pcmp (if uses_pcmp=True and pcmp > 0)
2. lot.standard_price (if exists and > 0)
3. lot.price_group_id.standard_price (if group exists)
4. product.standard_price (fallback)
```

---

## Technical Details

### Architecture

The module extends three core models:

#### 1. `product.pricelist.item`

**New Fields:**
- `base_lot_group_id` (Many2one → base.lot.group)
- `lot_price_group_id` (Many2one → lot.price.group)

**Extended Selection:**
- `applied_on`: Added '4_base_lot_group' and '5_lot_price_group'
- `display_applied_on`: Added UI options

**New Logic:**
- `_is_applicable_for()`: Checks if rule applies to specific lot
- `_compute_price()`: **Uses `lot.list_price_lot` AND `lot.standard_price` as base for ALL pricelist types**
- `_get_lot_cost()`: Helper method with intelligent cost fallback hierarchy (pcmp → standard_price → group → product)
- Validation constraints for required fields
- Auto-clear conflicting fields on change

**IMPORTANT - Lot Price AND Cost Support for ALL Pricelist Types:**

The module now ensures that **ALL pricelist types** (not just custom lot-based types) correctly use lot-specific values when a lot is present:

- ✅ **Custom Lot Types** (4_base_lot_group, 5_lot_price_group): Always use `lot.list_price_lot`
- ✅ **Native Types** (0_product_variant, 1_product, 2_product_category, 3_global):
  - **Percentage rules**: Always use `lot.list_price_lot` as base
  - **Formula with base='list_price'**: Use `lot.list_price_lot`
  - **Formula with base='standard_price'**: Use lot cost (pcmp/standard_price) via `_get_lot_cost()`
  - **Fixed price rules**: Not affected (don't depend on base)
  - **Other bases**: Use standard Odoo logic (recursive pricelists, etc.)

**Cost Fallback Hierarchy (for base='standard_price'):**
```python
1. lot.pcmp                           # PCMP products (most accurate)
2. lot.standard_price                 # Lot-specific cost
3. lot.price_group_id.standard_price  # Group-level cost
4. product.standard_price             # Product base cost (fallback)
```

This ensures consistent pricing AND costing across your entire pricelist system. Without this feature:
- Revenue loss: Native rules would use `product.lst_price` instead of premium lot prices
- Margin errors: Cost-based formulas would use `product.standard_price` instead of actual lot costs

#### 2. `product.pricelist`

**Extended Methods:**
- `_get_applicable_rules_domain()`: Adds lot group filtering when `lot_id` provided
- Uses OR logic to include lot-based rules in domain

#### 3. `sale.order.line`

**Hybrid Pricing Logic:**
- `_get_pricelist_price_before_discount()`: Implements 3-tier priority system
- `_get_product_price_context()`: Passes `lot_id` to pricelist computation
- `_onchange_lot_id()`: Triggers price recalculation when lot selected
- `_compute_price_unit()`: Added `lot_id` dependency

### Pricing Flow

```
User selects lot_id in sale order line
    ↓
_onchange_lot_id() triggered
    ↓
Dimensions filled from lot
    ↓
_reset_price_unit() called
    ↓
_compute_price_unit() runs (depends on lot_id)
    ↓
_get_pricelist_price_before_discount() called
    ↓
┌─────────────────────────────────────────────┐
│ HYBRID PRICING LOGIC                        │
├─────────────────────────────────────────────┤
│ 1. Try pricelist with lot_id               │
│    - Pass lot_id to _compute_price_rule()   │
│    - Check if lot-specific rule applied     │
│    - If yes → USE THAT PRICE ✓             │
│                                             │
│ 2. Fallback to direct lot price            │
│    - Check lot.list_price_lot               │
│    - If > 0 → USE LOT PRICE ✓              │
│                                             │
│ 3. Fallback to standard pricelist          │
│    - Product/category/global rules          │
│    - Standard Odoo behavior ✓              │
└─────────────────────────────────────────────┘
    ↓
Price set in sale order line
```

### Database Schema

**product_pricelist_item** table extensions:
```sql
ALTER TABLE product_pricelist_item
ADD COLUMN base_lot_group_id INTEGER REFERENCES base_lot_group(id) ON DELETE CASCADE;

ALTER TABLE product_pricelist_item
ADD COLUMN lot_price_group_id INTEGER REFERENCES lot_price_group(id) ON DELETE CASCADE;

CREATE INDEX ON product_pricelist_item(base_lot_group_id);
CREATE INDEX ON product_pricelist_item(lot_price_group_id);
```

## Compatibility

- **Odoo Version:** 18.0
- **Python Version:** 3.10+
- **Required Modules:** product, sale, mh_sale, mh_picking
- **Tested With:** mh_inventory, mh_base

## Known Limitations

1. **Lot-based rules require price_group_id** - Custom lot-based pricelist rules (4_base_lot_group, 5_lot_price_group) require lots to have a price_group_id. If a lot doesn't belong to a price group, these rules won't match (will fall back to native rules or direct lot price).

2. **Formula rules with base='standard_price'** - Now SUPPORTED! ✅ When using formula with base='standard_price', the system uses lot-specific costs (pcmp → standard_price → group cost → product cost hierarchy). For PCMP products, it automatically uses the most accurate `lot.pcmp` value.

3. **Formula rules with base='pricelist' or base='other'** - These use standard Odoo recursive logic. The lot_id context is available but interpretation depends on the target pricelist configuration.

4. **Performance** - With very large numbers of pricelist rules and lots, domain filtering might be slower (indexes help mitigate this)

5. **Multi-company** - Lot groups must respect company boundaries (already enforced via `check_company=True`)

## Troubleshooting

### Price not updating when lot selected

**Check:**
- Does the sale order have a pricelist assigned?
- Does the lot have a `price_group_id`?
- Does a pricelist rule exist for that lot group?
- Is the rule within valid date range?
- Does the quantity meet min_quantity requirement?

### Pricelist rule not matching

**Verify:**
- `Applied On` is set to "Base Lot Group" or "Lot Price Group"
- Correct lot group is selected
- No conflicting fields are set (product_id, categ_id should be empty)
- Rule is active and within date range

### Fallback to direct lot price instead of pricelist

**This is expected behavior when:**
- No lot-specific pricelist rule exists
- The hybrid system uses direct lot price as fallback
- This maintains backward compatibility

**To force pricelist usage:**
- Create an appropriate pricelist rule for the lot group

## Support

For issues or questions:
- **Module:** mh_sale_pricelist_lot
- **Author:** Make It Happen, SA
- **Website:** https://www.makeithappen.pt

## License

LGPL-3

## Changelog

### Version 18.0.1.0.0 (2025-01-09)
- Initial release
- Lot-based pricelist rules support
- Hybrid pricing system
- Full backward compatibility
