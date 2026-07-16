# FlowBench Public Task

You are in `/app`. The file `/app/flowbench_tools.py` contains deterministic
Python tools over a synthetic business-operations dataset. Use those tools
to compute the requested value, then write the final output to
`/app/answer.txt`.

Required output:
- `/app/answer.txt` must contain only the exact integer.
- Use integer arithmetic for currency and counts. Do not use floating point
  arithmetic.

Task:
For orders in region EU, category A, months 202602-202605: sum net USD revenue after loyalty discounts and refunds, then convert the total into the region's local currency. Report the integer local-currency amount.

Available tools:
- `region_currency(region: str) -> str`: ISO currency code for a region.
- `get_orders(region: str, category: str, month_start: int, month_end: int) -> list[int]`: Paid/refunded order ids for a region, product category, and inclusive month window.
- `order_gross_usd(order_id: int) -> int`: Gross order revenue in USD before discounts/refunds.
- `order_margin_usd(order_id: int) -> int`: Gross order margin in USD before discounts/refunds.
- `refund_usd(order_id: int) -> int`: Refund amount in USD for returned quantity on an order.
- `customer_tier(order_id: int) -> str`: Customer loyalty tier for an order.
- `apply_discount(amount_usd: int, tier: str) -> int`: Apply the order customer's loyalty discount to a USD amount.
- `net_revenue_usd(order_id: int) -> int`: Net USD revenue after loyalty discount and refunds.
- `to_local(amount_usd: int, currency: str) -> int`: Convert a USD integer amount to a local-currency integer.
- `inventory_position(product_id: int, region: str) -> int`: Available inventory position: on_hand - reserved + inbound.
- `product_lead_time(product_id: int) -> int`: Supplier lead time in days for a product.
- `product_id_for_top_seller(region: str, category: str, month_start: int, month_end: int) -> int`: Product id with the highest units sold in a region/category/month window.
- `units_sold(product_id: int, region: str, month_start: int, month_end: int) -> int`: Units sold for one product in a region and month window.
- `tickets_for_orders(order_ids: list[int], severity: str) -> list[int]`: Support ticket ids for given orders and severity.
- `ticket_order_id(ticket_id: int) -> int`: Order id associated with a support ticket.
- `sla_breached(ticket_id: int, first_response_limit_hours: int, resolution_limit_hours: int) -> bool`: Whether a support ticket breaches first-response or resolution SLA.
- `delayed_orders(order_ids: list[int]) -> list[int]`: Subset of order ids whose ship_days exceeded promised_days.
- `unique_customers(order_ids: list[int]) -> list[int]`: Unique customer ids among the given orders.
- `count_items(values: list) -> int`: Length of a list.
- `sum_values(values: list[int]) -> int`: Sum a list of integers.
- `count_true(values: list[bool]) -> int`: Count true values.
- `count_below(values: list[int], threshold: int) -> int`: Count values below a threshold.
