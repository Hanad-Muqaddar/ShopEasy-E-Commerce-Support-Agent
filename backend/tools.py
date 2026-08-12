"""
tools.py
--------
The agent's tools, written as LangChain tools (the @tool decorator) so LangGraph's
ToolNode can run them automatically. The LLM decides WHEN to call them.

For the demo these read/write local JSON. In a real client deployment you'd
change the function bodies to hit their store's API (Shopify, WooCommerce),
help-desk (Zendesk), and payment provider — the tool signatures stay the same.
"""

import json
import os
from datetime import datetime

from langchain_core.tools import tool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
POLICIES_FILE = os.path.join(DATA_DIR, "policies.json")
RETURNS_FILE = os.path.join(DATA_DIR, "returns.json")
ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")


def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _append(path, record):
    records = _load(path, [])
    records.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


@tool
def get_order_status(order_id: str = "", email: str = "") -> str:
    """Look up the FULL details of an order so you can answer any question about
    it — status, items, total cost, carrier, tracking number, and dates. Provide
    either the order_id (e.g. ORD-1001) or the customer's email. Returns all order
    details or a not-found message."""
    orders = _load(ORDERS_FILE, [])
    matches = []
    for o in orders:
        if order_id and o["order_id"].lower() == order_id.lower():
            matches.append(o)
        elif email and o["email"].lower() == email.lower():
            matches.append(o)

    if not matches:
        return "No order found. Please double-check the order ID or the email used at checkout."

    blocks = []
    for o in matches:
        tracking = f"{o['tracking']} ({o['carrier']})" if o.get("tracking") else "not shipped yet"
        carrier = o.get("carrier") or "not assigned yet"
        blocks.append(
            f"Order {o['order_id']} — {o['customer']}\n"
            f"  Items: {', '.join(o['items'])}\n"
            f"  Total cost: ${o['total']:.2f}\n"
            f"  Status: {o['status']}\n"
            f"  Carrier: {carrier}\n"
            f"  Tracking: {tracking}\n"
            f"  Ordered on: {o['ordered_on']}\n"
            f"  Estimated delivery: {o['estimated_delivery']}"
        )
    return "\n\n".join(blocks)


@tool
def start_return(order_id: str, reason: str = "") -> str:
    """Start a return/refund for an order. Only works for orders that are Delivered.
    Requires the order_id and a short reason."""
    orders = _load(ORDERS_FILE, [])
    order = next((o for o in orders if o["order_id"].lower() == order_id.lower()), None)
    if not order:
        return f"Order {order_id} not found."
    if order["status"] != "Delivered":
        return (f"Order {order_id} is '{order['status']}', not delivered yet, so it "
                f"can't be returned. You can cancel or wait until it arrives.")

    rma = f"RMA-{order_id.split('-')[-1]}"
    _append(RETURNS_FILE, {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "rma": rma,
        "order_id": order_id,
        "customer": order["customer"],
        "reason": reason,
        "status": "Return started",
    })
    return (f"Return started for {order_id}. Your return number is {rma}. "
            f"We've emailed you a prepaid label. Refund of ${order['total']:.2f} will be "
            f"issued 5-7 business days after we receive the item.")


@tool
def get_policy(topic: str) -> str:
    """Answer a store policy question. Valid topics: returns, shipping, sizing,
    refunds, payment."""
    policies = _load(POLICIES_FILE, {})
    key = topic.lower().strip()
    if key in policies:
        return policies[key]
    return ("I can help with returns, shipping, sizing, refunds, or payment. "
            "Which one would you like to know about?")


@tool
def escalate_to_human(summary: str, contact: str = "") -> str:
    """Escalate to a human support agent when the issue is complex, the customer
    is upset, or it's outside what you can resolve. Provide a short summary and
    the customer's contact if known."""
    _append(ESCALATIONS_FILE, {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "contact": contact,
        "status": "Open",
    })
    return ("I've passed this to a human support agent who will follow up shortly. "
            "Is there anything else I can help with in the meantime?")


# All tools, exported for the LangGraph agent to bind.
TOOLS = [get_order_status, start_return, get_policy, escalate_to_human]
