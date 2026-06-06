/**
 * GENESIS — Shared TypeScript types
 * 
 * These types mirror the Supabase schema and backend models.
 * Used across all frontend components for type safety.
 */

// ═══════════ Agent Types ═══════════

export type AgentName = 'brand' | 'website' | 'payment' | 'outreach' | 'gmb' | 'legal';
export type AgentStatus = 'pending' | 'running' | 'completed' | 'error';

export interface AgentTask {
  id: string;
  session_id: string;
  agent_name: AgentName;
  status: AgentStatus;
  progress: number;           // 0-100
  current_step: string;       // "Generating logo..." (shown on card)
  result_data: Record<string, any> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// ═══════════ Session Types ═══════════

export interface MenuItem {
  item: string;
  price: number;
}

export interface Session {
  id: string;
  user_id: string;
  business_name: string;
  business_type: string;
  menu: MenuItem[];
  address: string;
  phone: string;
  language: string;
  upi_id: string;
  shop_photo_url: string | null;
  existing_logo_url: string | null;
  status: 'active' | 'completed' | 'error';
  created_at: string;
}

// ═══════════ API Types ═══════════

export interface LaunchRequest {
  business_name: string;
  business_type: string;
  menu: MenuItem[];
  address: string;
  phone: string;
  language: string;
  upi_id: string;
  shop_photo_url?: string;
  existing_logo_url?: string;
  user_id?: string;
}

export interface LaunchResponse {
  session_id: string;
  status: string;
}

export interface InvoiceItem {
  item: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface InvoiceResponse {
  items: InvoiceItem[];
  subtotal: number;
  business_name: string;
  upi_qr_url: string;
}

// ═══════════ Agent Config (for UI) ═══════════

export interface AgentConfig {
  name: AgentName;
  label: string;
  icon: string;
  description: string;
  color: string;
}

export const AGENT_CONFIGS: AgentConfig[] = [
  {
    name: 'brand',
    label: 'Brand Identity',
    icon: '🎨',
    description: 'Logo, colors, tagline, and brand kit',
    color: '#FF6B35',
  },
  {
    name: 'website',
    label: 'Live Website',
    icon: '🌐',
    description: 'Deployed website with your branding',
    color: '#3B82F6',
  },
  {
    name: 'payment',
    label: 'Smart Payments',
    icon: '💳',
    description: 'UPI QR code and Smart Invoice tool',
    color: '#10B981',
  },
  {
    name: 'outreach',
    label: 'Customer Outreach',
    icon: '📧',
    description: 'WhatsApp + email outreach to nearby businesses',
    color: '#8B5CF6',
  },
  {
    name: 'gmb',
    label: 'Google Business',
    icon: '📍',
    description: 'Google Business Profile auto-fill',
    color: '#F59E0B',
  },
  {
    name: 'legal',
    label: 'Legal & Compliance',
    icon: '⚖️',
    description: 'GST, FSSAI, Udyam — forms pre-filled',
    color: '#06B6D4',
  },
];
