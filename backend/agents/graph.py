"""LangGraph Graph — Wires all 6 agents into the supervisor loop.

Architecture:
  ┌─────────────┐
  │  Supervisor  │←─────────────────────────────────────┐
  │  (router)    │                                       │
  └──────┬───┬──┘                                       │
    Send │   │ Send (parallel)                          │
  ┌──────┘   └──────┐  ┌────────┐  ┌────────┐         │
  │Brand│   │Payment│  │Outreach│  │Legal   │         │
  └──┬──┘   └──┬────┘  └──┬─────┘  └──┬─────┘         │
     │         │           │           │                │
     └─────────┴───────────┴───────────┴─── merge ──── ┘
                                                        │
  Then:  Brand done → Website → Supervisor              │
  Then:  Website done → GMB → Supervisor → END          │
"""

from langgraph.graph import StateGraph, END
from agents.state import GenesisState
from agents.supervisor import supervisor_route
from agents.brand import brand_agent
from agents.payment import payment_agent
from agents.outreach import outreach_agent
from agents.legal import legal_agent
from agents.website import website_agent
from agents.gmb import gmb_agent
from services.supabase_client import push_update
import traceback
import operator
from typing import Annotated


# ═══════════════════════════════════════
# State with reducer for completed_agents
# (LangGraph needs to know HOW to merge
#  parallel agent outputs into one state)
# ═══════════════════════════════════════

class MergeableGenesisState(GenesisState):
    """GenesisState with a list-merge reducer for completed_agents.
    
    When 4 agents run in parallel and each returns
    completed_agents: ["brand"], completed_agents: ["payment"], etc.,
    LangGraph uses this reducer to merge them:
    completed_agents: ["brand", "payment", "outreach", "legal"]
    """
    completed_agents: Annotated[list[str], operator.add]


# ═══════════════════════════════════════
# Build the LangGraph
# ═══════════════════════════════════════

def build_graph():
    """Build and compile the GENESIS agent graph."""
    graph = StateGraph(MergeableGenesisState)

    # Add all 6 REAL agent nodes
    graph.add_node("brand", brand_agent)
    graph.add_node("payment", payment_agent)
    graph.add_node("outreach", outreach_agent)
    graph.add_node("legal", legal_agent)
    graph.add_node("website", website_agent)
    graph.add_node("gmb", gmb_agent)

    # Supervisor is a pass-through node that routes
    graph.add_node("supervisor", lambda state: state)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor conditionally routes to agents
    graph.add_conditional_edges("supervisor", supervisor_route)

    # All agents feed back to supervisor for next routing decision
    for agent_name in ["brand", "payment", "outreach", "legal", "website", "gmb"]:
        graph.add_edge(agent_name, "supervisor")

    return graph.compile()


async def run_genesis_graph(session_id: str, launch_data: dict):
    """Run the full GENESIS agent pipeline.
    
    Called as a background task from FastAPI.
    Creates initial state from launch data and runs all agents.
    """
    graph = build_graph()

    initial_state = {
        "session_id": session_id,
        "user_id": launch_data.get("user_id", "anonymous"),
        "business_name": launch_data["business_name"],
        "business_type": launch_data["business_type"],
        "menu": launch_data.get("menu", []),
        "address": launch_data.get("address", ""),
        "phone": launch_data.get("phone", ""),
        "language": launch_data.get("language", "hi"),
        "upi_id": launch_data.get("upi_id", ""),
        "shop_photo_url": launch_data.get("shop_photo_url"),
        "existing_logo_url": launch_data.get("existing_logo_url"),
        # Supervisor
        "completed_agents": [],
        # Agent outputs (empty initially)
        "logo_url": None,
        "primary_color": None,
        "secondary_color": None,
        "tagline_hindi": None,
        "tagline_english": None,
        "photo_urls": [],
        "website_url": None,
        "upi_qr_url": None,
        "invoice_page_url": None,
        "nearby_businesses": [],
        "whatsapp_links": [],
        "gmb_status": None,
        "legal_pdf_url": None,
        "legal_checklist": [],
    }

    try:
        print(f"\n{'='*60}")
        print(f"[GENESIS] Starting pipeline for: {launch_data['business_name']}")
        print(f"[GENESIS] Session ID: {session_id}")
        print(f"[GENESIS] All 6 REAL agents active!")
        print(f"{'='*60}\n")

        final_state = await graph.ainvoke(initial_state)

        print(f"\n{'='*60}")
        print(f"[GENESIS] Pipeline complete!")
        print(f"[GENESIS] Completed agents: {final_state.get('completed_agents', [])}")
        print(f"[GENESIS] Logo: {final_state.get('logo_url', 'N/A')}")
        print(f"[GENESIS] Website: {final_state.get('website_url', 'N/A')}")
        print(f"[GENESIS] Leads found: {len(final_state.get('nearby_businesses', []))}")
        print(f"{'='*60}\n")

        # Mark session as completed in Supabase
        from services.supabase_client import supabase
        if supabase:
            supabase.table("sessions").update(
                {"status": "completed"}
            ).eq("id", session_id).execute()

        return final_state

    except Exception as e:
        print(f"\n[GENESIS] PIPELINE ERROR: {traceback.format_exc()}")

        # Mark session as error
        from services.supabase_client import supabase
        if supabase:
            supabase.table("sessions").update(
                {"status": "error"}
            ).eq("id", session_id).execute()

        raise
