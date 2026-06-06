"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Copy, Share2, QrCode } from "lucide-react";
import { useParams } from "next/navigation";

// ═══════════ TYPES ═══════════

interface InvoiceItem {
  item: string;
  quantity: number;
  unit_price: number;
  total: number;
}

interface InvoiceData {
  items: InvoiceItem[];
  subtotal: number;
  business_name: string;
  upi_qr_url: string;
}

interface MenuItem {
  item: string;
  price: number;
}

interface SessionData {
  business_name: string;
  menu: MenuItem[];
  phone: string;
  upi_id: string;
  // Brand data (if completed)
  logo_url?: string;
  primary_color?: string;
}

// ═══════════ SMART INVOICE PAGE ═══════════

export default function SmartInvoicePage() {
  const params = useParams();
  const businessId = params.businessId as string;

  const [session, setSession] = useState<SessionData | null>(null);
  const [orderText, setOrderText] = useState("");
  const [invoice, setInvoice] = useState<InvoiceData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(true);

  // Fetch session data
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const res = await fetch(`${backendUrl}/api/session/${businessId}`);
        const data = await res.json();
        if (!data.error) {
          setSession(data);
        } else {
          // Fallback demo data
          setSession({
            business_name: "Ramesh Tiffin Service",
            menu: [
              { item: "Dal Chawal", price: 80 },
              { item: "Rajma Chawal", price: 90 },
              { item: "Paneer Thali", price: 120 },
              { item: "Special Thali", price: 150 },
            ],
            phone: "9876543210",
            upi_id: "9876543210@paytm",
          });
        }
      } catch {
        // Fallback
        setSession({
          business_name: "Ramesh Tiffin Service",
          menu: [
            { item: "Dal Chawal", price: 80 },
            { item: "Rajma Chawal", price: 90 },
            { item: "Paneer Thali", price: 120 },
            { item: "Special Thali", price: 150 },
          ],
          phone: "9876543210",
          upi_id: "9876543210@paytm",
        });
      }
      setIsLoadingSession(false);
    };

    fetchSession();
  }, [businessId]);

  // Parse order
  const handleParseOrder = async () => {
    if (!orderText.trim()) return;
    setIsLoading(true);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/invoice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_text: orderText,
          session_id: businessId,
        }),
      });
      const data = await res.json();
      setInvoice(data);
    } catch (err) {
      console.error("Invoice parse error:", err);
    }

    setIsLoading(false);
  };

  // Copy invoice link
  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    alert("Invoice link copied! 📋");
  };

  // Share on WhatsApp
  const handleShareWhatsApp = () => {
    if (!invoice || !session) return;
    const message = encodeURIComponent(
      `🧾 Invoice from ${session.business_name}\n\n` +
        invoice.items
          .map((item) => `${item.quantity}x ${item.item} — ₹${item.total}`)
          .join("\n") +
        `\n\n💰 Total: ₹${invoice.subtotal}\n\n` +
        `Pay here: ${window.location.href}`
    );
    window.open(`https://wa.me/?text=${message}`, "_blank");
  };

  if (isLoadingSession) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-primary)",
        }}
      >
        <Loader2
          size={32}
          style={{ animation: "spin 1s linear infinite", color: "var(--blue)" }}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        padding: "24px",
      }}
    >
      <div style={{ maxWidth: "500px", margin: "0 auto" }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: "center", marginBottom: "32px" }}
        >
          <div style={{ fontSize: "2rem", marginBottom: "8px" }}>🧾</div>
          <h2 style={{ fontSize: "1.5rem" }}>
            <span className="gradient-text">{session?.business_name}</span>
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Smart Invoice — Type your order below
          </p>
        </motion.div>

        {/* Menu Display */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{ marginBottom: "16px" }}
        >
          <h4 style={{ fontSize: "0.9rem", marginBottom: "12px", color: "var(--text-secondary)" }}>
            📋 Menu
          </h4>
          <div style={{ display: "grid", gap: "8px" }}>
            {session?.menu.map((item, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "0.9rem",
                  padding: "6px 0",
                  borderBottom: "1px solid var(--border-subtle)",
                }}
              >
                <span>{item.item}</span>
                <span style={{ fontWeight: 600, color: "var(--green)" }}>
                  ₹{item.price}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Order Input */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{ marginBottom: "16px" }}
        >
          <h4 style={{ fontSize: "0.9rem", marginBottom: "12px", color: "var(--text-secondary)" }}>
            🗣️ Type your order
          </h4>
          <div style={{ display: "flex", gap: "8px" }}>
            <input
              className="chat-input"
              placeholder='e.g., "2 paneer thali 1 dal chawal"'
              value={orderText}
              onChange={(e) => setOrderText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleParseOrder()}
              disabled={isLoading}
              style={{ flex: 1 }}
            />
            <button
              className="btn btn-primary"
              onClick={handleParseOrder}
              disabled={isLoading || !orderText.trim()}
              style={{ padding: "10px 16px" }}
            >
              {isLoading ? (
                <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "8px" }}>
            Hindi bhi likh sakte hain: &quot;2 पनीर थाली 1 दाल चावल&quot;
          </p>
        </motion.div>

        {/* Invoice Result */}
        <AnimatePresence>
          {invoice && (
            <motion.div
              className="glass-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              style={{
                border: "1px solid rgba(16,185,129,0.2)",
                marginBottom: "16px",
              }}
            >
              <h4
                style={{
                  fontSize: "0.9rem",
                  marginBottom: "12px",
                  color: "var(--green)",
                }}
              >
                ✅ Invoice
              </h4>

              {/* Line items */}
              {invoice.items.map((item, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.9rem",
                    padding: "8px 0",
                    borderBottom: "1px solid var(--border-subtle)",
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 500 }}>{item.item}</span>
                    <span style={{ color: "var(--text-muted)", marginLeft: "8px" }}>
                      ×{item.quantity}
                    </span>
                  </div>
                  <span style={{ fontWeight: 600 }}>₹{item.total}</span>
                </div>
              ))}

              {/* Total */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: "12px",
                  paddingTop: "12px",
                  borderTop: "2px solid var(--border-subtle)",
                  fontSize: "1.1rem",
                  fontWeight: 700,
                }}
              >
                <span>Total</span>
                <span className="gradient-text-accent" style={{ fontSize: "1.3rem" }}>
                  ₹{invoice.subtotal}
                </span>
              </div>

              {/* QR Code */}
              <div style={{ textAlign: "center", marginTop: "20px" }}>
                <p
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                    marginBottom: "12px",
                  }}
                >
                  Scan to pay exact amount ↓
                </p>
                <img
                  src={invoice.upi_qr_url}
                  alt="UPI QR Code"
                  style={{
                    width: "180px",
                    height: "180px",
                    borderRadius: "12px",
                    margin: "0 auto",
                    background: "white",
                    padding: "8px",
                  }}
                />
              </div>

              {/* Actions */}
              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  marginTop: "16px",
                }}
              >
                <button
                  className="btn btn-ghost"
                  onClick={handleCopyLink}
                  style={{ flex: 1, fontSize: "0.8rem" }}
                >
                  <Copy size={14} />
                  Copy Link
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleShareWhatsApp}
                  style={{ flex: 1, fontSize: "0.8rem" }}
                >
                  <Share2 size={14} />
                  WhatsApp
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
