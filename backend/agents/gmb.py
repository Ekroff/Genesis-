"""GMB Agent — Prepares and optionally automates Google Business Profile listing.

What it produces:
- Structured GMB profile data (categories, descriptions, hours, attributes)
- Optional: browser-use automation to fill the Google Business form

Dependencies: Website Agent must complete first (needs website URL)
Writes to state: gmb_status

Browser-use integration:
  When browser-use + playwright are installed, the agent can automate
  filling the Google Business Profile creation form. Otherwise, it
  provides pre-filled data for manual submission.

  Install: pip install browser-use playwright
  Then:    playwright install chromium
"""

from agents.state import GenesisState
from services.supabase_client import push_update
from services.gemini_client import generate_json
import traceback

# Check if browser-use is available
try:
    from browser_use import Agent, Browser
    from langchain_google_genai import ChatGoogleGenerativeAI
    from config import GEMINI_API_KEY
    HAS_BROWSER_USE = True
except ImportError:
    HAS_BROWSER_USE = False
    print("[GMBAgent] browser-use not available — running in data-only mode")


async def gmb_agent(state: GenesisState) -> dict:
    """Run the GMB Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Prepare Business Data (0% → 30%)
        # ══════════════════════════════════════
        await push_update(sid, "gmb", 10, "Preparing Google Business data... 📍")

        business_name = state["business_name"]
        business_type = state.get("business_type", "")
        address = state.get("address", "")
        phone = state.get("phone", "")
        website_url = state.get("website_url", "")

        # ══════════════════════════════════════
        # PHASE 2: Generate GMB Profile via Gemini (30% → 65%)
        # ══════════════════════════════════════
        await push_update(sid, "gmb", 30, "Generating business profile... ✍️")

        gmb_data = await generate_json(f"""
You are a Google Business Profile expert. Create optimized listing data.

Business Name: {business_name}
Business Type: {business_type}
Address: {address}
Phone: {phone}
Website: {website_url or "Not yet available"}

Return JSON:
{{
    "business_name": "{business_name}",
    "category_primary": "Google Business primary category (exact Google category name, e.g., 'Indian Restaurant', 'Hair Salon', 'Tutor')",
    "category_secondary": ["List of 2-3 secondary Google categories"],
    "description_english": "Business description in English (max 750 chars, SEO optimized, include location and what you offer)",
    "description_hindi": "Business description in Hindi (max 750 chars, warm and inviting tone)",
    "opening_hours": {{
        "monday": "09:00 - 21:00",
        "tuesday": "09:00 - 21:00",
        "wednesday": "09:00 - 21:00",
        "thursday": "09:00 - 21:00",
        "friday": "09:00 - 21:00",
        "saturday": "09:00 - 21:00",
        "sunday": "10:00 - 20:00"
    }},
    "attributes": ["List of 3-5 relevant GMB attributes like 'Delivery', 'Takeaway', 'Online appointments'"],
    "service_area": "Service area description (e.g., '5 km radius from address' or 'City name')",
    "short_name": "Suggested short name for g.page URL (lowercase, no spaces, max 15 chars)"
}}

Make the descriptions include local keywords for better search visibility.
Opening hours should be realistic for a {business_type} in India.
""")

        await push_update(sid, "gmb", 60, "Profile data ready! 📋")

        # Build the complete GMB profile
        gmb_profile = {
            "business_name": gmb_data.get("business_name", business_name),
            "category_primary": gmb_data.get("category_primary", ""),
            "category_secondary": gmb_data.get("category_secondary", []),
            "description_english": gmb_data.get("description_english", ""),
            "description_hindi": gmb_data.get("description_hindi", ""),
            "address": address,
            "phone": phone,
            "website": website_url,
            "opening_hours": gmb_data.get("opening_hours", {}),
            "attributes": gmb_data.get("attributes", []),
            "service_area": gmb_data.get("service_area", ""),
            "short_name": gmb_data.get("short_name", ""),
            "listing_url": "https://business.google.com/create",
        }

        # ══════════════════════════════════════
        # PHASE 3: Browser Automation (65% → 90%)
        # ══════════════════════════════════════
        gmb_status = "data_ready"

        if HAS_BROWSER_USE:
            try:
                await push_update(sid, "gmb", 70, "Starting browser automation... 🤖")

                # Use browser-use to automate GMB form filling
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=GEMINI_API_KEY,
                )

                browser = Browser()
                
                task_description = f"""
Go to https://business.google.com/create and help set up a Google Business Profile.

Business Details:
- Name: {business_name}
- Category: {gmb_data.get("category_primary", business_type)}
- Address: {address}
- Phone: {phone}
- Website: {website_url or "skip this field"}
- Description: {gmb_data.get("description_english", "")}

Steps:
1. Navigate to the Google Business Profile creation page
2. Enter the business name: "{business_name}"
3. Select the business category: "{gmb_data.get("category_primary", "")}"
4. Enter the address if prompted: "{address}"
5. Enter the phone number: "{phone}"
6. Fill in any other available fields
7. STOP before clicking any final submit/publish button
8. Report what fields were filled successfully

IMPORTANT: Do NOT click any final submit or publish button. Just fill the form.
"""

                agent = Agent(
                    task=task_description,
                    llm=llm,
                    browser=browser,
                    max_actions_per_step=5,
                )

                result = await agent.run(max_steps=15)
                
                await push_update(sid, "gmb", 88, "Form filling attempted! 📝")
                gmb_status = "form_filled"
                gmb_profile["automation_result"] = str(result)

            except Exception as browser_err:
                print(f"[GMBAgent] Browser automation failed: {browser_err}")
                await push_update(sid, "gmb", 88, "Browser automation skipped, data ready ⚠️")
                gmb_status = "data_ready"
        else:
            await push_update(sid, "gmb", 88, "Browser automation not available, data ready 📋")

        # ══════════════════════════════════════
        # PHASE 4: Complete (90% → 100%)
        # ══════════════════════════════════════
        result_data = {
            **gmb_profile,
            "status": gmb_status,
            "browser_use_available": HAS_BROWSER_USE,
            "instructions": (
                "The form has been pre-filled! Review and submit at business.google.com"
                if gmb_status == "form_filled"
                else "Go to business.google.com/create and fill in the details below. We've prepared all the data for you!"
            ),
        }

        await push_update(
            sid, "gmb", 100,
            f"Google Business profile {'filled' if gmb_status == 'form_filled' else 'ready'}! 🎉",
            status="completed",
            result_data=result_data,
        )

        return {
            "gmb_status": gmb_status,
            "completed_agents": ["gmb"],
        }

    except Exception as e:
        error_msg = f"GMB Agent error: {str(e)}"
        print(f"[GMBAgent] ERROR: {traceback.format_exc()}")
        await push_update(sid, "gmb", 0, error_msg, status="error")

        return {
            "gmb_status": "error",
            "completed_agents": ["gmb"],
        }
