"""
Conversation memory — LangGraph checkpointer factory and lifecycle.

CLAUDE.md learning checkpoint #11: "where memory goes."

In LangGraph 1.x, multi-turn conversation memory is implemented by attaching
a `BaseCheckpointSaver` to the compiled graph. The graph snapshots its state
(messages, scratch values, etc.) to the saver after every step, keyed by
`thread_id` (passed via `config={"configurable": {"thread_id": ...}}`).
Subsequent runs with the same thread_id resume from the last snapshot —
the LLM sees the prior turns automatically without any caller-side message
threading.

This module is the single seam where the checkpointer is constructed and
its lifecycle is managed. Three backends; one env-driven choice:

    memory     InMemorySaver — process-local, lost on restart. Dev only.
    sqlite     AsyncSqliteSaver — file-backed, single-writer, survives
               restart. Good for single-process / hobby deployments.
    postgres   AsyncPostgresSaver — concurrent writers, the production
               choice. Requires an existing reachable database.

Why a process-wide singleton (rather than per-request construction):
    InMemorySaver's data lives inside the saver instance. If we made a new
    InMemorySaver per request, every "remembered" message would be lost the
    moment the request returned. Even sqlite/postgres benefit — opening and
    tearing down a connection per turn is wasteful (~ms of overhead, plus
    schema-check round trips for setup()). One long-lived saver per process
    is the LangGraph-recommended shape.

Why an AsyncExitStack:
    `AsyncSqliteSaver.from_conn_string()` and `AsyncPostgresSaver.from_conn_string()`
    return async context managers that own real I/O resources (file handles,
    connection pools). They MUST be closed on shutdown. The exit stack
    captures whatever needs closing without each branch having to remember
    its own teardown — `aclose()` runs the right finalizers in LIFO order.

Why a lock around lazy init:
    The first request to call `get_checkpointer()` initializes the singleton.
    Under a multi-worker FastAPI host (or just two near-simultaneous CLI
    invocations sharing a process — uncommon, but possible) two coroutines
    could race into the constructor, opening two connections and leaking one.
    The lock is acquired only on the slow path; the hot path is a plain
    pointer read and stays cheap.

Optional dependencies:
    The sqlite and postgres backends require packages that are not pulled
    in by default. Install them on demand:

        pip install -e ".[memory-sqlite]"
        pip install -e ".[memory-postgres]"
 
    Imports are deferred into the relevant branch so a deployment that only
    uses the default in-memory backend never has to install the extras.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

from agent.config import settings

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver

log = logging.getLogger(__name__)

# Process-wide singleton state. Guarded by `_init_lock` for first-call init;
# subsequent reads are lock-free (pointer assignment is atomic in CPython).
_checkpointer: "BaseCheckpointSaver | None" = None
_exit_stack: AsyncExitStack | None = None
_init_lock = asyncio.Lock()


async def get_checkpointer() -> "BaseCheckpointSaver | None":
    """
    Return the shared checkpointer for this process, building it on first
    use. Returns None when memory is disabled — callers treat that as
    "stateless mode" and pass nothing to `create_agent(checkpointer=...)`.

    Safe to call from any number of concurrent coroutines; the constructor
    runs at most once per process.
    """
    global _checkpointer, _exit_stack

    if not settings.memory_enabled:
        return None

    # Fast path — already built. Pointer read is atomic in CPython, so no
    # lock is needed once the singleton is published.
    if _checkpointer is not None:
        return _checkpointer

    async with _init_lock:
        # Re-check inside the lock — another coroutine may have built it
        # while we were waiting.
        if _checkpointer is not None:
            return _checkpointer

        backend = settings.memory_backend.lower().strip()
        log.info("Initialising conversation memory: backend=%s", backend)

        stack = AsyncExitStack()
        try:
            if backend == "memory":
                # InMemorySaver is sync-only and has no resources to close,
                # but we still register it on the stack for symmetry — the
                # `aclose()` is a no-op for it.
                from langgraph.checkpoint.memory import InMemorySaver
                saver: "BaseCheckpointSaver" = InMemorySaver()
                log.warning(
                    "InMemorySaver is process-local — conversation history is "
                    "lost on restart. Switch to sqlite or postgres for production."
                )

            elif backend == "sqlite":
                # AsyncSqliteSaver lives in langgraph-checkpoint-sqlite. Lazy
                # import so deployments using the default backend don't pay
                # for the dep.
                try:
                    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
                except ImportError as exc:
                    raise RuntimeError(
                        "MEMORY_BACKEND=sqlite requires the langgraph-checkpoint-sqlite "
                        "package. Install it with: pip install -e \".[memory-sqlite]\""
                    ) from exc

                # `from_conn_string` returns an async context manager that
                # owns the underlying aiosqlite connection. Hand it to the
                # exit stack so shutdown closes it cleanly.
                cm = AsyncSqliteSaver.from_conn_string(settings.memory_sqlite_path)
                saver = await stack.enter_async_context(cm)
                # First-time table creation. Idempotent — safe to call on
                # every startup. Cheap enough that we don't bother gating it.
                await saver.setup()
                log.info("SQLite checkpointer ready at %s", settings.memory_sqlite_path)

            elif backend == "postgres":
                if not settings.memory_postgres_url:
                    raise RuntimeError(
                        "MEMORY_BACKEND=postgres requires MEMORY_POSTGRES_URL to be set "
                        "(e.g. postgresql://user:pass@host:5432/dbname)."
                    )
                try:
                    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                except ImportError as exc:
                    raise RuntimeError(
                        "MEMORY_BACKEND=postgres requires the langgraph-checkpoint-postgres "
                        "package. Install it with: pip install -e \".[memory-postgres]\""
                    ) from exc

                cm = AsyncPostgresSaver.from_conn_string(settings.memory_postgres_url)
                saver = await stack.enter_async_context(cm)
                # Postgres setup() runs the schema migrations. Required on
                # first ever run; idempotent on later runs. The LangGraph
                # docs explicitly call this out — without it, the first
                # write fails with "table does not exist."
                await saver.setup()
                log.info(
                    "Postgres checkpointer ready (db=%s)",
                    # Don't log credentials — only the host portion past the @.
                    settings.memory_postgres_url.rsplit("@", 1)[-1]
                    if "@" in settings.memory_postgres_url
                    else "<configured>",
                )

            else:
                raise RuntimeError(
                    f"Unknown MEMORY_BACKEND={backend!r}. "
                    "Supported: memory, sqlite, postgres."
                )

            # Publish the singleton. Order matters: the stack must be saved
            # alongside the saver so shutdown_checkpointer() can close it.
            _exit_stack = stack
            _checkpointer = saver
            return saver

        except BaseException:
            # If anything went wrong during init, unwind whatever we already
            # opened so we don't leak a half-initialised connection.
            await stack.aclose()
            raise


async def shutdown_checkpointer() -> None:
    """
    Close the shared checkpointer and release its underlying resources.

    Call from a FastAPI lifespan handler (`@asynccontextmanager` on app
    startup/shutdown) or from a CLI's `finally` block. Safe to call when
    memory is disabled or never initialised — both are no-ops.

    Idempotent: a second call after shutdown returns immediately.
    """
    global _checkpointer, _exit_stack

    if _exit_stack is None:
        return

    log.info("Shutting down conversation memory checkpointer")
    try:
        await _exit_stack.aclose()
    except Exception:
        # Don't let a flaky teardown mask a real error elsewhere — log and
        # move on. The process is exiting anyway in the common case.
        log.exception("Error during checkpointer shutdown (continuing)")
    finally:
        _exit_stack = None
        _checkpointer = None
