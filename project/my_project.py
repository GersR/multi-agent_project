import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.8, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.

from openai import OpenAI
import json
import json_repair

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("BASE_URL")

client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

MODEL = "gpt-4.1-mini"

"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""

from smolagents import tool, CodeAgent, ToolCallingAgent, OpenAIServerModel

# Set up the smolagents model (replaces raw OpenAI client for agents)
model = OpenAIServerModel(
    model_id=MODEL,
    api_key=api_key,
    api_base=base_url,
)

#############################
# Tools for inventory agent #
#############################
@tool
def check_inventory(as_of_date: str) -> str:
    """Check all inventory levels and flag items below minimum stock.
    
    Args:
        as_of_date: ISO-formatted date string (YYYY-MM-DD) to check inventory as of.
    """
    inventory = get_all_inventory(as_of_date)
    inventory_ref = pd.read_sql("SELECT * FROM inventory", db_engine)
    
    report_lines = []
    low_stock_items = []
    
    for _, item in inventory_ref.iterrows():
        name = item["item_name"].replace("paper", "")
        current = inventory.get(name, 0)
        minimum = item["min_stock_level"]
        status = "LOW" if current <= minimum else "OK"
        
        if status == "LOW":
            low_stock_items.append(name)
        report_lines.append(f"{name}: {current} units (min: {minimum}) [{status}]")
    
    summary = f"Items in stock: {len(inventory)}/{len(inventory_ref)}\n"
    summary += f"Low stock alerts: {len(low_stock_items)}\n"
    summary += "\n".join(report_lines)
    return summary

@tool
def check_item_stock(item_name: str, quantity: int, as_of_date: str) -> str:
    """Check stock level for a specific item and whether it needs restocking.
    
    Args:
        item_name: The name of the item to check stock for.
        quantity: The quantity needed to have in stock.
        as_of_date: ISO-formatted date string (YYYY-MM-DD) to check stock as of.
    """
    # Load all inventory items for fuzzy matching
    inv_ref = pd.read_sql("SELECT * FROM inventory", db_engine)
    
    search_lower = item_name.lower().replace("paper","")
    search_words = set(search_lower.split())
    
    # Find matching items using bidirectional + word-overlap matching
    matches = []
    for _, row in inv_ref.iterrows():
        catalog_lower = row["item_name"].lower().replace("paper","")
        catalog_words = set(catalog_lower.split())

        if (catalog_lower in search_lower or 
            search_lower in catalog_lower or
            len(catalog_words & search_words) >= max(1, len(catalog_words) * 0.5)):
            matches.append(row)
        
    if not matches:
        return f"No catalog items matching '{item_name}'. Item may need to be sourced externally."

    match=matches[0]
    min_level = int(match["min_stock_level"])
    current_stock = match["current_stock"]
    needs_restock = current_stock <= quantity + min_level
    quantity_needed = quantity + min_level - current_stock
    
    return (
        f"Item: {item_name}\n"
        f"Current Stock: {current_stock}\n"
        f"Minimum Level: {min_level}\n"
        f"Needs Restock: {'YES' if needs_restock else 'No'}\n"
        f"Restock Needed: {quantity_needed if needs_restock else 0}"
    )

@tool
def restock_item(item_name: str, quantity: int, request_date: str, delivery_date: str) -> str:
    """Restock an item by placing a stock order. Validates cash availability, records the transaction, and returns the estimated delivery date.
    
    Args:
        item_name: The name of the item to restock.
        quantity: Number of units to order.
        request_date: ISO-formatted date string (YYYY-MM-DD) for the order request.
        delivery_date: ISO-formatted date string (YYYY-MM-DD) for the order delivery.
    """
    # Load all inventory items for fuzzy matching
    inv_ref = pd.read_sql("SELECT * FROM inventory", db_engine)
    
    search_lower = item_name.lower().replace("paper","")
    search_words = set(search_lower.split())
    
    # Find matching items using bidirectional + word-overlap matching
    matches = []
    for _, row in inv_ref.iterrows():
        catalog_lower = row["item_name"].lower()
        catalog_words = set(catalog_lower.split())
        
        if (catalog_lower in search_lower or 
            search_lower in catalog_lower or
            len(catalog_words & search_words) >= max(1, len(catalog_words) * 0.5)):
            matches.append(row)
    
    if not matches:
        return f"'{item_name}' is not currently in our inventory catalog."
    
    match=matches[0]
    min_level = int(match["min_stock_level"])
    current_stock = match["current_stock"]
    needs_restock = current_stock <= quantity + min_level
    quantity_needed = quantity + min_level - current_stock
    if quantity_needed <= 0:
        return f"Item '{match['item_name']}' has sufficient stock ({current_stock} units). No restock needed."

    restock_date = get_supplier_delivery_date(request_date, quantity_needed)
    restock_cost = quantity_needed * match["unit_price"]

    # --- CHECK: Does delivery arrive by order_date? ---
    if restock_date > delivery_date:
        return (
            f"RESTOCK DELAYED:\n"
            f"  Item: {match['item_name']}\n"
            f"  Quantity Needed: {quantity_needed}\n"
            f"  Request Date: {request_date}\n"
            f"  Expected Delivery: {delivery_date}\n"
            f"  → Cannot fulfill by requested date. Restock delivery arrives {restock_date}."
        )

    # --- CHECK: Sufficient cash? ---
    cash = get_cash_balance(request_date)
    if cash < restock_cost:
        return (
            f"ERROR: Insufficient cash (${cash:.2f}) to cover restock cost (${restock_cost:.2f})."
        )

    # --- RECORD the restock transaction ---
    txn_id = create_transaction(
        item_name=match["item_name"],
        transaction_type="stock_orders",
        quantity=quantity_needed,
        price=restock_cost,
        date=restock_date
    )

    # --- UPDATE the inventory reference table ---
    new_stock=current_stock + quantity_needed
    with db_engine.connect() as conn:
        conn.execute(
            text("UPDATE inventory SET current_stock = :new_stock WHERE item_name = :name"),
            {"new_stock": new_stock, "name": match["item_name"]}
        )
        conn.commit()

    return (
        f"RESTOCKED (Txn #{txn_id}):\n"
        f"  Item: {match['item_name']}\n"
        f"  Quantity Ordered: {quantity_needed}\n"
        f"  Cost: ${restock_cost:.2f}\n"
        f"  Request Date: {request_date}\n"
        f"  Expected Delivery: {delivery_date}\n"
        f"  Expected Restock Delivery: {restock_date}\n"
        f"  New Stock Level: {new_stock}"
    )

#############################
# Tools for quoting agent   #
#############################
@tool
def search_past_quotes(search_terms: str, limit: int = 5) -> str:
    """Search historical quotes for similar requests to inform pricing. Provide comma-separated search terms.
    
    Args:
        search_terms: Comma-separated keywords to search for in past quotes (e.g. "wedding,invitation,cardstock").
        limit: Maximum number of results to return. Defaults to 5.
    """  
    terms_list = [t.strip() for t in search_terms.split(",") if t.strip()]
    
    results = search_quote_history(terms_list, limit=limit)  
    print(f"Results: {results}")

    if not results:
        return f"No historical quotes found matching: {', '.join(terms_list)}"
    
    lines = [f"Found {len(results)} matching historical quote(s):\n"]
    for i, quote in enumerate(results, 1):
        lines.append(
            f"Quote #{i}:\n"
            f"  Original Request: {quote['original_request'][:100]}...\n"
            f"  Total Amount: ${quote['total_amount']:.2f}\n"
            f"  Job Type: {quote.get('job_type', 'N/A')}\n"
            f"  Order Size: {quote.get('order_size', 'N/A')}\n"
            f"  Event Type: {quote.get('event_type', 'N/A')}\n"
            f"  Explanation: {quote['quote_explanation'][:150]}...\n"
        )
    return "\n".join(lines)

@tool
def get_catalog_pricing(item_name: str = None) -> str:
    """Look up pricing from the full paper supplies catalog. If item_name is empty, returns all items. Otherwise filters to items matching the search term.
    
    Args:
        item_name: Item name or partial name to search for. Leave empty for full catalog.
    """
    # Load all inventory items for fuzzy matching
    inv_ref = pd.read_sql("SELECT * FROM inventory", db_engine)
    
    search_lower = item_name.lower().replace("paper","")
    search_words = set(search_lower.split())
    
    # Find matching items using bidirectional + word-overlap matching
    matches = []
    for _, row in inv_ref.iterrows():
        catalog_lower = row["item_name"].lower().replace("paper","")
        catalog_words = set(catalog_lower.split())

        if (catalog_lower in search_lower or 
            search_lower in catalog_lower or
            len(catalog_words & search_words) >= max(1, len(catalog_words) * 0.5)):
            matches.append(row)
        
    if not matches:
        return f"No catalog items matching '{item_name}'. Item may need to be sourced externally."
    
    lines = [f"Catalog matches for '{item_name}':"]
    
    for m in matches:
        lines.append(f"Item name: {m['item_name']}. Unit Price: ${m['unit_price']:.2f}/unit")
    
    return "\n".join(lines)

@tool
def calculate_quote(items_json: str, as_of_date: str, markup: float = 0.35) -> str:
    """Calculate a quote for requested items. Takes a JSON string of items with names and quantities.
    
    Args:
        items_json: JSON array of objects with 'item_name' and 'quantity' keys, e.g. '[{"item_name": "A4 paper", "quantity": 500}]'.
        as_of_date: ISO-formatted date string (YYYY-MM-DD) for inventory availability check.
        markup: Profit margin to apply as a decimal (default 0.35 for 35%).
    """
    import json
    items_requested = json.loads(items_json)
    inventory = get_all_inventory(as_of_date)
    
    line_items = []
    subtotal = 0.0
    availability_issues = []
    
    # Load all inventory items
    inv_ref = pd.read_sql("SELECT * FROM inventory", db_engine)

    # Find matching items using bidirectional + word-overlap matching
    for req in items_requested:
        name = req["item_name"]
        qty = req["quantity"]
        search_lower = name.lower().replace("paper","")
        search_words = set(search_lower.split())
        matches = []
        
        for _, row in inv_ref.iterrows():
            catalog_lower = row["item_name"].lower().replace("paper","")
            catalog_words = set(catalog_lower.split())

            if (catalog_lower in search_lower or 
                search_lower in catalog_lower or
                len(catalog_words & search_words) >= max(1, len(catalog_words) * 0.5)):
                matches.append(row)
        
        if not matches:
            availability_issues.append(f"'{name}' not found in catalog")
            continue
        match=matches[0]
        unit_price = match["unit_price"]
        line_cost = qty * unit_price
        subtotal += line_cost
        
        # Check stock availability
        current_stock = match["current_stock"]
        stock_status = "In Stock" if current_stock >= qty else f"LOW (only {current_stock} available, need restock)"
        
        if current_stock < qty:
            availability_issues.append(f"'{name}': need {qty}, have {current_stock}")
        
        line_items.append(
            f"  - {name} x {qty} @ ${unit_price:.2f} = ${line_cost:.2f} [{stock_status}]"
        )
    
    # Apply markup
    total_with_markup = subtotal * (1 + markup)
    
    # Build quote summary
    quote_lines = ["QUOTE SUMMARY", "=" * 40]
    quote_lines.append(f"Date: {as_of_date}")
    quote_lines.append(f"Line Items:")
    quote_lines.extend(line_items)
    quote_lines.append(f"\n  Subtotal (cost): ${subtotal:.2f}")
    quote_lines.append(f"  Markup ({markup*100:.0f}%): ${subtotal * markup:.2f}")
    quote_lines.append(f"  TOTAL QUOTE: ${total_with_markup:.2f}")
    
    if availability_issues:
        quote_lines.append(f"\nAvailability Issues:")
        for issue in availability_issues:
            quote_lines.append(f"    - {issue}")
        quote_lines.append("  → Restocking required before fulfillment.")
    
    return "\n".join(quote_lines)


#############################
# Tools for ordering agent  #
#############################
@tool
def record_sale(item_name: str, quantity: int, sale_date: str) -> str:
    """Record a sale transaction. Validates stock availability, records the sale, and updates inventory state.
    
    Args:
        item_name: The name of the item being sold.
        quantity: Number of units sold.
        sale_date: ISO-formatted date string (YYYY-MM-DD) for the sale.
    """
    # Load all inventory items for fuzzy matching
    inv_ref = pd.read_sql("SELECT * FROM inventory", db_engine)
    # Verify item exists in catalog
    search_lower = item_name.lower()
    search_words = set(search_lower.split())
    # Find matching items using bidirectional + word-overlap matching
    matches = []
    for _, row in inv_ref.iterrows():
        catalog_lower = row["item_name"].lower().replace("paper", "")
        catalog_words = set(catalog_lower.split())
        
        if (catalog_lower in search_lower or 
            search_lower in catalog_lower or
            len(catalog_words & search_words) >= max(1, len(catalog_words) * 0.5)):
            matches.append(row)

    if not matches:
        return f"ERROR: '{item_name}' not found in product catalog."
    
    match=matches[0]
    catalog_match = match["item_name"]
    unit_price = match["unit_price"]

    # Check stock availability
    current_stock = int(match["current_stock"])

    if current_stock < quantity:
        return (
            f"ERROR: Insufficient stock for '{item_name}'.\n"
            f"Requested: {quantity}, Available: {current_stock}\n"
            f"→ Restock required before fulfilling this order."
        )

    # Calculate sale price (with markup applied)
    markup = 0.35
    sale_price = quantity * unit_price * (1 + markup)

    # Record the sale
    txn_id = create_transaction(
        item_name=catalog_name,
        transaction_type="sales",
        quantity=quantity,
        price=sale_price,
        date=sale_date
    )
    # Update inventory
    new_stock = current_stock - quantity
    with db_engine.connect() as conn:
        conn.execute(
            text("UPDATE inventory SET current_stock = :new_stock WHERE item_name = :name"),
            {"new_stock": new_stock, "name": catalog_match}
        )
        conn.commit()

    return (
        f"Sale recorded (Txn #{txn_id}):\n"
        f"Item: {item_name}\n"
        f"Quantity: {quantity} units\n"
        f"Revenue: ${sale_price:.2f}\n"
        f"Remaining Stock: {new_stock} units"
    )

@tool
def get_balance(as_of_date: str) -> str:
    """Get current cash balance with contextual health status.
    
    Args:
        as_of_date: ISO-formatted date string (YYYY-MM-DD) to check balance as of.
    """
    cash = get_cash_balance(as_of_date)

    if cash < 0:
        status = "CRITICAL - Negative balance"
    elif cash < 1000:
        status = "LOW - Limited purchasing power"
    else:
        status = "HEALTHY"

    return (
        f"Cash Balance as of {as_of_date}:\n"
        f"  Amount: ${cash:.2f}\n"
        f"  Status: {status}"
    )

@tool
def get_report(as_of_date: str) -> str:
    """Generate a formatted financial report including cash balance, inventory value, total assets, and top selling products.
    
    Args:
        as_of_date: ISO-formatted date string (YYYY-MM-DD) for the report date.
    """
    report = generate_financial_report(as_of_date)

    lines = [
        "FINANCIAL REPORT",
        "=" * 40,
        f"Date: {report['as_of_date']}",
        f"Cash Balance: ${report['cash_balance']:.2f}",
        f"Inventory Value: ${report['inventory_value']:.2f}",
        f"Total Assets: ${report['total_assets']:.2f}",
        "",
        "Inventory Breakdown:"
    ]
    for item in report["inventory_summary"]:
        lines.append(
            f"  - {item['item_name']}: {item['stock']} units "
            f"(${item['value']:.2f})"
        )
    
    if report["top_selling_products"]:
        lines.append("\nTop Selling Products:")
        for product in report["top_selling_products"]:
            if not product["item_name"] or pd.isna(product["total_units"]):
                continue
            lines.append(
                f"  - {product['item_name']}: "
                f"{int(product['total_units'])} units, "
                f"${product['total_revenue']:.2f} revenue"
            )
    else:
        lines.append("\nNo sales recorded yet.")
    return "\n".join(lines)

@tool
def fulfill_order(items_json: str, order_date: str) -> str:
    """Process a full order with multiple items. Validates all items, records sales, and reports any issues.
    
    Args:
        items_json: JSON array of objects with 'item_name' and 'quantity' keys, e.g. '[{"item_name": "A4 paper", "quantity": 500}]'.
        order_date: ISO-formatted date string (YYYY-MM-DD) for the order.
    """
    import json
    items = json.loads(items_json)
    results = []
    successful = 0
    failed = 0

    for item in items:
        result = record_sale(item["item_name"], item["quantity"], order_date)
        results.append(f"[{item['item_name']}] {result}")
        if result.startswith("ERROR"):
            failed += 1
        else:
            successful += 1

    summary = (
        f"ORDER FULFILLMENT SUMMARY\n"
        f"{'=' * 40}\n"
        f"Date: {order_date}\n"
        f"Items Processed: {len(items)}\n"
        f"Successful: {successful}\n"
        f"Failed: {failed}\n\n"
        f"Details:\n" + "\n\n".join(results)
    )

    # Append updated balance
    cash = get_cash_balance(order_date)
    summary += f"\n\nUpdated Cash Balance: ${cash:.2f}"

    return summary

############
# HELPERS  #
###########

def handle_inventory(classification: Dict, request_date: str) -> str:
    """Inventory Agent: delegates to ToolCallingAgent."""
    items = classification.get("items", [])
    
    if not items:
        task = (
            f"Check all inventory levels as of {request_date}. "
            f"Identify any items below minimum stock and restock them "
            f"to 2x their minimum level."
        )
    else:
        task = (
            f"Check stock levels for these items as of {request_date}: {items}. "
            f"If any are below minimum, restock them to 2x their minimum level."
        )
    
    return inventory_agent.run(task)

def handle_quote(classification: Dict, request_date: str, original_request: str) -> str:
    """Quoting Agent: delegates to ToolCallingAgent."""
    items = classification.get("items", [])
    quantities = classification.get("quantities", [])
    context = classification.get("context", "")
    
    # Build a descriptive task for the agent
    items_detail = ""
    if items:
        parts = []
        for i, item_name in enumerate(items):
            qty = quantities[i] if i < len(quantities) else 100
            parts.append(f"{item_name} x {qty}")
        items_detail = ", ".join(parts)
    
    task = (
        f"Customer request: {original_request}\n\n"
        f"Date: {request_date}\n"
        f"Items identified: {items_detail if items_detail else 'See request above'}\n"
        f"Context: {context}\n\n"
        f"Search for similar past quotes, look up catalog pricing, "
        f"and calculate a professional quote with 35% markup. "
        f"Flag any availability issues."
    )
    
    return quoting_agent.run(task)

def handle_order(classification: Dict, request_date: str, original_request: str) -> str:
    """Order Agent: delegates to ToolCallingAgent."""
    items = classification.get("items", [])
    quantities = classification.get("quantities", [])
    
    # Build order description
    order_parts = []
    for i, item_name in enumerate(items):
        qty = quantities[i] if i < len(quantities) else 100
        order_parts.append(f"{item_name} x {qty}")
    
    task = (
        f"Original request: {original_request}\n\n"
        f"Date: {request_date}\n"
        f"Items to fulfill: {', '.join(order_parts) if order_parts else 'See request above'}\n\n"
        f"First check the cash balance, then fulfill the order. "
        f"Report confirmation or explain any issues (insufficient stock, etc.)."
    )
    
    return order_agent.run(task)

# Set up your agents and create an orchestration agent that will manage them.
##########################
# CREATE SUB-AGENTS      #
##########################

inventory_agent = ToolCallingAgent(
    tools=[check_inventory, check_item_stock, restock_item],
    model=model,
    name="inventory_agent",
    description=(
        "Manages stock levels and restocking for the paper warehouse. "
        "Use this agent to: check current inventory levels for all or specific items, "
        "identify items below their minimum stock threshold, and place restock orders "
        "Typical triggers: 'check stock', 'do we have enough', 'restock', "
        "'inventory status', 'what's available', or when another agent reports "
        "'insufficient stock' or 'LOW' availability. "
        "Do NOT use for pricing, quotes, or recording sales — those belong to "
        "quoting_agent and order_agent respectively."
    ),
    instructions=(
        "You are the Inventory Agent for Munder Difflin Paper Company.\n\n"
        "YOUR RESPONSIBILITIES:\n"
        "1. Check stock levels for specific items or the entire warehouse.\n"
        "2. Restock items that are insufficient for a pending order or below their minimum threshold.\n\n"
        "WORKFLOW:\n"
        "- When asked about specific items: use `check_item_stock` for each item.\n"
        "- When asked for a full inventory scan: use `check_inventory`.\n"
        "- When restocking is needed: use `restock_item` with the appropriate quantity.\n\n"
        "RESTOCKING RULES:\n"
        "- Fulfill to restock needed\n"
        "- Always confirm the restock was recorded before reporting success.\n\n"
        "RESPONSE FORMAT:\n"
        "- Always report: item name, current stock, minimum level, and whether restocking was performed.\n"
        "- If stock is sufficient: state 'AVAILABLE — ready for quoting/fulfillment'.\n"
        "- If stock was insufficient and you restocked: state 'RESTOCKED — now ready for quoting/fulfillment'.\n"
        "- If an item is not found in the catalog: state 'NOT IN CATALOG — cannot fulfill'.\n\n"
        "IMPORTANT:\n"
        "- Always use the date provided in the task for all stock lookups.\n"
        "- Do NOT generate quotes or record sales — that is not your role.\n"
        "- Be concise and structured so downstream agents can parse your output."
    ),
    max_steps=10,
)

quoting_agent = ToolCallingAgent(
    tools=[search_past_quotes, get_catalog_pricing, calculate_quote],
    model=model,
    name="quoting_agent",
    description=(
        "Creates price quotes and cost estimates for customer paper supply requests. "
        "Use this agent when a customer describes what supplies they need and you must "
        "determine pricing — even if they say 'I would like to request' or 'I need'. "
        "This agent interprets requests to identify items, matches them to catalog products "
        "Call AFTER inventory_agent confirms availability and BEFORE order_agent fulfills."
        "Typical triggers: 'quote', 'price', 'cost', 'estimate', 'request supplies', "
        " or any request listing items with quantities that needs pricing."
    ),
    instructions=(
    "You are the Quoting Agent for Munder Difflin Paper Company.\n\n"
    "YOUR RESPONSIBILITIES:\n"
    "1. Interpret customer requests to identify specific items and quantities.\n"
    "2. Look up catalog pricing for each item.\n"
    "3. Search historical quotes for similar orders to ensure consistency.\n"
    "WORKFLOW (follow this order every time):\n"
    "- Step 1: Use `get_catalog_pricing` for each item the customer mentioned to confirm it exists and get the base price.\n"
    "- Step 2: Use `search_past_quotes` with relevant keywords (item names, event type, job type) to find comparable past quotes.\n"
    "- Step 3: Use `calculate_quote` with a JSON array of all items and quantities, the request date, and the 0.35 markup.\n\n"
    "PRICING RULES:\n"
    "- If an item has multiple catalog matches, pick the closest match.\n"
    "- If an item is NOT found in the catalog, include it in your response as 'NOT IN CATALOG — requires sourcing'.\n\n"
    "RESPONSE FORMAT:\n"
    "- List each line item with: item name, quantity, unit price, line total.\n"
    "- Show subtotal, markup amount, and final quoted total.\n"
    "- Flag any availability issues (e.g., 'LOW stock — restocking may be required before fulfillment').\n"
    "- Reference similar past quotes if found (e.g., 'Similar to Quote #3: wedding invitation order at $X').\n\n"
    "IMPORTANT:\n"
    "- Always use the date provided in the task for the `as_of_date` parameter.\n"
    "- Do NOT record sales or modify inventory — that belongs to order_agent.\n"
    "- Do NOT restock items — that belongs to inventory_agent.\n"
    "- Be concise and structured so order_agent can parse your output for fulfillment."
    ),
    max_steps=10,
)

order_agent = ToolCallingAgent(
    tools=[record_sale, get_balance, get_report, fulfill_order],
    model=model,
    name="order_agent",
    description=(
        "Fulfills confirmed customer orders and manages company finances. "
        "Call ONLY after inventory_agent confirms stock AND quoting_agent provides a quote."
        "Also handles standalone financial queries: 'what is our balance', 'generate a report'. "
        "Do NOT use for price estimates or 'how much would it cost' — use quoting_agent instead."
    ),
    instructions=(
        "You are the Order Agent for Munder Difflin Paper Company.\n\n"
        "YOUR RESPONSIBILITIES:\n"
        "1. Fulfill confirmed customer orders by recording sales transactions.\n"
        "2. Provide financial information: cash balance and financial reports.\n\n"
        "WORKFLOW FOR ORDER FULFILLMENT (follow this order every time):\n"
        "- Step 1: Use `get_balance` to verify the company has sufficient cash to cover supplier costs.\n"
        "- Step 2: Use `fulfill_order` with the full JSON array of items and quantities to process the batch.\n"
        "- Step 3: Use `get_balance` again to report the updated cash position after fulfillment.\n\n"
        "WORKFLOW FOR FINANCIAL QUERIES:\n"
        "- For balance inquiries: Use `get_balance` with the specified date.\n"
        "- For full reports: Use `get_report` with the specified date.\n\n"
        "ERROR HANDLING:\n"
        "- If `fulfill_order` reports 'Insufficient stock' for any item, report the shortage clearly:\n"
        "  state the item name, quantity needed, and quantity available.\n"
        "- Do NOT attempt to restock — that is inventory_agent's job.\n"
        "- If cash balance is negative or critically low, flag it as a warning before proceeding.\n\n"
        "RESPONSE FORMAT:\n"
        "- For successful orders: report each item fulfilled, total revenue, and updated cash balance.\n"
        "- For partial failures: separate successful items from failed ones and explain each failure.\n"
        "- For financial queries: return the formatted balance or report as provided by the tools.\n\n"
        "IMPORTANT:\n"
        "- Always use the date provided in the task for all tool calls.\n"
        "- Do NOT generate quotes or check inventory — those belong to quoting_agent and inventory_agent.\n"
        "- Do NOT call `record_sale` directly if you have multiple items — use `fulfill_order` for batch processing.\n"
        "- Be concise and structured so the manager agent can compose a final customer response."
    ),
    max_steps=10,
)

##################
# ORCHESTRATOR   #
##################
manager_agent = CodeAgent(
    tools=[],  # No direct tools - delegates everything to sub-agents
    model=model,
    managed_agents=[inventory_agent, quoting_agent, order_agent],
    instructions=(
        """You are the Manager Agent for Munder Difflin Paper Company.
        You coordinate a team of specialized agents to handle customer requests.

        Your team:
        - inventory_agent: checks stock levels and restocks items
        - quoting_agent: creates price quotes for customer inquiries
        - order_agent: fulfills confirmed orders and tracks finances

        === MANDATORY WORKFLOW RULES ===

        STEP 1: CLASSIFY the incoming request into one of these categories:
          A) ORDER — customer wants to purchase/order/buy/request supplies with intent to receive them
          B) QUOTE_ONLY — customer wants a price estimate without placing an order
          C) INVENTORY_CHECK — customer asks about stock levels or availability only
          D) FINANCIAL — customer asks about balance, reports, or revenue

        STEP 2: EXECUTE the correct workflow based on classification:

        For ORDER requests (category A), you MUST execute ALL 3 steps IN THIS EXACT ORDER:
          1. Call inventory_agent → verify stock for ALL requested items. If stock is insufficient,
             instruct inventory_agent to restock the needed quantity BEFORE proceeding.
          2. Call quoting_agent → generate a priced quote with 35% markup for the requested items.
          3. Call order_agent → fulfill the order and record the sales transactions.
          ⚠️ NEVER call order_agent without FIRST completing steps 1 and 2 for the same request.
          ⚠️ NEVER skip the quoting step — every order must have a quote generated before fulfillment.

        For QUOTE_ONLY requests (category B), execute steps 1 and 2 only:
          1. Call inventory_agent → check availability for quoted items.
          2. Call quoting_agent → generate the quote with pricing and availability notes.

        For INVENTORY_CHECK requests (category C):
          1. Call inventory_agent only.

        For FINANCIAL requests (category D):
          1. Call order_agent only (it has get_balance and get_report tools).

        === FINAL RESPONSE FORMAT ===

        When composing the final customer-facing response, use the following template. 
        Adapt sections based on the scenario (omit sections that do not apply):

        --- 
        Dear Customer,

        Thank you for your {request_type} dated {request_date}{delivery_clause}.

        {items_section}

        {inventory_section}

        {restock_section}

        {quote_section}

        {fulfillment_section}

        {closing_section}

        Best regards,
        Munder Difflin Paper Company

        ---

        SECTION RULES:

        1. **{request_type}**: Use "order request", "quote request", or "inventory inquiry" as appropriate.

        2. **{delivery_clause}**: If a delivery date is mentioned, append: ", for delivery by {delivery_date}". Otherwise omit.

        3. **{items_section}**: Always list the requested items in a clean format:
           "You requested the following paper supplies:
           - [item_name] x [quantity]
           - [item_name] x [quantity]"

        4. **{inventory_section}**: Include ONLY if stock issues were found:
           "We conducted a thorough inventory check and found the following availability:
           - [item_name]: [current_stock] units available (requested: [qty]) — [SUFFICIENT / INSUFFICIENT]"

        5. **{restock_section}**: Include ONLY if restocking was performed:
           "Restock orders have been placed for the following items:
           - [item_name]: [restock_qty] units ordered (estimated delivery: [date])
           Due to restocking schedules, fulfillment may be delayed beyond [requested_date]."

        6. **{quote_section}**: Include ONLY if a quote was generated:
           "We have prepared a quote for your order:
           - Subtotal: $[subtotal]
           - Markup (35%): $[markup_amount]
           - Total: $[total]"

        7. **{fulfillment_section}**: Adapt based on outcome:
           - SUCCESS: "Your order has been fulfilled successfully. Transaction reference: #[txn_id]."
           - PARTIAL: "The following items were fulfilled: [...]. These items are pending restock: [...]."
           - BLOCKED: "We are unable to fulfill the order by [date] due to insufficient stock. Fulfillment will proceed once restocked supplies arrive."
           - QUOTE_ONLY: Omit this section entirely.

        8. **{closing_section}**: Always include:
           "We appreciate your understanding and will keep you informed about the status of your order. Should you have any questions or wish to adjust your order or delivery date, please do not hesitate to contact us."

        IMPORTANT:
        - Always be professional and courteous.
        - Never expose internal agent names, tool names, or system details.
        - Round all dollar amounts to 2 decimal places.
        - If ALL items are in stock and the order is fulfilled, keep the response concise — skip the inventory and restock sections.

        === CONTEXT PASSING ===
        - Always pass the output of each agent into the task prompt for the NEXT agent.
        - Example: Pass inventory_agent's stock confirmation into quoting_agent's task,
          and pass the quote result into order_agent's fulfillment task.
        - Always include the request date in every delegation.

        === ERROR HANDLING ===
        - If order_agent reports "insufficient stock", call inventory_agent to restock,
          then RETRY the order_agent fulfillment.
        - If quoting_agent flags availability issues, resolve them with inventory_agent
          BEFORE proceeding to order_agent.

        Combine all agent responses into a single coherent reply to the customer."""
    ),
    max_steps=12,
    verbosity_level=2,  # Set to 0 in production to suppress logs
)

def orchestrator(request: str) -> str:
    """
    Main entry point: the manager agent handles classification
    and delegation automatically via its reasoning loop.
    """
    response = manager_agent.run(request)
    return str(response)

# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        response = orchestrator(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
