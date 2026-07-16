"""Deterministic FlowBench tools. This file contains no task answers."""


REGIONS = ["NA", "EU", "APAC", "LATAM"]
CATEGORIES = ["A", "B", "C", "D"]
CURRENCIES = {"NA": "USD", "EU": "EUR", "APAC": "JPY", "LATAM": "BRL"}
FX_TO_USD_BP = {"USD": 10000, "EUR": 10900, "JPY": 67, "BRL": 1850}
TIERS = ["std", "gold", "plat"]
DISCOUNT_PCT = {"std": 0, "gold": 10, "plat": 20}
CHANNELS = ["web", "store", "partner"]
MONTHS = [202601, 202602, 202603, 202604, 202605, 202606]

N_CUSTOMERS = 72
N_PRODUCTS = 48
N_ORDERS = 720
N_TICKETS = 260
N_RETURNS = 180


def _h(*xs):
    import hashlib
    s = "|".join(str(x) for x in xs).encode()
    return int.from_bytes(hashlib.sha256(s).digest()[:8], "big") & 0x7FFFFFFF


def build_data():
    customers = []
    for cid in range(N_CUSTOMERS):
        region = REGIONS[_h("region", cid) % len(REGIONS)]
        customers.append({
            "customer_id": cid,
            "region": region,
            "tier": TIERS[_h("tier", cid) % len(TIERS)],
            "segment": ["consumer", "smb", "enterprise"][_h("segment", cid) % 3],
        })

    products = []
    for pid in range(N_PRODUCTS):
        cat = CATEGORIES[_h("cat", pid) % len(CATEGORIES)]
        unit_price = 12 + _h("price", pid) % 240
        cogs = unit_price * (45 + _h("margin", pid) % 35) // 100
        products.append({
            "product_id": pid,
            "category": cat,
            "unit_price_usd": unit_price,
            "unit_cogs_usd": cogs,
            "lead_time_days": 3 + _h("lead", pid) % 18,
        })

    inventory = []
    for pid in range(N_PRODUCTS):
        for region in REGIONS:
            inventory.append({
                "product_id": pid,
                "region": region,
                "on_hand": 10 + _h("onhand", pid, region) % 140,
                "reserved": _h("reserved", pid, region) % 28,
                "inbound": _h("inbound", pid, region) % 85,
            })

    orders = []
    for oid in range(N_ORDERS):
        customer_id = _h("ocust", oid) % N_CUSTOMERS
        product_id = _h("oprod", oid) % N_PRODUCTS
        month = MONTHS[_h("month", oid) % len(MONTHS)]
        qty = 1 + _h("qty", oid) % 9
        ship_days = 1 + _h("shipdays", oid) % 16
        promised_days = 3 + _h("promise", oid) % 9
        status = ["paid", "paid", "paid", "paid", "cancelled", "refunded"][
            _h("status", oid) % 6]
        orders.append({
            "order_id": oid,
            "customer_id": customer_id,
            "product_id": product_id,
            "month": month,
            "qty": qty,
            "status": status,
            "channel": CHANNELS[_h("channel", oid) % len(CHANNELS)],
            "ship_days": ship_days,
            "promised_days": promised_days,
        })

    returns = []
    for rid in range(N_RETURNS):
        oid = _h("roid", rid) % N_ORDERS
        order = orders[oid]
        if order["status"] == "cancelled":
            continue
        returned_qty = 1 + _h("rqty", rid) % max(1, order["qty"])
        reason = ["defect", "late", "changed_mind", "wrong_item"][_h("reason", rid) % 4]
        returns.append({
            "return_id": rid,
            "order_id": oid,
            "month": MONTHS[_h("rmonth", rid) % len(MONTHS)],
            "returned_qty": returned_qty,
            "reason": reason,
        })

    tickets = []
    for tid in range(N_TICKETS):
        oid = _h("toid", tid) % N_ORDERS
        severity = ["low", "medium", "high", "critical"][_h("sev", tid) % 4]
        opened = MONTHS[_h("tmonth", tid) % len(MONTHS)]
        first_response_hours = 1 + _h("resp", tid) % 96
        resolution_hours = first_response_hours + _h("res", tid) % 240
        tickets.append({
            "ticket_id": tid,
            "order_id": oid,
            "opened_month": opened,
            "severity": severity,
            "first_response_hours": first_response_hours,
            "resolution_hours": resolution_hours,
        })

    return {
        "customers": customers,
        "products": products,
        "inventory": inventory,
        "orders": orders,
        "returns": returns,
        "tickets": tickets,
        "fx_to_usd_bp": FX_TO_USD_BP,
    }


DATA = build_data()
CUSTOMERS = {c["customer_id"]: c for c in DATA["customers"]}
PRODUCTS = {p["product_id"]: p for p in DATA["products"]}
ORDERS = {o["order_id"]: o for o in DATA["orders"]}


def region_currency(region: str) -> str:
    return CURRENCIES[region]


def get_orders(region: str, category: str, month_start: int, month_end: int) -> list:
    """Paid/refunded order ids in a region/category/month window."""
    out = []
    for o in DATA["orders"]:
        if o["status"] not in ("paid", "refunded"):
            continue
        c = CUSTOMERS[o["customer_id"]]
        p = PRODUCTS[o["product_id"]]
        if c["region"] == region and p["category"] == category and month_start <= o["month"] <= month_end:
            out.append(o["order_id"])
    return sorted(out)


def order_gross_usd(order_id: int) -> int:
    o = ORDERS[order_id]
    p = PRODUCTS[o["product_id"]]
    return o["qty"] * p["unit_price_usd"]


def order_margin_usd(order_id: int) -> int:
    o = ORDERS[order_id]
    p = PRODUCTS[o["product_id"]]
    return o["qty"] * (p["unit_price_usd"] - p["unit_cogs_usd"])


def refund_usd(order_id: int) -> int:
    o = ORDERS[order_id]
    p = PRODUCTS[o["product_id"]]
    qty = sum(r["returned_qty"] for r in DATA["returns"] if r["order_id"] == order_id)
    qty = min(qty, o["qty"])
    return qty * p["unit_price_usd"]


def customer_tier(order_id: int) -> str:
    o = ORDERS[order_id]
    return CUSTOMERS[o["customer_id"]]["tier"]


def apply_discount(amount_usd: int, tier: str) -> int:
    return amount_usd * (100 - DISCOUNT_PCT[tier]) // 100


def net_revenue_usd(order_id: int) -> int:
    gross = apply_discount(order_gross_usd(order_id), customer_tier(order_id))
    return max(0, gross - refund_usd(order_id))


def to_local(amount_usd: int, currency: str) -> int:
    return amount_usd * 10000 // FX_TO_USD_BP[currency]


def inventory_position(product_id: int, region: str) -> int:
    row = next(x for x in DATA["inventory"]
               if x["product_id"] == product_id and x["region"] == region)
    return row["on_hand"] - row["reserved"] + row["inbound"]


def product_lead_time(product_id: int) -> int:
    return PRODUCTS[product_id]["lead_time_days"]


def product_id_for_top_seller(region: str, category: str, month_start: int, month_end: int) -> int:
    totals = {}
    for oid in get_orders(region, category, month_start, month_end):
        o = ORDERS[oid]
        totals[o["product_id"]] = totals.get(o["product_id"], 0) + o["qty"]
    if not totals:
        return -1
    return min((-qty, pid) for pid, qty in totals.items())[1]


def units_sold(product_id: int, region: str, month_start: int, month_end: int) -> int:
    total = 0
    for o in DATA["orders"]:
        if o["product_id"] != product_id or o["status"] not in ("paid", "refunded"):
            continue
        c = CUSTOMERS[o["customer_id"]]
        if c["region"] == region and month_start <= o["month"] <= month_end:
            total += o["qty"]
    return total


def tickets_for_orders(order_ids: list, severity: str) -> list:
    s = set(order_ids)
    return sorted(t["ticket_id"] for t in DATA["tickets"]
                  if t["order_id"] in s and t["severity"] == severity)


def ticket_order_id(ticket_id: int) -> int:
    return next(t["order_id"] for t in DATA["tickets"] if t["ticket_id"] == ticket_id)


def sla_breached(ticket_id: int, first_response_limit_hours: int,
                 resolution_limit_hours: int) -> bool:
    t = next(x for x in DATA["tickets"] if x["ticket_id"] == ticket_id)
    return (t["first_response_hours"] > first_response_limit_hours or
            t["resolution_hours"] > resolution_limit_hours)


def delayed_orders(order_ids: list) -> list:
    s = set(order_ids)
    return sorted(o["order_id"] for o in DATA["orders"]
                  if o["order_id"] in s and o["ship_days"] > o["promised_days"])


def unique_customers(order_ids: list) -> list:
    return sorted({ORDERS[oid]["customer_id"] for oid in order_ids})


def count_items(values: list) -> int:
    return len(values)


def sum_values(values: list) -> int:
    return sum(values)


def count_true(values: list) -> int:
    return sum(1 for v in values if bool(v))


def count_below(values: list, threshold: int) -> int:
    return sum(1 for v in values if v < threshold)


TOOLS = {
    "region_currency": ("region_currency(region: str) -> str",
                        "ISO currency code for a region.", region_currency),
    "get_orders": ("get_orders(region: str, category: str, month_start: int, month_end: int) -> list[int]",
                   "Paid/refunded order ids for a region, product category, and inclusive month window.",
                   get_orders),
    "order_gross_usd": ("order_gross_usd(order_id: int) -> int",
                        "Gross order revenue in USD before discounts/refunds.", order_gross_usd),
    "order_margin_usd": ("order_margin_usd(order_id: int) -> int",
                         "Gross order margin in USD before discounts/refunds.", order_margin_usd),
    "refund_usd": ("refund_usd(order_id: int) -> int",
                   "Refund amount in USD for returned quantity on an order.", refund_usd),
    "customer_tier": ("customer_tier(order_id: int) -> str",
                      "Customer loyalty tier for an order.", customer_tier),
    "apply_discount": ("apply_discount(amount_usd: int, tier: str) -> int",
                       "Apply the order customer's loyalty discount to a USD amount.", apply_discount),
    "net_revenue_usd": ("net_revenue_usd(order_id: int) -> int",
                        "Net USD revenue after loyalty discount and refunds.", net_revenue_usd),
    "to_local": ("to_local(amount_usd: int, currency: str) -> int",
                 "Convert a USD integer amount to a local-currency integer.", to_local),
    "inventory_position": ("inventory_position(product_id: int, region: str) -> int",
                           "Available inventory position: on_hand - reserved + inbound.",
                           inventory_position),
    "product_lead_time": ("product_lead_time(product_id: int) -> int",
                          "Supplier lead time in days for a product.", product_lead_time),
    "product_id_for_top_seller": (
        "product_id_for_top_seller(region: str, category: str, month_start: int, month_end: int) -> int",
        "Product id with the highest units sold in a region/category/month window.",
        product_id_for_top_seller),
    "units_sold": ("units_sold(product_id: int, region: str, month_start: int, month_end: int) -> int",
                   "Units sold for one product in a region and month window.", units_sold),
    "tickets_for_orders": ("tickets_for_orders(order_ids: list[int], severity: str) -> list[int]",
                           "Support ticket ids for given orders and severity.", tickets_for_orders),
    "ticket_order_id": ("ticket_order_id(ticket_id: int) -> int",
                        "Order id associated with a support ticket.", ticket_order_id),
    "sla_breached": (
        "sla_breached(ticket_id: int, first_response_limit_hours: int, resolution_limit_hours: int) -> bool",
        "Whether a support ticket breaches first-response or resolution SLA.",
        sla_breached),
    "delayed_orders": ("delayed_orders(order_ids: list[int]) -> list[int]",
                       "Subset of order ids whose ship_days exceeded promised_days.", delayed_orders),
    "unique_customers": ("unique_customers(order_ids: list[int]) -> list[int]",
                         "Unique customer ids among the given orders.", unique_customers),
    "count_items": ("count_items(values: list) -> int", "Length of a list.", count_items),
    "sum_values": ("sum_values(values: list[int]) -> int", "Sum a list of integers.", sum_values),
    "count_true": ("count_true(values: list[bool]) -> int", "Count true values.", count_true),
    "count_below": ("count_below(values: list[int], threshold: int) -> int",
                    "Count values below a threshold.", count_below),
}

__all__ = [name for name in TOOLS.keys()] + ['TOOLS']
