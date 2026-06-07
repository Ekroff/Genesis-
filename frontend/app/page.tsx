"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import {
  Sparkles,
  Zap,
  Globe,
  CreditCard,
  Mail,
  MapPin,
  Scale,
  ArrowRight,
  Rocket,
  ChevronDown,
  LogIn,
} from "lucide-react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useRef, useState, useEffect } from "react";
import { useUser, UserButton } from "@clerk/nextjs";

const Hero3D = dynamic(() => import("./components/Hero3D"), {
  ssr: false,
  loading: () => null,
});

// ═══════════ ANIMATION VARIANTS ═══════════

const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.6,
      ease: "easeOut",
    },
  }),
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5, ease: "easeOut" },
  },
};

// ═══════════ FEATURES DATA ═══════════

const features = [
  {
    icon: <Sparkles size={28} />,
    title: "Brand Identity",
    titleHi: "ब्रांड पहचान",
    description:
      "AI generates your logo, brand colors, Hindi tagline, and complete social media kit in seconds.",
    color: "#FF6B35",
  },
  {
    icon: <Globe size={28} />,
    title: "Live Website",
    titleHi: "लाइव वेबसाइट",
    description:
      "A beautiful, mobile-first website deployed to the internet with your menu, photos, and WhatsApp ordering.",
    color: "#3B82F6",
  },
  {
    icon: <CreditCard size={28} />,
    title: "Smart Payments",
    titleHi: "स्मार्ट पेमेंट",
    description:
      "UPI QR code + AI-powered Smart Invoice that converts voice orders to exact-amount payment links.",
    color: "#10B981",
  },
  {
    icon: <Mail size={28} />,
    title: "Customer Outreach",
    titleHi: "कस्टमर आउटरीच",
    description:
      "Find nearby offices and businesses, send personalized WhatsApp messages and emails automatically.",
    color: "#8B5CF6",
  },
  {
    icon: <MapPin size={28} />,
    title: "Google Business",
    titleHi: "गूगल बिज़नेस",
    description:
      "AI fills your Google Business Profile so customers can find you on Google Maps and Search.",
    color: "#F59E0B",
  },
  {
    icon: <Scale size={28} />,
    title: "Legal & Compliance",
    titleHi: "कानूनी सहायता",
    description:
      "Pre-filled FSSAI, GST, and Udyam registration forms with step-by-step Hindi guides.",
    color: "#06B6D4",
  },
];

const stats = [
  { value: "6", label: "AI Agents" },
  { value: "30", label: "Minutes" },
  { value: "₹0", label: "Cost" },
  { value: "100%", label: "Automated" },
];

// ═══════════ HOW IT WORKS ═══════════

const steps = [
  {
    number: "01",
    title: "Talk to Your AI Assistant",
    titleHi: "AI असिस्टेंट से बात करें",
    description:
      "Speak naturally in Hindi. Tell us about your business — name, what you sell, your location. Upload a menu photo if you have one.",
    icon: "🎙️",
  },
  {
    number: "02",
    title: "6 Agents Work Simultaneously",
    titleHi: "6 एजेंट एक साथ काम करते हैं",
    description:
      "Watch in real-time as AI creates your brand, builds your website, sets up payments, finds customers, and more.",
    icon: "⚡",
  },
  {
    number: "03",
    title: "Your Business Is Live",
    titleHi: "आपका बिज़नेस लाइव है",
    description:
      "Get your website URL, QR code, customer contacts, and legal docs — everything ready to go. Start earning today.",
    icon: "🚀",
  },
];

// ═══════════ PAGE COMPONENT ═══════════

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95]);

  const { isSignedIn } = useUser();

  return (
    <main>
      {/* ═══════════ NAVBAR ═══════════ */}
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          padding: "16px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "rgba(10, 10, 15, 0.8)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
        }}
      >
        <Link href="/" style={{ textDecoration: "none" }}>
          <span
            style={{
              fontSize: "1.3rem",
              fontWeight: 800,
              background: "linear-gradient(135deg, #FF6B35, #FFD700)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              letterSpacing: "-0.02em",
            }}
          >
            GENESIS
          </span>
        </Link>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {!isSignedIn ? (
            <>
              <Link href="/sign-in">
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: "0.85rem", padding: "8px 20px" }}
                >
                  <LogIn size={16} />
                  Sign In
                </button>
              </Link>
              <Link href="/sign-up">
                <button
                  className="btn btn-primary"
                  style={{ fontSize: "0.85rem", padding: "8px 20px" }}
                >
                  Get Started
                </button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/dashboard">
                <button
                  className="btn btn-primary"
                  style={{ fontSize: "0.85rem", padding: "8px 20px" }}
                >
                  <Rocket size={16} />
                  Dashboard
                </button>
              </Link>
              <UserButton />
            </>
          )}
        </div>
      </nav>

      {/* ═══════════ HERO ═══════════ */}
      <motion.section
        ref={heroRef}
        className="hero"
        style={{ opacity: heroOpacity, scale: heroScale, position: "relative" }}
      >
        {/* Three.js 3D Background */}
        <Hero3D />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "6px 16px",
            borderRadius: "9999px",
            background: "rgba(59,130,246,0.1)",
            border: "1px solid rgba(59,130,246,0.2)",
            fontSize: "0.85rem",
            color: "#3B82F6",
            marginBottom: "24px",
          }}
        >
          <Sparkles size={14} />
          Powered by 6 AI Agents
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
        >
          Launch Your Business
          <br />
          <span className="gradient-text">in 30 Minutes</span>
        </motion.h1>

        <motion.p
          className="hero-subtitle"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          अपना बिज़नेस 30 मिनट में लॉन्च करें — Logo, Website, UPI QR, Google
          Listing, सब कुछ AI करेगा।
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          style={{
            display: "flex",
            gap: "16px",
            marginTop: "32px",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          <Link href="/dashboard">
            <button className="btn btn-primary btn-lg">
              <Rocket size={20} />
              Launch My Business
              <ArrowRight size={18} />
            </button>
          </Link>
          <a href="#how-it-works">
            <button className="btn btn-ghost btn-lg">
              See How It Works
              <ChevronDown size={18} />
            </button>
          </a>
        </motion.div>

        {/* Stats */}
        <motion.div
          className="hero-stats"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {stats.map((stat, i) => (
            <motion.div key={stat.label} className="hero-stat" variants={fadeInUp} custom={i + 8}>
              <div className="hero-stat-value">{stat.value}</div>
              <div className="hero-stat-label">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          style={{
            position: "absolute",
            bottom: "40px",
            animation: "float 2s ease-in-out infinite",
          }}
        >
          <ChevronDown size={24} color="var(--text-muted)" />
        </motion.div>
      </motion.section>

      {/* ═══════════ HOW IT WORKS ═══════════ */}
      <section id="how-it-works" className="section" style={{ background: "var(--bg-secondary)" }}>
        <div className="container text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            How It <span className="gradient-text">Works</span>
          </motion.h2>
          <motion.p
            className="text-muted mt-md"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            style={{ fontSize: "1.1rem", maxWidth: "500px", margin: "16px auto 0" }}
          >
            Three simple steps. That&apos;s it.
          </motion.p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "24px",
              marginTop: "64px",
              maxWidth: "1000px",
              marginLeft: "auto",
              marginRight: "auto",
            }}
          >
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                className="glass-card"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.5 }}
                style={{ textAlign: "left", position: "relative" }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: "16px",
                    right: "16px",
                    fontSize: "3rem",
                    fontWeight: 800,
                    opacity: 0.05,
                    fontFamily: "var(--font-display)",
                  }}
                >
                  {step.number}
                </div>
                <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>{step.icon}</div>
                <h3 style={{ marginBottom: "4px" }}>{step.title}</h3>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--blue)",
                    marginBottom: "12px",
                  }}
                >
                  {step.titleHi}
                </p>
                <p className="text-muted" style={{ fontSize: "0.9rem", lineHeight: "1.7" }}>
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════ 6 AGENTS ═══════════ */}
      <section className="section">
        <div className="container text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            6 AI Agents, <span className="gradient-text-accent">One Mission</span>
          </motion.h2>
          <motion.p
            className="text-muted mt-md"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            style={{ fontSize: "1.1rem", maxWidth: "550px", margin: "16px auto 0" }}
          >
            Each agent is a specialist. They work in parallel to build your entire
            business infrastructure.
          </motion.p>

          <div className="features-grid" style={{ marginTop: "48px" }}>
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                className="feature-card"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.01 }}
              >
                <div
                  className="feature-icon"
                  style={{
                    color: feature.color,
                    display: "inline-flex",
                    padding: "12px",
                    borderRadius: "12px",
                    background: `${feature.color}15`,
                  }}
                >
                  {feature.icon}
                </div>
                <h4 className="feature-title" style={{ marginTop: "12px" }}>
                  {feature.title}
                </h4>
                <p
                  style={{
                    fontSize: "0.8rem",
                    color: feature.color,
                    marginBottom: "8px",
                  }}
                >
                  {feature.titleHi}
                </p>
                <p className="feature-description">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════ CTA ═══════════ */}
      <section
        className="section"
        style={{
          background: "var(--bg-secondary)",
          textAlign: "center",
          padding: "96px 24px",
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="container"
        >
          <div
            style={{
              maxWidth: "700px",
              margin: "0 auto",
              padding: "48px",
              borderRadius: "24px",
              background: "var(--glass-bg)",
              backdropFilter: "blur(20px)",
              border: "1px solid var(--glass-border)",
            }}
          >
            <h2>
              Ready to <span className="gradient-text-accent">Launch</span>?
            </h2>
            <p
              className="text-muted"
              style={{
                marginTop: "16px",
                fontSize: "1.1rem",
                lineHeight: "1.7",
              }}
            >
              Join thousands of Indian entrepreneurs who launched their business
              with GENESIS. No coding, no designer, no consultant — just you and
              your dream.
            </p>
            <p
              style={{
                marginTop: "12px",
                fontSize: "1rem",
                color: "var(--orange)",
              }}
            >
              &quot;सपने देखना बंद करो, बिज़नेस शुरू करो&quot;
            </p>
            <Link href="/dashboard">
              <button
                className="btn btn-accent btn-lg"
                style={{ marginTop: "32px" }}
              >
                <Rocket size={20} />
                Launch My Business — Free 🚀
              </button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ═══════════ FOOTER ═══════════ */}
      <footer
        style={{
          padding: "32px",
          textAlign: "center",
          borderTop: "1px solid var(--border-subtle)",
          color: "var(--text-muted)",
          fontSize: "0.85rem",
        }}
      >
        <p>
          Built with ❤️ for Indian MSMEs •{" "}
          <span className="gradient-text" style={{ fontSize: "0.85rem" }}>
            GENESIS
          </span>{" "}
          © 2025
        </p>
      </footer>
    </main>
  );
}
