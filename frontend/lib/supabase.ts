/**
 * GENESIS — Supabase client + Realtime hooks
 * 
 * Provides:
 * 1. Supabase client singleton
 * 2. useAgentTasks() hook — subscribes to Realtime updates for agent_tasks
 * 3. Helper functions for sessions and storage
 */

import { createClient, RealtimePostgresChangesPayload } from '@supabase/supabase-js';
import { useEffect, useState, useCallback } from 'react';
import { AgentTask, Session } from './types';

// ═══════════ Client ═══════════

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://localhost:54321',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'
);

// ═══════════ Realtime Hook ═══════════

/**
 * Subscribe to real-time agent task updates for a session.
 * 
 * This is the CORE of the live dashboard. When any agent writes
 * to Supabase via push_update(), this hook receives the change
 * in <200ms and updates the React state.
 */
export function useAgentTasks(sessionId: string | null) {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initial fetch
  useEffect(() => {
    if (!sessionId) {
      setIsLoading(false);
      return;
    }

    const fetchTasks = async () => {
      const { data, error } = await supabase
        .from('agent_tasks')
        .select('*')
        .eq('session_id', sessionId)
        .order('created_at', { ascending: true });

      if (data && !error) {
        setTasks(data as AgentTask[]);
      }
      setIsLoading(false);
    };

    fetchTasks();
  }, [sessionId]);

  // Realtime subscription
  useEffect(() => {
    if (!sessionId) return;

    const channel = supabase
      .channel(`agent-updates-${sessionId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'agent_tasks',
          filter: `session_id=eq.${sessionId}`,
        },
        (payload: RealtimePostgresChangesPayload<AgentTask>) => {
          const updated = payload.new as AgentTask;
          setTasks(prev =>
            prev.map(t => (t.id === updated.id ? { ...t, ...updated } : t))
          );
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'agent_tasks',
          filter: `session_id=eq.${sessionId}`,
        },
        (payload: RealtimePostgresChangesPayload<AgentTask>) => {
          const newTask = payload.new as AgentTask;
          setTasks(prev => {
            // Don't add duplicates
            if (prev.find(t => t.id === newTask.id)) return prev;
            return [...prev, newTask];
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [sessionId]);

  // Derived state
  const allCompleted = tasks.length > 0 && tasks.every(t => t.status === 'completed');
  const hasError = tasks.some(t => t.status === 'error');
  const overallProgress =
    tasks.length > 0
      ? Math.round(tasks.reduce((sum, t) => sum + t.progress, 0) / tasks.length)
      : 0;

  return { tasks, isLoading, allCompleted, hasError, overallProgress };
}

// ═══════════ Session Helpers ═══════════

export async function getSession(sessionId: string): Promise<Session | null> {
  const { data, error } = await supabase
    .from('sessions')
    .select('*')
    .eq('id', sessionId)
    .single();

  if (error || !data) return null;
  return data as Session;
}

// ═══════════ Storage Helpers ═══════════

export async function uploadFile(
  bucket: string,
  path: string,
  file: File
): Promise<string | null> {
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, { upsert: true });

  if (error) {
    console.error('Upload error:', error);
    return null;
  }

  const { data: urlData } = supabase.storage
    .from(bucket)
    .getPublicUrl(path);

  return urlData.publicUrl;
}
