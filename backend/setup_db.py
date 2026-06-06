"""
GENESIS — Supabase Database Setup Script

Run this once to create the required tables.
Usage: python setup_db.py
"""

import httpx
import json

SUPABASE_URL = "https://fngptsucwjfxvsstynqn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZuZ3B0c3Vjd2pmeHZzc3R5bnFuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDUzOTIwNCwiZXhwIjoyMDk2MTE1MjA0fQ.cq5fPtJXKFyLMrcDk4TH1TrIa7vxs22_rQy6WTaTWmE"

SQL = """
-- Drop existing tables if any (clean slate)
DROP TABLE IF EXISTS agent_tasks CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;

-- Sessions table
CREATE TABLE sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'anonymous',
  business_name TEXT NOT NULL,
  business_type TEXT NOT NULL DEFAULT '',
  menu JSONB DEFAULT '[]',
  address TEXT DEFAULT '',
  phone TEXT DEFAULT '',
  language TEXT DEFAULT 'hi',
  upi_id TEXT DEFAULT '',
  shop_photo_url TEXT,
  existing_logo_url TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'error')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent tasks table (Realtime enabled)
CREATE TABLE agent_tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  agent_name TEXT NOT NULL CHECK (agent_name IN ('brand', 'website', 'payment', 'outreach', 'gmb', 'legal')),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'error')),
  progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
  current_step TEXT DEFAULT 'Waiting to start...',
  result_data JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast session lookups
CREATE INDEX idx_agent_tasks_session ON agent_tasks(session_id);

-- Enable RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;

-- Allow all operations (hackathon mode - tighten for production)
CREATE POLICY "Allow all on sessions" ON sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on agent_tasks" ON agent_tasks FOR ALL USING (true) WITH CHECK (true);

-- Enable Realtime on agent_tasks
ALTER PUBLICATION supabase_realtime ADD TABLE agent_tasks;
"""

def setup():
    print("Setting up GENESIS database...")
    print(f"Supabase URL: {SUPABASE_URL}")

    # Use the Supabase SQL endpoint (via PostgREST rpc)
    # We'll use the pg_net extension or direct SQL execution
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    # Execute SQL via Supabase's SQL query endpoint
    response = httpx.post(
        f"{SUPABASE_URL}/rest/v1/rpc/",
        headers=headers,
        json={"query": SQL},
        timeout=30,
    )

    if response.status_code in (200, 201, 204):
        print("✅ Tables created successfully!")
    else:
        print(f"⚠️  RPC method not available (status {response.status_code})")
        print("This is expected — Supabase doesn't expose raw SQL via REST.")
        print("")
        print("=" * 60)
        print("MANUAL STEP REQUIRED:")
        print("=" * 60)
        print("")
        print("1. Go to: https://supabase.com/dashboard/project/fngptsucwjfxvsstynqn/sql/new")
        print("2. Paste the SQL below and click 'Run'")
        print("3. Then go to Database → Tables → agent_tasks → Edit → Enable Realtime")
        print("")
        print("-" * 60)
        print(SQL)
        print("-" * 60)

    # Verify connection by trying to read from a table
    print("\nTesting connection...")
    test_response = httpx.get(
        f"{SUPABASE_URL}/rest/v1/sessions?select=id&limit=1",
        headers=headers,
        timeout=10,
    )
    
    if test_response.status_code == 200:
        print(f"✅ Connection successful! Sessions table accessible.")
    elif test_response.status_code == 404:
        print("⚠️  Sessions table doesn't exist yet. Run the SQL above first.")
    else:
        print(f"Response: {test_response.status_code} - {test_response.text[:200]}")

if __name__ == "__main__":
    setup()
