"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Globe,
  CreditCard,
  Mail,
  MapPin,
  Scale,
  Rocket,
  Upload,
  Send,
  ArrowLeft,
  ExternalLink,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Image as ImageIcon,
} from "lucide-react";
import Link from "next/link";
import { useAgentTasks } from "@/lib/supabase";
import { AgentTask, AGENT_CONFIGS, LaunchRequest } from "@/lib/types";

// ═══════════ AGENT ICON MAP ═══════════

const agentIcons: Record<string, React.ReactNode> = {
  brand: <Sparkles size={20} />,
  website: <Globe size={20} />,
  payment: <CreditCard size={20} />,
  outreach: <Mail size={20} />,
  gmb: <MapPin size={20} />,
  legal: <Scale size={20} />,
};

// ═══════════ DEMO DATA ═══════════

const DEMO_DATA: LaunchRequest = {
  business_name: "Ramesh Tiffin Service",
  business_type: "tiffin_delivery",
  menu: [
    { item: "Dal Chawal", price: 80 },
    { item: "Rajma Chawal", price: 90 },
    { item: "Paneer Thali", price: 120 },
    { item: "Special Thali", price: 150 },
  ],
  address: "B-12, Laxmi Nagar, Delhi",
  phone: "9876543210",
  language: "hi",
  upi_id: "9876543210@paytm",
};

// ═══════════ PROGRESS BAR COMPONENT ═══════════

function ProgressBar({
  progress,
  status,
}: {
  progress: number;
  status: string;
}) {
  return (
    <div className={`progress-bar ${status === "running" ? "running" : ""}`}>
      <div
        className={`progress-bar-fill ${status === "completed" ? "completed" : ""}`}
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

// ═══════════ STATUS BADGE ═══════════

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { className: string; label: string }> = {
    pending: { className: "badge badge-pending", label: "Waiting" },
    running: { className: "badge badge-running", label: "Running" },
    completed: { className: "badge badge-completed", label: "Done" },
    error: { className: "badge badge-error", label: "Error" },
  };

  const { className, label } = config[status] || config.pending;

  return (
    <span className={className}>
      {status === "completed" && <CheckCircle2 size={12} />}
      {status === "error" && <AlertCircle size={12} />}
      {status === "running" && <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />}
      {label}
    </span>
  );
}

// ═══════════ AGENT CARD COMPONENT ═══════════

function AgentCard({ task }: { task: AgentTask }) {
  const config = AGENT_CONFIGS.find((c) => c.name === task.agent_name);
  if (!config) return null;

  const icon = agentIcons[task.agent_name];
  const result = task.result_data;

  return (
    <motion.div
      className={`agent-card ${task.status}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      layout
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              padding: "8px",
              borderRadius: "10px",
              background: `${config.color}15`,
              color: config.color,
              display: "flex",
            }}
          >
            {icon}
          </div>
          <div>
            <h4 style={{ fontSize: "0.95rem", fontWeight: 600 }}>{config.label}</h4>
            <p
              style={{
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                marginTop: "2px",
              }}
            >
              {config.description}
            </p>
          </div>
        </div>
        <StatusBadge status={task.status} />
      </div>

      {/* Progress */}
      <ProgressBar progress={task.progress} status={task.status} />

      {/* Current Step */}
      <p
        style={{
          fontSize: "0.8rem",
          color: "var(--text-secondary)",
          marginTop: "8px",
          minHeight: "20px",
        }}
      >
        {task.current_step || "Waiting to start..."}
      </p>

      {/* Results (shown when completed) */}
      <AnimatePresence>
        {task.status === "completed" && result && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              marginTop: "12px",
              paddingTop: "12px",
              borderTop: "1px solid var(--border-subtle)",
            }}
          >
            {/* Brand results */}
            {task.agent_name === "brand" && result.logo_url && (
              <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                <img
                  src={result.logo_url}
                  alt="Logo"
                  style={{
                    width: "48px",
                    height: "48px",
                    borderRadius: "10px",
                    objectFit: "cover",
                    border: "1px solid var(--border-subtle)",
                  }}
                />
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: "0.8rem", fontWeight: 600 }}>
                    {result.tagline_hindi}
                  </p>
                  <div style={{ display: "flex", gap: "6px", marginTop: "6px" }}>
                    <div
                      style={{
                        width: "18px",
                        height: "18px",
                        borderRadius: "4px",
                        background: result.primary_color,
                        border: "1px solid var(--border-subtle)",
                      }}
                    />
                    <div
                      style={{
                        width: "18px",
                        height: "18px",
                        borderRadius: "4px",
                        background: result.secondary_color,
                        border: "1px solid var(--border-subtle)",
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Website results */}
            {task.agent_name === "website" && result.website_url && (
              <a
                href={result.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-ghost"
                style={{ fontSize: "0.8rem", padding: "6px 14px", width: "100%" }}
              >
                <ExternalLink size={14} />
                Visit Website
              </a>
            )}

            {/* Payment results */}
            {task.agent_name === "payment" && result.upi_qr_url && (
              <div style={{ textAlign: "center" }}>
                <img
                  src={result.upi_qr_url}
                  alt="UPI QR"
                  style={{
                    width: "100px",
                    height: "100px",
                    borderRadius: "8px",
                    margin: "0 auto",
                  }}
                />
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "6px" }}>
                  UPI: {result.upi_id}
                </p>
                {result.invoice_page_url && (
                  <Link
                    href={result.invoice_page_url}
                    className="btn btn-ghost"
                    style={{
                      fontSize: "0.8rem",
                      padding: "6px 14px",
                      marginTop: "8px",
                      width: "100%",
                    }}
                  >
                    🧾 Open Smart Invoice
                  </Link>
                )}
              </div>
            )}

            {/* Outreach results */}
            {task.agent_name === "outreach" && (
              <p style={{ fontSize: "0.8rem", color: "var(--green)" }}>
                ✅ {result.message || "Outreach plan ready"}
              </p>
            )}

            {/* Legal results */}
            {task.agent_name === "legal" && result.legal_checklist && (
              <div style={{ fontSize: "0.8rem" }}>
                {(result.legal_checklist as Array<{ item: string; status: string }>).map(
                  (item: { item: string; status: string }, i: number) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        gap: "6px",
                        alignItems: "center",
                        marginBottom: "4px",
                      }}
                    >
                      <span>
                        {item.status === "required" ? "🔴" : item.status === "recommended" ? "🟡" : "🟢"}
                      </span>
                      <span>{item.item}</span>
                    </div>
                  )
                )}
              </div>
            )}

            {/* GMB results */}
            {task.agent_name === "gmb" && (
              <p style={{ fontSize: "0.8rem", color: "var(--green)" }}>
                ✅ {result.message || "GMB data prepared"}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ═══════════ CHAT PANEL ═══════════

interface ChatMessage {
  id: string;
  role: "bot" | "user";
  text: string;
  imageUrl?: string;
}

function ChatPanel({
  onLaunch,
  isLaunched,
}: {
  onLaunch: (data: LaunchRequest) => void;
  isLaunched: boolean;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "bot",
      text: "नमस्ते! 🙏 मैं GENESIS हूं। आपका बिज़नेस लॉन्च करने में मदद करूंगा। अपने बिज़नेस के बारे में बताइए!",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", text: input },
    ]);
    setInput("");

    // Simulate bot response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          text: "बहुत बढ़िया! मैं आपकी details समझ रहा हूं। 'Launch My Business' बटन दबाकर शुरू करें! 🚀",
        },
      ]);
    }, 1000);
  };

  return (
    <div className="chat-panel" style={{ height: "500px" }}>
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--border-subtle)",
          fontWeight: 600,
          fontSize: "0.9rem",
        }}
      >
        💬 Chat with GENESIS
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-message ${msg.role}`}>
            {msg.text}
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <button
          className="btn btn-ghost"
          style={{ padding: "10px", borderRadius: "10px" }}
          title="Upload photo"
        >
          <ImageIcon size={18} />
        </button>
        <input
          className="chat-input"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={isLaunched}
        />
        <button
          className="btn btn-ghost"
          style={{ padding: "10px", borderRadius: "10px" }}
          onClick={handleSend}
          disabled={isLaunched}
        >
          <Send size={18} />
        </button>
      </div>

      {!isLaunched && (
        <div style={{ padding: "12px" }}>
          <button
            className="btn btn-accent"
            style={{ width: "100%" }}
            onClick={() => onLaunch(DEMO_DATA)}
          >
            <Rocket size={18} />
            Launch My Business 🚀
          </button>
        </div>
      )}
    </div>
  );
}

// ═══════════ VIDEO PANEL (TruGen Placeholder) ═══════════

function VideoPanel() {
  return (
    <div className="video-panel">
      <div className="video-panel-placeholder">
        <div style={{ fontSize: "3rem", marginBottom: "12px" }}>🎙️</div>
        <h3 style={{ fontSize: "1.1rem", marginBottom: "8px" }}>
          AI Avatar
        </h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: "250px" }}>
          TruGen AI avatar will appear here.
          <br />
          Speak naturally in Hindi to set up your business.
        </p>
      </div>
    </div>
  );
}

// ═══════════ DASHBOARD PAGE ═══════════

export default function DashboardPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const { tasks, isLoading, allCompleted, overallProgress } = useAgentTasks(sessionId);

  const handleLaunch = async (data: LaunchRequest) => {
    setIsLaunching(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      setSessionId(result.session_id);
    } catch (err) {
      console.error("Launch error:", err);
      alert("Backend not connected. Make sure the FastAPI server is running on port 8000.");
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      {/* Header */}
      <header className="dashboard-header" style={{ padding: "16px 24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link
            href="/"
            style={{
              color: "var(--text-muted)",
              display: "flex",
              alignItems: "center",
            }}
          >
            <ArrowLeft size={18} />
          </Link>
          <h3>
            <span className="gradient-text">GENESIS</span> Dashboard
          </h3>
        </div>

        {sessionId && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span
              style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}
            >
              {allCompleted ? "✅ All agents complete!" : `⚡ ${overallProgress}% complete`}
            </span>
          </div>
        )}
      </header>

      <div style={{ padding: "0 24px 24px", maxWidth: "1600px", margin: "0 auto" }}>
        {/* Top section: Video + Chat */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "16px",
            marginBottom: "24px",
          }}
        >
          <VideoPanel />
          <ChatPanel onLaunch={handleLaunch} isLaunched={!!sessionId} />
        </div>

        {/* Agent Cards Grid */}
        {sessionId && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h3 style={{ marginBottom: "16px" }}>
              ⚡ Agent Status
            </h3>
            <div className="agent-grid">
              {tasks.map((task, i) => (
                <motion.div
                  key={task.id || task.agent_name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                >
                  <AgentCard task={task} />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Not launched yet — show intro */}
        {!sessionId && !isLaunching && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              textAlign: "center",
              padding: "64px 24px",
              color: "var(--text-muted)",
            }}
          >
            <div style={{ fontSize: "3rem", marginBottom: "16px" }}>🚀</div>
            <h3 style={{ color: "var(--text-primary)", marginBottom: "8px" }}>
              Ready to Launch
            </h3>
            <p style={{ maxWidth: "400px", margin: "0 auto" }}>
              Talk to the AI avatar or use the chat to tell us about your
              business. Then hit &quot;Launch My Business&quot; to start all 6 agents.
            </p>
          </motion.div>
        )}

        {/* Launching state */}
        {isLaunching && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ textAlign: "center", padding: "64px 24px" }}
          >
            <Loader2
              size={48}
              style={{ animation: "spin 1s linear infinite", color: "var(--blue)" }}
            />
            <p style={{ marginTop: "16px", color: "var(--text-secondary)" }}>
              Launching your business...
            </p>
          </motion.div>
        )}

        {/* All Complete — Results */}
        {allCompleted && (
          <motion.div
            className="results-panel"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ marginTop: "24px" }}
          >
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "3rem", marginBottom: "12px" }}>🎉</div>
              <h2>
                Your Business is{" "}
                <span className="gradient-text-accent">Live!</span>
              </h2>
              <p
                className="text-muted"
                style={{ marginTop: "8px", fontSize: "1rem" }}
              >
                All 6 agents have completed. Your business is ready to go!
              </p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Keyframe for spin animation */}
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
