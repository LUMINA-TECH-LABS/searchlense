"""Example: Mode B — an agent that actually pauses at a checkpoint.

The agent's loop calls `await session.checkpoint()` at every iteration.
When the user (or the agent itself) requests a pause, the checkpoint
suspends the agent at the next boundary. Resume continues from the same
point.

Compare to Mode A (examples 01 and 02), where pause only freezes the view
and the agent keeps running.

To see it working: run this file and watch the printed output. The
director below simulates a user pausing, rewinding, and resuming while the
agent is mid-search. Notice that "[agent] step N" lines stop appearing
during the pause and resume exactly where they left off.
"""

import asyncio

from searchlense import ConsoleRenderer, DemoProvider, Session


async def agent_loop(session: Session, query: str) -> None:
    """A toy agent: it "thinks", then "searches", in a loop.

    The only searchlense-specific line is `await session.checkpoint()`.
    Everything else is the agent doing its own work.
    """
    steps = [
        "plan the search",
        "refine the query",
        "fetch sources",
        "extract snippets",
        "synthesize",
    ]

    for i, step in enumerate(steps):
        # === The one line that makes Mode B work ===
        # If a pause has been requested, this suspends here. When resume
        # arrives, execution continues from exactly this point.
        await session.checkpoint()
        # ==========================================

        print(f"[agent] step {i + 1}/{len(steps)}: {step}")

        # The agent does its real work here. In a real system this is where
        # you'd call your LLM, your tools, your scraper, etc. For this demo,
        # we just record a note in the ledger.
        session.ledger.append_raw(f"agent working on: {step}")

        await asyncio.sleep(0.4)


async def main() -> None:
    session = Session(
        provider=DemoProvider(delay=0.4),
        renderer=ConsoleRenderer(),
        speed=1.0,
    )

    async def director() -> None:
        """Simulates a user interacting with the workspace."""
        await asyncio.sleep(1.0)
        print("\n--- USER: pause ---\n")
        await session.pause()  # sets control signal AND pauses the view

        await asyncio.sleep(2.0)

        print("\n--- USER: rewind 2 ---\n")
        session.controller.rewind(2)

        print("\n--- USER: resume ---\n")
        await session.resume()

    await asyncio.gather(
        session.run("history of the printing press"),
        agent_loop(session, "history of the printing press"),
        director(),
    )


if __name__ == "__main__":
    asyncio.run(main())
