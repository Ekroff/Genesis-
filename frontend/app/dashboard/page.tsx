"use client";

import { useState, useEffect, useCallback, useRef } from "react";
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
  RefreshCw,
  Share2,
  FileText,
  Clock,
  Trophy,
  MessageCircle,
} from "lucide-react";
import Link from "next/link";
import { useAgentTasks } from "@/lib/supabase";
import { AgentTask, AGENT_CONFIGS, LaunchRequest } from "@/lib/types";

// ═══════════ CONSTANTS ═══════════

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const agentIcons: Record<string, React.ReactNode> = {
  brand: <Sparkles size={20} />,
  website: <Globe size={20} />,
  payment: <CreditCard size={20} />,
  outreach: <Mail size={20} />,
  gmb: <MapPin size={20} />,
  legal: <Scale size={20} />,
};

const agentEmoji: Record<string, string> = {
  brand: "🎨",
  website: "🌐",
  payment: "💳",
  outreach: "📧",
  gmb: "📍",
  legal: "⚖️",
};

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

// ═══════════ CONFETTI CELEBRATION (#1) ═══════════

function ConfettiCelebration() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = ["#FF6B35", "#FFD700", "#3B82F6", "#10B981", "#8B5CF6", "#EC4899", "#06B6D4"];
    const particles: Array<{
      x: number; y: number; r: number;
      vx: number; vy: number; color: string;
      rotation: number; rotSpeed: number;
      shape: "rect" | "circle";
      alpha: number;
    }> = [];

    for (let i = 0; i < 150; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height - canvas.height,
        r: Math.random() * 6 + 3,
        vx: (Math.random() - 0.5) * 4,
        vy: Math.random() * 3 + 2,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rotSpeed: (Math.random() - 0.5) * 10,
        shape: Math.random() > 0.5 ? "rect" : "circle",
        alpha: 1,
      });
    }

    let animId: number;
    let frame = 0;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      frame++;

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.04; // gravity
        p.rotation += p.rotSpeed;
        if (frame > 120) p.alpha -= 0.008;

        ctx.save();
        ctx.globalAlpha = Math.max(0, p.alpha);
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;

        if (p.shape === "rect") {
          ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, p.r, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      });

      if (frame < 300) {
        animId = requestAnimationFrame(animate);
      }
    };

    animate();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1000,
        pointerEvents: "none",
      }}
    />
  );
}

// ═══════════ PROGRESS BAR ═══════════

function ProgressBar({ progress, status }: { progress: number; status: string }) {
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

// ═══════════ TIME DISPLAY HELPER (#3) ═══════════

function formatDuration(startedAt: string | null, completedAt: string | null): string | null {
  if (!startedAt) return null;
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const seconds = Math.round((end - start) / 1000);
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs.toString().padStart(2, "0")}s`;
}

// ═══════════ AGENT CARD (#3 time tracker + #6 retry) ═══════════

function AgentCard({
  task,
  sessionId,
  onRetry,
}: {
  task: AgentTask;
  sessionId: string;
  onRetry: (agentName: string) => void;
}) {
  const config = AGENT_CONFIGS.find((c) => c.name === task.agent_name);
  if (!config) return null;

  const icon = agentIcons[task.agent_name];
  const emoji = agentEmoji[task.agent_name] || "⚡";
  const result = task.result_data;

  // Time tracking (#3)
  const duration = formatDuration(
    (task as any).started_at || (task as any).created_at || null,
    (task as any).completed_at || (task as any).updated_at || null,
  );

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
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
          <StatusBadge status={task.status} />
          {/* Time display (#3) */}
          {duration && task.status !== "pending" && (
            <span
              style={{
                fontSize: "0.7rem",
                color: task.status === "completed" ? "var(--green)" : "var(--text-muted)",
                display: "flex",
                alignItems: "center",
                gap: "3px",
              }}
            >
              <Clock size={10} />
              {duration}
            </span>
          )}
        </div>
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

      {/* Retry Button (#6) */}
      {task.status === "error" && (
        <motion.button
          className="btn btn-ghost"
          onClick={() => onRetry(task.agent_name)}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{
            marginTop: "8px",
            width: "100%",
            fontSize: "0.8rem",
            padding: "8px",
            border: "1px solid var(--red)",
            color: "var(--red)",
          }}
        >
          <RefreshCw size={14} />
          Retry {config.label}
        </motion.button>
      )}

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

// ═══════════ VIDEO PANEL (TruGen AI Avatar) ═══════════

function VideoPanel({
  onLaunch,
  isLaunched,
}: {
  onLaunch: (data: LaunchRequest) => void;
  isLaunched: boolean;
}) {
  const AGENT_ID = "56c7c319-c335-483f-b8b9-d1181580601a";

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.origin !== "https://app.trugen.ai") return;
      try {
        const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
        if (data.type === "tool_call" && data.tool === "launch_business") {
          onLaunch(data.arguments || DEMO_DATA);
        }
      } catch { /* ignore parse errors */ }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, [onLaunch]);

  return (
    <div
      className="glass-card"
      style={{
        height: "500px",
        overflow: "hidden",
        padding: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--border-subtle)",
          fontWeight: 600,
          fontSize: "0.9rem",
        }}
      >
        🎙️ AI Business Advisor
      </div>
      <iframe
        src={`https://app.trugen.ai/embed/${AGENT_ID}?username=User&id=genesis-user&context=Indian%20small%20business%20launch`}
        allow="camera; microphone; fullscreen; display-capture"
        style={{
          width: "100%",
          flex: 1,
          border: "none",
          background: "var(--bg-tertiary)",
        }}
        title="GENESIS AI Avatar"
      />
    </div>
  );
}

// ═══════════ OVERALL PROGRESS HEADER (#4) ═══════════

function OverallProgressHeader({
  tasks,
  allCompleted,
}: {
  tasks: AgentTask[];
  allCompleted: boolean;
}) {
  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const runningCount = tasks.filter((t) => t.status === "running").length;
  const errorCount = tasks.filter((t) => t.status === "error").length;
  const totalProgress = Math.round(
    tasks.reduce((sum, t) => sum + (t.progress || 0), 0) / Math.max(tasks.length, 1)
  );

  // Total time
  const allStartTimes = tasks
    .map((t) => (t as any).started_at || (t as any).created_at)
    .filter(Boolean)
    .map((s: string) => new Date(s).getTime());
  const allEndTimes = tasks
    .filter((t) => t.status === "completed")
    .map((t) => (t as any).completed_at || (t as any).updated_at)
    .filter(Boolean)
    .map((s: string) => new Date(s).getTime());

  const earliest = allStartTimes.length ? Math.min(...allStartTimes) : null;
  const latest = allEndTimes.length ? Math.max(...allEndTimes) : null;
  const totalDuration =
    earliest && (allCompleted ? latest : Date.now())
      ? formatDuration(
          new Date(earliest).toISOString(),
          allCompleted && latest ? new Date(latest).toISOString() : null
        )
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        padding: "16px 20px",
        background: "var(--glass-bg)",
        backdropFilter: "blur(20px)",
        border: "1px solid var(--glass-border)",
        borderRadius: "16px",
        marginBottom: "20px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "10px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {allCompleted ? (
            <Trophy size={20} color="var(--orange)" />
          ) : (
            <Loader2 size={20} color="var(--blue)" style={{ animation: "spin 1.5s linear infinite" }} />
          )}
          <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>
            {allCompleted
              ? "🎉 All agents complete!"
              : `GENESIS is working... ${completedCount}/6 agents complete`}
          </span>
        </div>
        <div style={{ display: "flex", gap: "12px", fontSize: "0.8rem" }}>
          {runningCount > 0 && (
            <span style={{ color: "var(--blue)" }}>⚡ {runningCount} running</span>
          )}
          {errorCount > 0 && (
            <span style={{ color: "var(--red)" }}>❌ {errorCount} failed</span>
          )}
          {totalDuration && (
            <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
              <Clock size={12} /> Total: {totalDuration}
            </span>
          )}
        </div>
      </div>

      {/* Overall progress bar */}
      <div
        style={{
          height: "6px",
          borderRadius: "3px",
          background: "var(--bg-tertiary)",
          overflow: "hidden",
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${totalProgress}%` }}
          transition={{ duration: 0.5 }}
          style={{
            height: "100%",
            borderRadius: "3px",
            background: allCompleted
              ? "linear-gradient(90deg, #10B981, #06B6D4)"
              : "linear-gradient(90deg, #FF6B35, #FFD700)",
          }}
        />
      </div>

      {/* Agent mini status strip */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          marginTop: "10px",
          flexWrap: "wrap",
        }}
      >
        {tasks.map((t) => (
          <span
            key={t.agent_name}
            style={{
              fontSize: "0.75rem",
              padding: "3px 8px",
              borderRadius: "6px",
              background:
                t.status === "completed"
                  ? "rgba(16,185,129,0.12)"
                  : t.status === "running"
                  ? "rgba(59,130,246,0.12)"
                  : t.status === "error"
                  ? "rgba(239,68,68,0.12)"
                  : "var(--bg-tertiary)",
              color:
                t.status === "completed"
                  ? "var(--green)"
                  : t.status === "running"
                  ? "var(--blue)"
                  : t.status === "error"
                  ? "var(--red)"
                  : "var(--text-muted)",
            }}
          >
            {agentEmoji[t.agent_name]} {AGENT_CONFIGS.find((c) => c.name === t.agent_name)?.label || t.agent_name}{" "}
            {t.status === "completed" ? "✅" : t.status === "running" ? "⚡" : t.status === "error" ? "❌" : "⏳"}
          </span>
        ))}
      </div>
    </motion.div>
  );
}

// ═══════════ COMPLETION PANEL (#1 celebration, #2 WhatsApp share, #5 biz card, #7 email) ═══════════

function CompletionPanel({
  tasks,
  sessionId,
  businessName,
}: {
  tasks: AgentTask[];
  sessionId: string;
  businessName: string;
}) {
  const [showConfetti, setShowConfetti] = useState(true);
  const [emailSent, setEmailSent] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowConfetti(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  // Collect data for sharing
  const brandResult = tasks.find((t) => t.agent_name === "brand")?.result_data || {};
  const websiteResult = tasks.find((t) => t.agent_name === "website")?.result_data || {};
  const paymentResult = tasks.find((t) => t.agent_name === "payment")?.result_data || {};

  const websiteUrl = websiteResult.website_url || "";
  const tagline = brandResult.tagline_hindi || brandResult.tagline_english || "";

  // WhatsApp share (#2)
  const shareOnWhatsApp = () => {
    const msg = `
🚀 Mera business ab online hai!

🌐 Website: ${websiteUrl}
💳 Payment: UPI QR ready!
📍 Google Maps: Coming soon!

${businessName} - ${tagline}

Powered by GENESIS AI ⚡
    `.trim();

    window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, "_blank");
  };

  // Business card download (#5)
  const downloadBusinessCard = () => {
    window.open(`${BACKEND_URL}/api/business-card/${sessionId}`, "_blank");
  };

  // Summary email (#7)
  const sendSummary = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/send-summary/${sessionId}`, { method: "POST" });
      setEmailSent(true);
    } catch (e) {
      console.error("Failed to send summary:", e);
    }
  };

  return (
    <>
      {showConfetti && <ConfettiCelebration />}

      <motion.div
        className="glass-card"
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        style={{ marginTop: "24px", textAlign: "center", padding: "40px 24px" }}
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
          style={{ fontSize: "4rem", marginBottom: "16px" }}
        >
          🎉
        </motion.div>

        <h2>
          Your Business is <span className="gradient-text-accent">Live!</span>
        </h2>
        <p className="text-muted" style={{ marginTop: "8px", fontSize: "1rem" }}>
          All 6 agents have completed. {businessName} is ready to go!
        </p>

        {/* Action buttons */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "12px",
            justifyContent: "center",
            marginTop: "28px",
          }}
        >
          {/* WhatsApp Share (#2) */}
          <motion.button
            className="btn btn-primary"
            onClick={shareOnWhatsApp}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            style={{
              background: "linear-gradient(135deg, #25D366, #128C7E)",
              border: "none",
              padding: "12px 24px",
              fontSize: "0.9rem",
            }}
          >
            <MessageCircle size={18} />
            Share on WhatsApp
          </motion.button>

          {/* Business Card PDF (#5) */}
          <motion.button
            className="btn btn-ghost"
            onClick={downloadBusinessCard}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            style={{ padding: "12px 24px", fontSize: "0.9rem" }}
          >
            <FileText size={18} />
            Download Business Card
          </motion.button>

          {/* Website link */}
          {websiteUrl && (
            <motion.a
              href={websiteUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              whileHover={{ scale: 1.03 }}
              style={{ padding: "12px 24px", fontSize: "0.9rem", textDecoration: "none" }}
            >
              <Globe size={18} />
              Visit Website
            </motion.a>
          )}

          {/* Summary Email (#7) */}
          <motion.button
            className="btn btn-ghost"
            onClick={sendSummary}
            disabled={emailSent}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            style={{ padding: "12px 24px", fontSize: "0.9rem" }}
          >
            <Mail size={18} />
            {emailSent ? "Email Sent! ✅" : "Email Me Everything"}
          </motion.button>
        </div>

        <p style={{ marginTop: "20px", fontSize: "0.85rem", color: "var(--orange)" }}>
          &quot;सपने देखना बंद करो, बिज़नेस शुरू करो&quot; 🚀
        </p>
      </motion.div>
    </>
  );
}

// ═══════════ DASHBOARD PAGE ═══════════

export default function DashboardPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [launchData, setLaunchData] = useState<LaunchRequest | null>(null);
  const { tasks, isLoading, allCompleted, overallProgress } = useAgentTasks(sessionId);

  const handleLaunch = async (data: LaunchRequest) => {
    setIsLaunching(true);
    setLaunchData(data);
    try {
      const res = await fetch(`${BACKEND_URL}/api/launch`, {
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

  // Agent retry handler (#6)
  const handleRetry = async (agentName: string) => {
    if (!sessionId) return;
    try {
      await fetch(`${BACKEND_URL}/api/retry/${sessionId}/${agentName}`, {
        method: "POST",
      });
    } catch (err) {
      console.error("Retry error:", err);
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

        {sessionId && !allCompleted && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span
              style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}
            >
              ⚡ {overallProgress}% complete
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
          <VideoPanel onLaunch={handleLaunch} isLaunched={!!sessionId} />
          <ChatPanel onLaunch={handleLaunch} isLaunched={!!sessionId} />
        </div>

        {/* Overall Progress Header (#4) */}
        {sessionId && tasks.length > 0 && (
          <OverallProgressHeader tasks={tasks} allCompleted={allCompleted} />
        )}

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
                  <AgentCard
                    task={task}
                    sessionId={sessionId}
                    onRetry={handleRetry}
                  />
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

        {/* All Complete — Celebration + Actions (#1, #2, #5, #7) */}
        {allCompleted && sessionId && (
          <CompletionPanel
            tasks={tasks}
            sessionId={sessionId}
            businessName={launchData?.business_name || "Your Business"}
          />
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
