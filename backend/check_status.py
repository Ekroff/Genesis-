"""Check agent_tasks table for the latest session to see what agents did."""
import asyncio
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent to path
sys.path.insert(0, ".")
from services.supabase_client import supabase


async def main():
    if not supabase:
        print("[ERROR] No Supabase connection")
        return

    # Get latest session
    result = supabase.table("sessions").select("id, business_name, status, created_at").order("created_at", desc=True).limit(3).execute()

    if not result.data:
        print("[ERROR] No sessions found")
        return

    print("=== RECENT SESSIONS ===")
    for s in result.data:
        print(f"  {s['id'][:8]}... | {s['business_name']} | status={s.get('status','?')} | {s['created_at']}")

    latest_id = result.data[0]["id"]
    print(f"\n=== AGENT TASKS for session {latest_id[:8]}... ===\n")

    tasks = supabase.table("agent_tasks").select("agent_name, status, progress, current_step, result_data").eq("session_id", latest_id).order("agent_name").execute()

    if not tasks.data:
        print("[ERROR] No agent tasks found for this session")
        return

    for t in tasks.data:
        status_icon = {"completed": "[OK]", "running": "[..]", "pending": "[--]", "error": "[!!]"}.get(t["status"], "[??]")
        print(f"{status_icon} {t['agent_name']:10s} | {t['progress']:3d}% | {t['status']:10s} | {t['current_step']}")
        if t.get("result_data"):
            rd = t["result_data"]
            # Show key outputs
            for key in ["logo_url", "website_url", "upi_qr_url", "invoice_page_url", "legal_pdf_url", "whatsapp_links", "nearby_businesses", "category_primary"]:
                if key in rd:
                    val = rd[key]
                    if isinstance(val, list):
                        print(f"           -> {key}: [{len(val)} items]")
                    elif isinstance(val, str) and len(val) > 80:
                        print(f"           -> {key}: {val[:80]}...")
                    else:
                        print(f"           -> {key}: {val}")


if __name__ == "__main__":
    asyncio.run(main())
