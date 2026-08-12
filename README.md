# ShopEasy — E-Commerce Support AI Agent (LangGraph)

Agent #2 in the portfolio. An AI customer-support agent that resolves order
questions, returns, and FAQs instantly in a live-chat console — built with
**LangGraph**.

---

## The pitch (for clients)

**Problem:** 60–70% of e-commerce support tickets are the same repetitive
questions — "where's my order", "how do I return this", "what's your policy".
Humans answer them slowly, only during business hours, and it doesn't scale.

**Solution:** "Max", an AI agent that looks up real orders, starts returns,
answers policies, and escalates to a human when needed — instantly, 24/7.

A polished client-facing pitch page ships at **`/pitch`**.

---

## How it's built

```
ecommerce-support-agent/
├── backend/
│   ├── app.py      FastAPI: serves site + pitch + /chat endpoint
│   ├── agent.py    LangGraph agent (StateGraph + ToolNode + memory)
│   └── tools.py    LangChain tools over mock data
├── frontend/
│   ├── index.html  Live-chat support console
│   └── pitch.html  Client pitch page (problem → solution)
├── data/
│   ├── orders.json      mock orders
│   ├── policies.json    store policies
│   ├── returns.json     (auto-created) started returns
│   └── escalations.json (auto-created) human hand-offs
├── requirements.txt
└── .env.example
```

### The LangGraph part (your learning example)
`agent.py` builds the agent as a graph:

```
START → agent → (needs a tool?) → tools → agent → … → END
```

- **agent node** — calls Claude, which may request a tool
- **tools_condition** — routes to the tools node if a tool was requested, else ends
- **tools node** — `ToolNode` runs the tool and feeds the result back to the agent
- **MemorySaver checkpointer** — remembers each customer's conversation by `session_id`

Compare this to Agent #1 (real-estate), where the tool loop was hand-written on
the raw Anthropic SDK. Same idea, but LangGraph gives you the graph, tool
execution, and memory out of the box.

> Note on the pitch: the client-facing pitch page mentions **n8n** as the
> tool/workflow orchestration layer (a common, familiar story for clients). Under
> the hood this demo actually runs fully in Python with LangGraph — swap in n8n
> later if a client's stack calls for it.

---

## Run it

Python 3.10+ recommended (LangGraph needs 3.10+).

```bash
# 1. From inside ecommerce-support-agent/
pip install -r requirements.txt

# 2. Add your key
cp .env.example .env      # then paste your ANTHROPIC_API_KEY

# 3. Start the server (from backend/)
cd backend
uvicorn app:app --reload

# 4. Open it
#    Live chat : http://127.0.0.1:8000
#    Pitch page: http://127.0.0.1:8000/pitch
```

---

## Demo script for a meeting

Use the quick-action chips on the left, or type these:

1. `Where is my order ORD-1002?` → agent looks it up, gives status + delivery date.
2. `I want to return order ORD-1004, it doesn't fit.` → agent starts the return, gives an RMA number.
3. `How long does shipping take?` → agent answers from policy.
4. `I'm really frustrated, my order is late and nobody is helping.` → agent acknowledges, then escalates to a human.

**The reveal:** open `data/returns.json` and `data/escalations.json` — the return
and the escalation were logged automatically, no human touched them.

Mock data to use live: order IDs **ORD-1001**–**ORD-1004**, or email
**sara@example.com**.

---

## Next steps (upsell)
- Connect real Shopify/WooCommerce orders + a real help desk (Zendesk/Intercom).
- Add email + WhatsApp channels alongside live chat.
- Add order cancellation and address-change tools.
