## Executive Summary

The Beaver's Choice Paper Company faces operational bottlenecks in three critical areas: 
inventory management, customer quote generation, and order fulfillment. Manual handling of 
these processes has led to missed sales opportunities, delayed responses, and suboptimal 
stock levels.

### Solution

This project implements a **4-agent orchestrated system** built on the `smolagents` Python 
framework. The architecture uses a Manager Agent 
(CodeAgent) as the central coordinator, delegating tasks to three specialized 
ToolCallingAgents:

| Agent | Role | Key Capabilities |
| --- | --- | --- |
| Manager Agent | Orchestration & routing | Classifies intent, delegates, combines multi-agent responses |
| Inventory Agent | Stock monitoring & procurement | Checks levels, flags low stock, auto-restocks to 2× minimum |
| Quoting Agent | Pricing & quote generation | Searches historical quotes, applies 35% markup, flags availability |
| Order Agent | Sales fulfillment & finance | Validates stock, records transactions, generates financial reports |

### Key Outcomes

* **Responsiveness**: Incoming text requests are automatically classified and routed to the 
  appropriate specialist agent without manual triage.
* **Accuracy**: All quotes are calculated from a canonical product catalog with consistent 
  markup, informed by historical pricing data from prior quotes.
* **Reliability**: Transactions are persisted in an SQLite database with full audit trails; 
  stock and cash balances are validated before any purchase or sale is committed.

### Technology Stack

The system is powered by OpenAI's GPT-4.1-mini model, SQLAlchemy/SQLite for persistent 
state, and pandas for data manipulation. The `smolagents` framework provides tool-decorated 
functions and native LLM integration, enabling each agent to reason over its toolset 
autonomously while the Manager coordinates multi-step workflows.

### Validation

The solution was verified against a set of sample customer requests (`mini_sample.csv`), 
processing each sequentially while tracking cash balance and inventory value across the 
full scenario lifecycle. Results are persisted to `test_results.csv` with a final 
financial health report confirming system integrity.

## System Architecture

### A. Agent Overview

The system employs **4 specialized agents**. Each agent is assigned a distinct operational domain, ensuring clear separation of responsibilities and minimal overlap.

#### 1. Manager Agent (CodeAgent) — Orchestrator & Router

The Manager Agent serves as the central entry point for all incoming text-based requests. 
Built as a `CodeAgent` (from the `smolagents` framework), it has enhanced reasoning 
capabilities that allow it to:

- **Classify intent**: Determine whether an incoming request relates to inventory, quoting, 
  or order fulfillment.
- **Delegate tasks**: Route the request to the appropriate specialist agent.
- **Coordinate multi-step workflows**: For complex requests that span multiple domains 
  (e.g., checking inventory before generating a quote), the Manager orchestrates the 
  sequence of sub-agent calls.
- **Aggregate responses**: Combine outputs from multiple sub-agents into a coherent, 
  unified response for the end user.

The `CodeAgent` type was chosen for the Manager because it can generate and execute Python 
code at runtime, providing maximum flexibility when routing logic requires conditional 
branching or data transformation between agent calls.

#### 2. Inventory Agent (ToolCallingAgent) — Stock Monitoring & Restocking

The Inventory Agent manages all operations related to the company's paper supply levels. 
As a `ToolCallingAgent`, it is equipped with the following tools:

| Tool | Function |
| --- | --- |
| `check_inventory` | Queries the full inventory table and flags items below minimum stock thresholds |
| `check_item_stock` | Looks up stock levels for a specific item by name |
| `restock_item` | Initiates a purchase order to replenish an item to 2× its minimum stock level |

The agent accesses the `inventory` table in SQLite, which tracks `current_stock` and 
`min_stock_level` for each of the ~37 items (80% coverage of the 46-item catalog). 
Restocking decisions are financially validated against the company's available cash balance 
recorded in the `transactions` table.

#### 3. Quoting Agent (ToolCallingAgent) — Pricing & Quote Generation

The Quoting Agent handles customer inquiries about pricing and generates formal quotes. 
Its tools include:

| Tool | Function |
| --- | --- |
| `search_past_quotes` | Queries the `quotes` table for historical pricing data on similar items/quantities |
| `get_catalog_price` | Retrieves the base unit price from the product catalog |
| `calculate_quote` | Computes a final quoted price applying a 35% markup, bulk discounts, and availability checks |

This agent references two data sources:
- **`quotes.csv`** (loaded into the `quotes` table): Historical quote records with metadata 
  on past pricing decisions.
- **`quote_requests.csv`** (loaded into `quote_requests` table): Incoming customer 
  inquiries used to build and validate quoting logic.

The pricing strategy applies a consistent 35% markup over base cost, with intelligence 
drawn from historical quote patterns to remain competitive.

#### 4. Order Agent (ToolCallingAgent) — Sales Fulfillment & Financial Reporting

The Order Agent handles the end-to-end processing of confirmed sales. Its tools include:

| Tool | Function |
| --- | --- |
| `process_sale` | Validates stock availability, deducts inventory, records revenue in the transactions table |
| `estimate_delivery` | Calculates delivery timelines based on item type and quantity |
| `financial_report` | Generates a summary of cash balance, total sales, and inventory valuation |

Before processing any sale, this agent performs pre-flight checks:
1. Confirms sufficient stock exists for the requested quantity
2. Validates the item name matches the canonical catalog exactly
3. Records the transaction with timestamp and type classification (`sale`)

---

### B. Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Agent Framework | `smolagents` | Provides `CodeAgent` and `ToolCallingAgent` abstractions with native tool registration via `@tool` decorators |
| LLM Backend | OpenAI GPT-4.1-mini | Powers agent reasoning, intent classification, and natural language generation (accessed via OpenAI-compatible proxy) |
| Database | SQLAlchemy + SQLite | Persistent state management for inventory, transactions, quotes, and quote requests |
| Data Processing | pandas + NumPy | Inventory generation, CSV ingestion, and data transformation |
| Configuration | python-dotenv | Secure API key management via `.env` file |

#### Why This Stack?

- **`smolagents`** was selected over `pydantic-ai` and `npcpy` for its lightweight 
  architecture, minimal boilerplate, and clear distinction between `CodeAgent` (for 
  orchestration) and `ToolCallingAgent` (for task execution). Tool registration via Python 
  decorators keeps the implementation clean and readable.

- **GPT-4.1-mini** balances reasoning quality with speed and cost, making it suitable for 
  high-frequency request processing in a business context.

- **SQLite** provides zero-configuration persistent storage appropriate for a single-user 
  demonstration system. All four database tables (`inventory`, `transactions`, `quotes`, 
  `quote_requests`) are initialized via the `init_database()` function with reproducible 
  seed-based data generation.

- **pandas** bridges the gap between raw CSV files and the SQLite database, handling 
  schema inference and bulk inserts during initialization.

## Requirement Fulfillment

This section maps each project requirement to the specific tools, logic, and agent 
behaviors implemented in `starter.py`.

---

### A. Inventory Management

**Requirement**: Answer questions regarding current inventory and manage the reordering 
of supplies when necessary, demonstrating effective use of database information and 
purchase decision-making.

The Inventory Agent is equipped with three tools that provide full lifecycle coverage 
of stock management:

#### `check_inventory(as_of_date)`

Performs a complete inventory audit by:
1. Calling `get_all_inventory()` to compute net stock per item (stock_orders minus sales)
2. Cross-referencing against the `inventory` table's `min_stock_level` for each item
3. Flagging each item as `[LOW]` or `[OK]` based on whether current stock ≤ minimum
4. Returning a summary with total items in stock, count of low-stock alerts, and a 
   full line-by-line breakdown

This tool satisfies the requirement to *answer questions regarding current inventory* 
by providing a real-time, transaction-derived snapshot rather than static table lookups.

#### `check_item_stock(item_name, as_of_date)`

Provides a targeted single-item query that:
1. Calls `get_stock_level()` to compute net stock for the specified item
2. Looks up the item's `min_stock_level` from the `inventory` reference table
3. Returns a structured report: current stock, minimum threshold, and a boolean 
   "Needs Restock" determination

If the item is not found in the inventory catalog, the tool returns a clear message 
indicating the item is not currently tracked.

#### `restock_item(item_name, quantity, order_date)`

Executes a purchase decision with the following safeguards:
1. **Catalog validation**: Confirms the item exists in the `inventory` table
2. **Cost calculation**: Computes `quantity × unit_price` from catalog data
3. **Cash sufficiency check**: Calls `get_cash_balance()` and rejects the order if 
   `total_cost > available_cash`
4. **Transaction recording**: Creates a `stock_orders` transaction via 
   `create_transaction()`
5. **Delivery estimation**: Calls `get_supplier_delivery_date()` to provide an 
   expected arrival date based on order size

#### Auto-Restock Strategy (2× Minimum)

The restocking logic is governed by the Inventory Agent's system prompt and the 
`handle_inventory()` helper function, which instructs the agent:

> "If any are below minimum, restock them to 2x their minimum level."

This strategy ensures:
- A buffer above the minimum threshold to prevent immediate re-triggers
- Proportional ordering (items with higher minimums get larger orders)
- Financial discipline (each order is validated against cash balance before execution)

---

### B. Intelligent Quoting

**Requirement**: Provide accurate and intelligent quotes for potential customers by 
considering historical quote data and pricing strategies.

The Quoting Agent combines three tools to produce data-informed, competitive quotes:

#### `search_past_quotes(search_terms, limit)`

Searches historical pricing intelligence by:
1. Accepting comma-separated keywords (e.g., `"wedding,invitation,cardstock"`)
2. Executing a SQL query that joins the `quotes` and `quote_requests` tables
3. Matching keywords against both the original customer request (`qr.response`) and 
   the quote explanation (`q.quote_explanation`) using case-insensitive `LIKE` filters
4. Returning up to `limit` results (default 5) sorted by most recent `order_date`

Each result includes: original request text, total amount quoted, job type, order size, 
event type, and the explanation rationale—giving the agent full context to inform 
competitive pricing.

#### `get_catalog_pricing(item_name)`

Provides authoritative base pricing by:
1. Performing a fuzzy match against the full `paper_supplies` catalog (46 items)
2. Matching any item whose name contains the search term (case-insensitive)
3. Returning item name, category, and unit price for all matches
4. If no `item_name` is provided, returning the complete catalog

This ensures quotes are always grounded in actual product costs rather than 
hallucinated prices.

#### `calculate_quote(items_json, as_of_date, markup)`

Produces a formal quote document by:
1. Parsing a JSON array of `{item_name, quantity}` objects
2. Looking up each item's `unit_price` from `paper_supplies` (exact match, 
   case-insensitive)
3. Computing line-item costs: `quantity × unit_price`
4. Checking real-time stock availability via `get_all_inventory(as_of_date)`
5. Applying a configurable markup (default **35%**) to the subtotal
6. Flagging availability issues where requested quantity exceeds current stock

The output is a formatted quote with:
- Individual line items with unit price, quantity, and extended cost
- Stock status per item (`In Stock` or `LOW` with available quantity)
- Subtotal, markup amount, and final quoted total
- An availability warnings section if restocking is required before fulfillment

---

### C. Transaction Finalization

**Requirement**: Efficiently finalize sales transactions based on the available 
inventory and delivery timelines.

The Order Agent handles end-to-end fulfillment with four tools:

#### `record_sale(item_name, quantity, sale_date)`

Processes a single-item sale with three validation gates:
1. **Catalog existence**: Verifies the item exists in `paper_supplies` (exact match, 
   case-insensitive). Rejects with an error if not found.
2. **Stock availability**: Calls `get_stock_level()` and compares against requested 
   quantity. If `current_stock < quantity`, the sale is blocked with a message 
   indicating the shortfall and recommending a restock.
3. **Revenue calculation**: Applies the standard 35% markup to compute sale price: 
   `quantity × unit_price × 1.35`

Upon successful validation, the function records a `sales` transaction and returns 
a confirmation with transaction ID, revenue generated, and remaining stock.

#### `fulfill_order(items_json, order_date)`

Handles multi-item orders atomically by:
1. Parsing a JSON array of items with quantities
2. Calling `record_sale()` for each item individually
3. Tracking successful vs. failed line items
4. Producing an order fulfillment summary with:
   - Total items processed, successful count, and failed count
   - Detailed per-item results (confirmation or error reason)
   - Updated cash balance after all transactions

This allows partial fulfillment—items with sufficient stock are processed while 
items with insufficient stock are flagged without blocking the entire order.

#### `get_balance(as_of_date)`

Provides financial context before and after transactions with a health assessment:

| Balance Range | Status |
| --- | --- |
| < $0 | CRITICAL — Negative balance |
| $0 – $999 | LOW — Limited purchasing power |
| ≥ $1,000 | HEALTHY |

#### `get_report(as_of_date)`

Generates a comprehensive financial report via `generate_financial_report()` including:
- Cash balance
- Total inventory valuation (units × unit_price for all items)
- Combined total assets
- Itemized inventory breakdown with per-item stock and value
- Top 5 best-selling products ranked by revenue

#### Delivery Timeline Estimation

The system estimates delivery dates via `get_supplier_delivery_date()` using a 
quantity-based lead time model:

| Order Size | Lead Time |
| --- | --- |
| ≤ 10 units | Same day |
| 11 – 100 units | 1 day |
| 101 – 1,000 units | 4 days |
| > 1,000 units | 7 days |

This is integrated into the `restock_item` tool and informs customers when orders 
requiring restocking can be expected.

---

## Testing & Validation

### Test Execution Framework

The system is validated through the `run_test_scenarios()` function, which serves as an 
end-to-end integration test simulating real-world customer interactions against the 
multi-agent system. This function exercises all four agents across diverse request types— 
inventory checks, quote generation, and order fulfillment—within a single sequential run.

---

### Test Data: mini_sample.csv

The test suite ingests customer requests from `mini_sample.csv`, a curated dataset 
containing simulated inquiries representative of actual business scenarios. Each record 
includes:

- **request**: The natural language customer inquiry (text-only input)
- **request_date**: The date the request was received (parsed from MM/DD/YY format)
- **job**: The customer's business role or profession (provides context)
- **event**: The occasion or purpose driving the request (e.g., wedding, corporate event)

Before processing begins, the function performs data preparation:
1. Parses all `request_date` values into proper datetime objects
2. Drops any rows with invalid or missing dates to prevent downstream failures
3. Sorts all requests chronologically by `request_date` to ensure transactions are 
   processed in temporal order—this is critical because inventory levels and cash 
   balances are date-sensitive and cumulative

---

### Sequential Processing Model

Requests are processed strictly one at a time in chronological order. For each request, 
the test harness performs the following cycle:

1. **Pre-request state capture**: Records the current cash balance and inventory value 
   by calling `generate_financial_report()` with the request's date
2. **Context logging**: Prints the request number, customer context (job and event), 
   request date, and current financial state to the console for real-time monitoring
3. **Request augmentation**: Appends the request date to the customer's original text 
   (e.g., "Date of request: 2025-03-15") so that all agents use the correct temporal 
   reference for inventory lookups and transaction recording
4. **Agent invocation**: Passes the augmented request to the `orchestrator()` function, 
   which triggers the Manager Agent's classification and delegation logic
5. **Post-request state update**: Calls `generate_financial_report()` again to capture 
   the updated cash balance and inventory value after any transactions the agents executed
6. **Throttling**: Introduces a 1-second delay between requests to avoid overwhelming 
   the LLM API endpoint with rapid successive calls

This sequential model ensures that each request sees the cumulative effect of all prior 
requests—a sale processed in request #3 reduces stock available for request #4, and a 
restock in request #5 increases the balance available for request #6.

---

### State Tracking

Two financial metrics are tracked continuously across the entire test run:

**Cash Balance** — Computed after each request as the net of all `sales` revenue minus 
all `stock_orders` costs recorded in the `transactions` table up to that request's date. 
This reflects real-time purchasing power and determines whether the system can approve 
restocking orders or must reject them due to insufficient funds.

**Inventory Value** — Calculated after each request by summing `current_stock × unit_price` 
for every item in the inventory table. This captures the total asset value held in 
physical stock and reveals whether the system is maintaining, depleting, or growing its 
inventory base over time.

Together, these two metrics provide a running view of the company's total asset position 
(cash + inventory) and make it immediately visible if the system is operating profitably 
or draining resources.

---

### Results Persistence: test_results.csv

At the conclusion of the test run, all per-request metrics are persisted to 
`test_results.csv`. Each row in the output file contains:

| Field | Description |
| --- | --- |
| request_id | Sequential identifier (1-indexed) |
| request_date | ISO-formatted date the request was processed |
| cash_balance | Cash balance after processing this request |
| inventory_value | Total inventory valuation after processing this request |
| response | The full text response generated by the multi-agent system |

This file serves as the primary audit artifact for evaluating system performance. 
Reviewers can trace the financial trajectory across all requests, identify which 
requests triggered state changes (sales, restocks), and verify that agent responses 
are contextually appropriate and factually consistent with the database state.

---

### Final Financial Report: System Health Check

After all requests have been processed, the test harness generates a comprehensive 
financial report as of the latest request date. This final report acts as a system 
health check and includes:

- **Final Cash Balance**: Confirms the company remains solvent after all transactions. 
  A positive balance indicates the system maintained financial discipline throughout the 
  run; a negative balance would signal that restocking orders exceeded revenue—a critical 
  failure condition.

- **Final Inventory Value**: Reveals whether stock levels were maintained, depleted 
  through sales, or grown through restocking. Combined with cash balance, this shows 
  whether the system achieved net asset growth or decline.

- **Inventory Breakdown**: Itemized list of every product with its remaining stock 
  count and per-item valuation, enabling verification that no single item was over-ordered 
  or completely depleted without replenishment.

- **Top 5 Selling Products**: Ranked by total revenue, this validates that the Order Agent 
  successfully processed sales transactions and that the system correctly identified and 
  fulfilled the highest-demand items.

The final report is printed to the console as the closing output of the test run, 
providing an at-a-glance confirmation that the system operated correctly across all 
scenarios. A healthy final state—positive cash balance, diversified inventory, and 
recorded sales—demonstrates that the 4-agent architecture maintained financial integrity 
while serving customer needs throughout the complete test lifecycle.

---
## Conclusion

### How the 4-Agent Architecture Addresses Core Qualities

#### Responsiveness

The system achieves responsiveness through the **Manager Agent's automatic classification 
and delegation pattern**. When a text-based request arrives, the `CodeAgent` orchestrator 
immediately identifies intent and routes to the appropriate specialist without manual 
intervention or multi-step user interaction. The `CodeAgent` type was specifically chosen 
for the Manager because it can generate runtime Python code to handle conditional routing 
and multi-agent coordination in a single reasoning pass.

Each sub-agent (`ToolCallingAgent`) operates with a focused toolset of 3–4 tools maximum, 
meaning the LLM's decision space is constrained and tool selection is fast. The 
`max_steps=10` limit on sub-agents and `max_steps=12` on the Manager prevent runaway 
reasoning loops, ensuring bounded response times for every request.

For requests that span multiple domains (e.g., "check stock and give me a quote"), the 
Manager coordinates sequential agent calls and combines responses—delivering a unified 
answer in a single interaction cycle rather than requiring the customer to make separate 
requests.

#### Accuracy

Accuracy is enforced through **database-grounded tool outputs** at every decision point:

- **No hallucinated prices**: The `calculate_quote` and `record_sale` tools always 
  resolve pricing from the canonical `paper_supplies` catalog using exact case-insensitive 
  matching. If an item is not found, the tool returns an explicit error rather than 
  estimating.
- **No phantom inventory**: Stock levels are computed dynamically via SQL aggregation 
  of `stock_orders - sales` transactions up to the specified date, not read from a static 
  field that could become stale.
- **Historical grounding for quotes**: The `search_past_quotes` tool queries actual 
  records from the `quotes` and `quote_requests` tables using parameterized SQL with 
  `LIKE` filters, ensuring pricing recommendations are based on real company data.
- **Consistent markup**: The 35% markup is applied programmatically in both `calculate_quote` 
  and `record_sale`, eliminating the risk of the LLM applying inconsistent margins across 
  interactions.

#### Reliability

Reliability is achieved through **multi-layered validation gates** and persistent state:

- **Pre-transaction validation**: Every `restock_item` call checks cash sufficiency 
  before recording; every `record_sale` call verifies stock availability before deducting 
  inventory. Failed validations return descriptive error messages rather than silent 
  failures.
- **Transaction integrity**: All state changes flow through `create_transaction()`, which 
  enforces type validation (`stock_orders` or `sales` only) and records every operation 
  with a timestamp, creating a full audit trail in the `transactions` table.
- **Reproducible initialization**: The `init_database()` function with `seed=137` ensures 
  identical starting conditions across test runs, making results verifiable and 
  comparable.
- **Partial fulfillment support**: The `fulfill_order` tool processes each line item 
  independently—successful items are recorded while failed items are flagged without 
  rolling back the entire order, preventing single-item failures from blocking valid 
  sales.

---
### Final Assessment

The implemented system fulfills all stated project requirements within the architectural 
constraints. The 4-agent design—one orchestrator and three domain specialists—provides 
clear separation of concerns while remaining within the 5-agent limit. Every agent 
interaction is grounded in database state, every financial operation is validated before 
execution, and every response is derived from authoritative catalog and transaction data 
rather than LLM estimation. The `run_test_scenarios()` function provides end-to-end 
validation by processing the sample dataset sequentially, tracking financial state across 
requests, and producing a final report that confirms system integrity.