# Memory in LangGraph Agents — A Complete Practical Guide

> **Who this is for:** You've already built an agent with `create_react_agent`. It works, but it has no memory — every conversation starts from zero. This guide walks you through adding memory, understanding what's actually happening under the hood, and tuning it when things go wrong.

---

## Before We Start: One Concept to Internalize

Imagine two different kinds of memory a human assistant might have:

- **During a meeting**: they remember everything said *in that meeting*. Once the meeting ends, that context is gone.
- **Across all meetings**: they remember facts about you — your preferences, your past projects, your name — regardless of when they last spoke to you.

LangGraph has a direct equivalent for each:

| Human Memory | LangGraph Equivalent | Backed By |
|---|---|---|
| Within one meeting | **Short-term / Thread memory** | Checkpointer |
| Across all meetings | **Long-term / Cross-session memory** | Store |

These are two separate systems. You can use one or both. Most agents start with short-term only and add long-term later.

---

## Part 1: Short-Term Memory

### What it does

Without short-term memory, your agent has no idea what was said earlier in the *same conversation*. Each `.invoke()` call is treated as a brand new conversation.

```python
# Without memory — the agent forgets Bob immediately
agent.invoke({"messages": [{"role": "user", "content": "My name is Bob"}]})
agent.invoke({"messages": [{"role": "user", "content": "What is my name?"}]})
# Agent: "I don't know your name."  ← No memory
```

With short-term memory, the agent remembers everything within that session.

### How it works under the hood

Every time your agent processes a message, LangGraph saves the **entire conversation state** (all messages so far) to a **checkpointer**. Think of a checkpointer as a database that stores conversation snapshots.

When you invoke the agent again with the same `thread_id`, LangGraph:
1. Loads the saved state from the checkpointer
2. Appends your new message
3. Runs the agent with the full history
4. Saves the updated state back

The `thread_id` is the key that identifies *which conversation* to load. Different users = different `thread_id`s.

```
thread_id: "user-alice-session-1"
  └── Checkpoint: [msg1, msg2, msg3, ...]

thread_id: "user-bob-session-1"
  └── Checkpoint: [msg1, msg2, ...]
```

### Adding short-term memory

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# 1. Create a checkpointer
checkpointer = InMemorySaver()

# 2. Pass it to create_agent
agent = create_agent(
    "gpt-4o",
    tools=[your_tool],
    checkpointer=checkpointer,
)

# 3. Always pass a thread_id when invoking
config = {"configurable": {"thread_id": "user-alice-session-1"}}

agent.invoke({"messages": [{"role": "user", "content": "My name is Bob"}]}, config)
agent.invoke({"messages": [{"role": "user", "content": "What is my name?"}]}, config)
# Agent: "Your name is Bob!"  ← Memory works
```

That's it. Two changes: add `checkpointer=` and always pass `thread_id`.

### Choosing the right checkpointer

`InMemorySaver` stores everything in RAM. It's perfect for development, but it's wiped when your process restarts. For anything real, use a database-backed checkpointer.

```python
# Development — data lives in RAM, gone on restart
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()

# Local dev with persistence — data survives restarts
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Production — use Postgres
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
checkpointer.setup()  # creates the necessary tables once

# High-traffic async production
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
```

> **Rule of thumb:** `InMemorySaver` in notebooks and quick tests. `SqliteSaver` when you want to iterate without losing history. `PostgresSaver` in production.

---

## Part 2: The Context Window Problem

Once short-term memory is working, a new problem appears: conversations get long. LLMs have a maximum number of tokens they can process at once (the context window). If your conversation history exceeds that, the agent crashes — or starts performing poorly well before it crashes.

Even within the limit, LLMs get "distracted" by old, irrelevant messages. A 100-message history makes the model worse, not better.

You need a strategy to keep history lean. LangGraph gives you three, all implemented via a `@before_model` middleware hook that runs *before* the LLM sees the messages.

### Strategy 1: Trim — Keep the last N messages

The simplest approach. Discard old messages, always keep the most recent ones. One caveat: always keep the first message (the system prompt), if you have one.

```python
from langchain.agents.middleware import before_model
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver

MAX_MESSAGES = 10  # tune this number

@before_model
def trim_old_messages(state: AgentState, runtime) -> dict | None:
    messages = state["messages"]

    # If we're under the limit, do nothing
    if len(messages) <= MAX_MESSAGES:
        return None

    # Keep the first message (system prompt) + last MAX_MESSAGES messages
    kept = [messages[0]] + messages[-MAX_MESSAGES:]

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),  # wipe current state
            *kept                                    # replace with trimmed set
        ]
    }

agent = create_agent(
    "gpt-4o",
    tools=[your_tool],
    middleware=[trim_old_messages],
    checkpointer=InMemorySaver(),
)
```

**When to use:** General-purpose chatbots and assistants where recent context is what matters.

**Tradeoff:** Old facts get lost. If a user said their name in message 1 and you've trimmed past that, the agent will forget.

---

### Strategy 2: Summarize — Compress old history into a summary

Instead of deleting old messages, you summarize them into a single "summary" message and remove the originals. This preserves the gist of what was said without keeping all the tokens.

```python
from langchain.agents.middleware import before_model
from langchain.messages import RemoveMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI

SUMMARIZE_AFTER = 12   # compress when history exceeds this
KEEP_RECENT = 4        # always keep the last N messages verbatim

summarizer_llm = ChatOpenAI(model="gpt-4o-mini")  # cheap model for summaries

@before_model
def summarize_old_messages(state: AgentState, runtime) -> dict | None:
    messages = state["messages"]

    if len(messages) <= SUMMARIZE_AFTER:
        return None

    # Split: old messages to summarize vs. recent ones to keep verbatim
    to_summarize = messages[:-KEEP_RECENT]
    recent = messages[-KEEP_RECENT:]

    # Ask a cheap model to summarize the old messages
    summary_prompt = (
        "Summarize the following conversation concisely. "
        "Preserve important facts (names, preferences, decisions):\n\n"
        + "\n".join(f"{m.type}: {m.content}" for m in to_summarize)
    )
    summary = summarizer_llm.invoke([HumanMessage(content=summary_prompt)])

    summary_message = SystemMessage(content=f"[Earlier conversation summary]: {summary.content}")

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            summary_message,
            *recent
        ]
    }

agent = create_agent(
    "gpt-4o",
    tools=[your_tool],
    middleware=[summarize_old_messages],
    checkpointer=InMemorySaver(),
)
```

**When to use:** Long-running assistants, support agents, or any case where facts from early in the conversation are important.

**Tradeoff:** Extra LLM call per compression step (costs tokens + adds latency). Use a cheap, fast model like `gpt-4o-mini` for this.

---

### Strategy 3: Delete specific messages

Sometimes you want surgical control — for example, removing tool call messages once they've been processed (they tend to be verbose and rarely useful after the fact).

```python
from langchain.messages import RemoveMessage, ToolMessage

@before_model
def remove_tool_messages(state: AgentState, runtime) -> dict | None:
    messages = state["messages"]
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    
    if not tool_msgs:
        return None
    
    return {"messages": [RemoveMessage(id=m.id) for m in tool_msgs]}
```

**When to use:** Agents that make many tool calls and you want to keep history clean.

---

## Part 3: Long-Term Memory

### The problem short-term memory can't solve

Short-term memory (the checkpointer) is tied to a `thread_id`. A new thread = a blank slate.

So if Alice comes back tomorrow and starts a new conversation (new `thread_id`), your agent will have completely forgotten her name, preferences, and everything from last time.

This is long-term memory's job: store facts about users (or the agent itself) in a way that survives across sessions.

```
Thread 1 (yesterday): Alice says she loves Python and prefers dark mode
Thread 2 (today):     Agent already knows this — even though it's a new thread
```

### The Store: LangGraph's long-term memory system

The store is a key-value database that lives *outside* of threads. You namespace entries by user (or whatever scope makes sense), and retrieve them at the start of each conversation.

```python
from langgraph.store.memory import InMemoryStore

# For development
store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": "openai:text-embedding-3-small",  # enables semantic search
    }
)
```

The `index` config is optional but powerful — with it, you can search memories by *meaning* rather than exact match. More on this shortly.

### Wiring both checkpointer and store together

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.utils.config import get_store

store = InMemoryStore(index={"dims": 1536, "embed": "openai:text-embedding-3-small"})
checkpointer = InMemorySaver()

def inject_memories(state):
    """Runs before each LLM call. Fetches relevant memories and injects into system prompt."""
    store = get_store()
    user_id = state.get("user_id", "default")

    # Search for memories relevant to the latest user message
    memories = store.search(
        ("user_memories", user_id),        # namespace — scoped per user
        query=state["messages"][-1].content,
        limit=5,                           # how many memories to retrieve
    )

    memory_text = "\n".join(m.value["content"] for m in memories) if memories else "None yet."

    system = f"""You are a helpful assistant.

Here is what you know about this user from past conversations:
{memory_text}

Use this context naturally. Don't announce that you remember things — just use them."""

    return [{"role": "system", "content": system}, *state["messages"]]


agent = create_agent(
    "gpt-4o",
    tools=[your_tool],
    prompt=inject_memories,      # called before each LLM invocation
    checkpointer=checkpointer,   # short-term: within a thread
    store=store,                 # long-term: across all threads
)
```

### Writing memories

Fetching is half the job — you also need to *write* to the store. There are two approaches:

#### Option A: Agent-controlled (Hot Path)

Give the agent a tool to save memories. The agent decides when something is worth remembering.

```python
from langchain_core.tools import tool
from langgraph.utils.config import get_store
import uuid

@tool
def save_memory(content: str, user_id: str) -> str:
    """Save an important fact about the user for future conversations."""
    store = get_store()
    store.put(
        ("user_memories", user_id),   # namespace
        str(uuid.uuid4()),            # unique key for this memory
        {"content": content},         # the memory itself
    )
    return f"Saved: {content}"

agent = create_agent(
    "gpt-4o",
    tools=[your_tool, save_memory],   # agent can now call save_memory
    prompt=inject_memories,
    checkpointer=checkpointer,
    store=store,
)
```

The agent will now write memories when it judges something worth saving. You can guide this with a line in the system prompt:

```
"If the user shares a preference, fact about themselves, or important context, 
save it using the save_memory tool."
```

**Tradeoff:** Adds latency (tool call on save). Agent may over-save or under-save. Tunable via prompting.

#### Option B: Background Task (Off Hot Path)

A separate process periodically reads completed conversations and extracts memories. The primary agent flow has zero added latency.

```python
async def extract_and_store_memories(conversation_messages: list, user_id: str, store):
    """Run this after a conversation ends, or on a schedule."""
    extraction_prompt = f"""
    Review this conversation and extract facts worth remembering about the user.
    Return a JSON list of strings. Only include concrete facts, preferences, or decisions.
    Conversation:
    {[f"{m['role']}: {m['content']}" for m in conversation_messages]}
    """
    
    result = await llm.ainvoke([{"role": "user", "content": extraction_prompt}])
    facts = json.loads(result.content)  # e.g., ["Prefers Python", "Works at Acme Corp"]
    
    for fact in facts:
        store.put(
            ("user_memories", user_id),
            str(uuid.uuid4()),
            {"content": fact},
        )
```

**Tradeoff:** Facts from the current conversation aren't available until extraction runs. Requires orchestration logic.

---

## Part 4: The Three Types of Long-Term Memory

Knowing *what* to store shapes how you structure your memories. There are three useful categories:

### 1. Semantic Memory — Facts about a user or domain

"Alice prefers Python", "Bob works at Acme", "The user's timezone is IST".

Store as a **Profile** (single JSON doc, continually updated) or a **Collection** (many small docs, one per fact).

| | Profile | Collection |
|---|---|---|
| Structure | One JSON object | Many individual documents |
| Update style | Replace/patch the whole thing | Add/edit/delete individual items |
| Good for | Well-defined attributes (name, prefs, timezone) | Open-ended, growing knowledge |
| Risk | Gets unwieldy at scale | Agent may over-insert duplicates |

```python
# Profile style — one document per user
store.put(
    ("user_profile", user_id),
    "profile",   # fixed key — always overwrite
    {
        "name": "Alice",
        "prefers_language": "Python",
        "timezone": "IST",
        "dark_mode": True,
    }
)

# Collection style — one document per fact
store.put(
    ("user_facts", user_id),
    str(uuid.uuid4()),   # new key per fact
    {"content": "Alice prefers Python for data work"}
)
```

### 2. Episodic Memory — What the agent has done before

"Last time I helped Alice debug a pandas script", "Bob asked me to write a poem in haiku format and loved it".

Stored as past examples, retrieved when a similar task comes up. Essentially few-shot examples that the agent builds over time.

```python
store.put(
    ("agent_episodes", user_id),
    str(uuid.uuid4()),
    {
        "task": "data analysis",
        "example": "User had a pandas DataFrame with duplicate rows. Solution: df.drop_duplicates()",
        "feedback": "positive"
    }
)
```

When the user asks a data-related question later, you search this namespace and inject relevant past episodes into the prompt.

### 3. Procedural Memory — How the agent should behave

"This user prefers short, bullet-pointed answers", "Always use metric units for this user", "When summarizing, use 3 bullet points max".

This is learned behavior that updates the agent's *instructions* over time, not just its knowledge.

```python
store.put(
    ("agent_instructions", user_id),
    "response_style",  # fixed key — overwritten as preferences evolve
    {
        "instructions": (
            "Always respond in bullet points. "
            "Keep answers under 5 sentences. "
            "Use metric units."
        )
    }
)

# Then in your prompt function:
def inject_memories(state):
    store = get_store()
    user_id = state.get("user_id", "default")
    
    instructions_doc = store.get(("agent_instructions", user_id), "response_style")
    instructions = instructions_doc.value["instructions"] if instructions_doc else ""
    
    system = f"You are a helpful assistant.\n\nUser preferences:\n{instructions}"
    return [{"role": "system", "content": system}, *state["messages"]]
```

---

## Part 5: Store Options for Production

Just like the checkpointer, `InMemoryStore` is dev-only. Here are your production options:

```python
# Postgres — most common production choice
from langgraph.checkpoint.postgres import PostgresStore
store = PostgresStore.from_conn_string("postgresql://...")
store.setup()  # creates tables once

# Redis — best for low latency + semantic search
# pip install langgraph-checkpoint-redis
from langgraph_checkpoint_redis import RedisStore
store = RedisStore("redis://localhost:6379")

# MongoDB — flexible documents, good if you're already on Mongo
from langgraph_mongodb import MongoDBStore
```

---

## Part 6: Putting It All Together

Here's a complete, production-ready pattern that uses both short-term and long-term memory with all three memory types:

```python
import uuid
import json
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.utils.config import get_store
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

# ── Infrastructure ────────────────────────────────────────────────────────────

DB_URI = "postgresql://..."

checkpointer = PostgresSaver.from_conn_string(DB_URI)
checkpointer.setup()

store = PostgresStore.from_conn_string(DB_URI)
store.setup()


# ── Context window management ─────────────────────────────────────────────────

MAX_MESSAGES = 20

@before_model
def trim_history(state: AgentState, runtime) -> dict | None:
    messages = state["messages"]
    if len(messages) <= MAX_MESSAGES:
        return None
    kept = [messages[0]] + messages[-MAX_MESSAGES:]
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *kept]}


# ── Memory tools ──────────────────────────────────────────────────────────────

@tool
def save_user_memory(content: str, memory_type: str, user_id: str) -> str:
    """
    Save an important fact about the user.
    memory_type: 'fact' | 'preference' | 'instruction'
    """
    s = get_store()
    namespace = ("user_memory", user_id, memory_type)
    s.put(namespace, str(uuid.uuid4()), {"content": content})
    return f"Saved {memory_type}: {content}"


# ── Prompt with memory injection ──────────────────────────────────────────────

def build_prompt(state):
    s = get_store()
    user_id = state.get("user_id", "anonymous")
    latest = state["messages"][-1].content

    # Semantic search across all memory types
    facts       = s.search(("user_memory", user_id, "fact"),        query=latest, limit=3)
    prefs       = s.search(("user_memory", user_id, "preference"),  query=latest, limit=3)
    instruct    = s.search(("user_memory", user_id, "instruction"), query=latest, limit=2)

    def fmt(mems): return "\n".join(f"- {m.value['content']}" for m in mems) or "None"

    system = f"""You are a helpful assistant.

## What you know about this user
Facts: {fmt(facts)}
Preferences: {fmt(prefs)}
How they like responses: {fmt(instruct)}

Use this context naturally. If the user shares something new worth remembering, 
use the save_user_memory tool to store it."""

    return [{"role": "system", "content": system}, *state["messages"]]


# ── Agent ─────────────────────────────────────────────────────────────────────

agent = create_agent(
    "gpt-4o",
    tools=[your_tool, save_user_memory],
    prompt=build_prompt,
    middleware=[trim_history],
    checkpointer=checkpointer,
    store=store,
)


# ── Usage ─────────────────────────────────────────────────────────────────────

config = {"configurable": {"thread_id": "alice-session-42"}}
initial_state = {
    "messages": [{"role": "user", "content": "I prefer Python and always use pandas for data work."}],
    "user_id": "alice-123",
}

response = agent.invoke(initial_state, config)
```

---

## Quick Reference: What Goes Where

```
Short-term (checkpointer)       Long-term (store)
─────────────────────────       ──────────────────────────────
Conversation history            User facts and preferences
Tool call results               How the user likes responses
Intermediate agent state        Past examples (few-shot)
Scoped to thread_id             Scoped to user_id (or any custom key)
Gone when thread ends           Persists forever (until you delete it)
```

## Common Mistakes to Avoid

**1. Using checkpointer for cross-session memory**
The checkpointer is tied to a `thread_id`. A new session = new `thread_id` = blank slate. If you want facts to survive across sessions, they go in the store, not the checkpointer.

**2. Forgetting to pass `thread_id`**
Every `invoke()` call needs `{"configurable": {"thread_id": "..."}}`. Without it, LangGraph has no idea which conversation to load.

**3. Using `InMemorySaver` / `InMemoryStore` in production**
Both are wiped on restart. Use `PostgresSaver` + `PostgresStore` (or Redis equivalents) for anything you care about.

**4. Putting all users in the same namespace**
Always include `user_id` in the namespace: `("user_memory", user_id, "facts")`, not just `("user_memory", "facts")`. Skipping this means every user shares the same memories.

**5. Not managing context window growth**
Short-term memory grows unbounded by default. Add a `@before_model` trim or summarize middleware from day one.