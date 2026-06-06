"""LangGraph Supervisor — Routes agents based on dependency graph.

Execution order:
  PARALLEL (no dependencies):
    brand, payment, outreach, legal → all fire simultaneously
  
  SEQUENTIAL (wait for deps):
    brand completes → website starts
    website completes → gmb starts

Communication:
  Agents do NOT talk to each other directly.
  They ALL read from and write to GenesisState.
  State is the shared memory. LangGraph manages merging.
"""

from agents.state import GenesisState


def get_next_agents(state: GenesisState) -> list[str]:
    """Determine which agents should run next based on completed agents.
    
    Returns a list of agent names to run in parallel,
    or ["__end__"] if all agents are done.
    """
    completed = set(state.get("completed_agents", []))
    to_run = []

    # Phase 1: These 4 run in parallel (no dependencies)
    parallel_agents = ["brand", "payment", "outreach", "legal"]
    for agent in parallel_agents:
        if agent not in completed:
            to_run.append(agent)

    if to_run:
        return to_run

    # Phase 2: Website needs brand to be done
    if "brand" in completed and "website" not in completed:
        return ["website"]

    # Phase 3: GMB needs website to be done
    if "website" in completed and "gmb" not in completed:
        return ["gmb"]

    # All done
    return ["__end__"]


def supervisor_route(state: GenesisState):
    """LangGraph conditional edge function.
    
    Returns either:
    - List of Send objects (for parallel execution)
    - "__end__" string (to finish the graph)
    """
    from langgraph.constants import Send

    next_agents = get_next_agents(state)

    if next_agents == ["__end__"]:
        return "__end__"

    # Fan out to multiple agents in parallel using Send
    return [Send(agent, state) for agent in next_agents]
