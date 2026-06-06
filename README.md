<p align="center">
  <img src="https://img.shields.io/badge/GENESIS-AI%20Business%20Launcher-00d4aa?style=for-the-badge&labelColor=0a0a0a" alt="Genesis Badge" />
</p>

<h1 align="center">🚀 GENESIS</h1>
<h3 align="center">Launch Your Entire Business in One Video Call</h3>

<p align="center">
  <em>Describe your business to an AI avatar on video. Watch 6 AI agents simultaneously build your brand, website, payments, find customers, and generate compliance docs — in under 6 minutes.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-15-black?logo=next.js" />
  <img src="https://img.shields.io/badge/Express-5-black?logo=express" />
  <img src="https://img.shields.io/badge/Supabase-Realtime-3ecf8e?logo=supabase" />
  <img src="https://img.shields.io/badge/Gemini-2.5-4285F4?logo=google" />
  <img src="https://img.shields.io/badge/TruGen-AI%20Video-ff6b6b" />
</p>

---

## 🔴 The Problem

India has **63.4 million** micro, small, and medium enterprises (MSMEs). The vast majority of them are invisible online.

| Reality | Number |
|---------|--------|
| Total MSMEs in India | 63.4 million |
| MSMEs with a website | ~3.2 million (**5%**) |
| MSMEs with online payments | ~8 million (**12%**) |
| MSMEs with any branding | ~6 million (**10%**) |
| Cost to get a website built | ₹15,000–50,000 |
| Cost for basic branding | ₹5,000–20,000 |
| Cost for a CA consultation | ₹5,000–15,000 |

**95% of Indian small businesses have zero digital presence.** A tiffin delivery auntie, a chai stall owner, a home baker, a local tailor — they know their craft, but they don't know how to get online. The tools that exist are either too expensive, too complex, or too fragmented.

Getting online today requires hiring **5 different people**: a designer, a developer, a payment gateway person, a marketing person, and a CA. That costs ₹50,000+ and takes weeks.

**Nobody has solved this for the people who need it most.**

---

## 🟢 The Solution: GENESIS

**One sentence:** *"Describe your business on a video call. Watch it launch."*

GENESIS is a real-time **video AI agent** that launches a small business's entire online presence through a single conversational video call.

A person with zero technical knowledge video-calls an AI avatar, describes what they do in their own language, and **watches live** as 6 AI agents simultaneously:

1. 🎨 **Build their brand** — logo, product photos, color palette
2. 🌐 **Deploy their website** — a live, production URL with their menu/services
3. 💳 **Set up payments** — a working Razorpay payment link
4. 📧 **Find their first customers** — outreach emails to nearby businesses
5. 📄 **Generate compliance docs** — GST, FSSAI, government schemes PDF
6. 📍 **Draft their Maps listing** — Google Business Profile ready to submit

**Everything is real. Everything works after the call ends.** Judges can click the live URL, test the payment link, and download the PDF.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Video Call)                      │
│              Speaks to TruGen AI Avatar                   │
└─────────────────┬───────────────────────────────────────┘
                  │ Tool Call (business data)
                  ▼
┌─────────────────────────────────────────────────────────┐
│              EXPRESS BACKEND (Render)                     │
│                                                          │
│   POST /api/launch                                       │
│     └── orchestrateAgents(session_id, business_data)     │
│           │                                              │
│           ├── 🎨 Brand Agent ──────► Imagen 3 API        │
│           ├── 🌐 Website Agent ────► Vercel Deploy API   │
│           ├── 💳 Payment Agent ────► Razorpay API        │
│           ├── 📧 Outreach Agent ───► Resend + Places API │
│           ├── 📄 Docs Agent ───────► Gemini + jsPDF      │
│           └── 📍 Maps Agent ───────► Gemini + Places API │
│                                                          │
│   All 6 agents run via Promise.allSettled()              │
│   Each agent writes progress to Supabase in real-time    │
└─────────────────┬───────────────────────────────────────┘
                  │ Realtime (WebSocket)
                  ▼
┌─────────────────────────────────────────────────────────┐
│             NEXT.JS DASHBOARD (Vercel)                   │
│                                                          │
│  ┌──────────┐  ┌──────────────────────────────────┐     │
│  │  Video   │  │  Agent Orchestration Panel       │     │
│  │  Call    │  │  ┌──────┐ ┌──────┐ ┌──────┐     │     │
│  │  (live)  │  │  │Brand │ │Web   │ │Pay   │     │     │
│  │          │  │  │ 75%  │ │ 40%  │ │ 100% │     │     │
│  │          │  │  └──────┘ └──────┘ └──────┘     │     │
│  │          │  │  ┌──────┐ ┌──────┐ ┌──────┐     │     │
│  │          │  │  │Email │ │Docs  │ │Maps  │     │     │
│  │          │  │  │ 50%  │ │ 25%  │ │ 70%  │     │     │
│  │          │  │  └──────┘ └──────┘ └──────┘     │     │
│  └──────────┘  └──────────────────────────────────┘     │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │  🎉 Results Panel                            │       │
│  │  🌐 Visit Website → https://genesis-xxx.vercel.app  ││
│  │  💳 Payment Link → https://rzp.io/xxx               ││
│  │  📄 Download PDF → business-kit.pdf                  ││
│  └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│               SUPABASE (Database + Realtime)             │
│                                                          │
│  sessions ──► agent_tasks ──► generated_sites            │
│                  │                                       │
│   Realtime subscriptions push status updates to          │
│   the dashboard as each agent progresses                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, Tailwind, Framer Motion | Dashboard with real-time agent visualization |
| **Auth** | Clerk | Google OAuth sign-in |
| **Backend** | Express.js on Render | Persistent server for agent orchestration |
| **Database** | Supabase (Postgres + Realtime) | Session storage + WebSocket progress updates |
| **Video AI** | TruGen AI | Conversational video avatar with tool calling |
| **AI Generation** | Gemini 2.5 Flash + Imagen 3 | Text/JSON generation + image generation |
| **Website Deploy** | Vercel Deploy API | Programmatic site deployment to production |
| **Payments** | Razorpay | Payment link creation |
| **Email** | Resend | Transactional outreach emails |
| **Location** | Google Places API | Nearby business discovery |
| **Documents** | jsPDF | PDF business kit generation |

---

## 🤖 The 6 AI Agents

### 🎨 Agent 1: Brand Maker
Generates a complete brand identity — logo (via Imagen 3), product photos, color palette, tagline, and brand voice. This feeds into the Website Agent.

### 🌐 Agent 2: Website Builder
Takes the brand output and business data to generate a fully responsive, production-ready HTML website. Deploys it to Vercel via their API. **Output: a live URL anyone can visit.**

### 💳 Agent 3: Payment Setup
Creates a Razorpay payment link with the business name, average item price, and contact info. **Output: a working payment link that accepts real money.**

### 📧 Agent 4: Customer Finder
Uses Gemini to write a professional outreach email, then sends it via Resend. Uses Google Places to find nearby businesses for targeting. **Output: actual emails sent.**

### 📄 Agent 5: Business Guide
Generates a comprehensive starter kit covering GST registration, FSSAI licensing, government schemes (PMEGP, Mudra, Stand-Up India), and tax tips. Exports as a downloadable PDF. **Output: a real PDF document.**

### 📍 Agent 6: Maps Helper
Generates a Google Business Profile draft with optimized description, categories, hours, and SEO keywords. **Output: ready-to-submit listing content.**

---

## ⚡ How It Works (User Flow)

```
1. User opens GENESIS → Signs in with Google
2. Clicks "Start Video Call" → TruGen AI avatar appears
3. AI asks: "What's your business name? What do you sell? Where are you located?"
4. User describes their business naturally (in any language)
5. AI confirms the details and triggers the launch
6. Dashboard splits: Video on left, Agent Panel on right
7. All 6 agent cards animate from "Pending" → "Running" → "Complete"
8. Progress bars update in real-time via Supabase WebSockets
9. Results appear as agents finish: live URLs, payment links, PDF downloads
10. Total time: ~3-6 minutes from conversation to fully launched business
```

---

## 💰 Why This Matters

| Traditional Way | GENESIS |
|----------------|---------|
| 5 people (designer, dev, marketer, payment, CA) | 1 video call |
| ₹50,000+ cost | Free / ₹99 |
| 2-4 weeks | 6 minutes |
| Requires technical knowledge | Zero tech skills needed |
| Fragmented tools | Everything in one place |

**TAM:** 63.4M MSMEs × ₹99/launch = **₹6,276 Cr** ($750M) addressable market in India alone.

---

## 🏃 Running Locally

```bash
# Clone
git clone https://github.com/chinmaykhatri/Genesis.git
cd Genesis

# Dashboard
cd dashboard
npm install
cp .env.example .env.local  # Add your API keys
npm run dev

# Server (in another terminal)
cd server
npm install
cp .env.example .env  # Add your API keys
npm run dev
```

---

<p align="center">
  <strong>Built for hackathon. Designed for production. Made for 63 million businesses.</strong>
</p>
