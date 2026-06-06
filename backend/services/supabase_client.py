"""Supabase service — handles all database operations and Realtime updates.

Every agent calls push_update() at each step to update the dashboard in real-time.
Supabase Realtime detects the row change and pushes it to all subscribed browsers.

NOTE: supabase-py is synchronous. All DB calls are wrapped in asyncio.to_thread()
to avoid blocking the FastAPI event loop.
"""

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone
import asyncio

# Initialize Supabase client with service role key (backend has full access)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None


async def create_session(data: dict) -> str:
    """Create a new session row. Returns the session UUID."""
    if not supabase:
        return "mock-session-id"

    def _insert():
        result = supabase.table("sessions").insert({
            "user_id": data.get("user_id", "anonymous"),
            "business_name": data["business_name"],
            "business_type": data["business_type"],
            "menu": data.get("menu", []),
            "address": data.get("address", ""),
            "phone": data.get("phone", ""),
            "language": data.get("language", "hi"),
            "upi_id": data.get("upi_id", ""),
            "shop_photo_url": data.get("shop_photo_url"),
            "existing_logo_url": data.get("existing_logo_url"),
        }).execute()
        return result.data[0]["id"]

    return await asyncio.to_thread(_insert)


async def create_agent_tasks(session_id: str):
    """Create 6 agent_tasks rows (one per agent) for a session."""
    if not supabase:
        return

    def _insert():
        agents = ["brand", "website", "payment", "outreach", "gmb", "legal"]
        rows = [
            {
                "session_id": session_id,
                "agent_name": agent,
                "status": "pending",
                "progress": 0,
                "current_step": "Waiting to start...",
            }
            for agent in agents
        ]
        supabase.table("agent_tasks").insert(rows).execute()

    await asyncio.to_thread(_insert)


async def push_update(
    session_id: str,
    agent_name: str,
    progress: int,
    step: str,
    status: str = "running",
    result_data: dict = None,
):
    """Update an agent's progress in the database.
    
    This triggers Supabase Realtime, which pushes the update
    to all subscribed browsers in <200ms.
    
    Args:
        session_id: The session UUID
        agent_name: One of: brand, website, payment, outreach, gmb, legal
        progress: 0-100
        step: Human-readable status text (shown on agent card)
        status: pending | running | completed | error
        result_data: Agent-specific output (logo_url, website_url, etc.)
    """
    if not supabase:
        print(f"[{agent_name}] {progress}% -- {step}")
        return

    def _update():
        update = {
            "progress": progress,
            "current_step": step,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if result_data is not None:
            update["result_data"] = result_data

        supabase.table("agent_tasks").update(update).eq(
            "session_id", session_id
        ).eq("agent_name", agent_name).execute()

    await asyncio.to_thread(_update)


async def get_session(session_id: str) -> dict:
    """Fetch a session by ID."""
    if not supabase:
        return {}

    def _fetch():
        result = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
        return result.data

    return await asyncio.to_thread(_fetch)


async def get_session_if_owner(session_id: str, user_id: str) -> dict | None:
    """Fetch a session only if the user owns it. Returns None if not owned.

    This prevents IDOR (Insecure Direct Object Reference) attacks —
    users cannot access other users' sessions by guessing UUIDs.
    """
    if not supabase:
        return {}

    def _fetch():
        result = (
            supabase.table("sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    return await asyncio.to_thread(_fetch)


async def upload_to_storage(bucket: str, path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload a file to Supabase Storage. Returns the public URL."""
    if not supabase:
        return f"https://placeholder.storage/{path}"

    def _upload():
        supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": content_type})
        return supabase.storage.from_(bucket).get_public_url(path)

    return await asyncio.to_thread(_upload)

