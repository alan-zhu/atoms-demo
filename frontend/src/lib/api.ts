import type { AppEvent, Project } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`

const TOKEN_KEY = 'atoms-demo-token'

export function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setToken(t: string | null) {
  if (t) window.localStorage.setItem(TOKEN_KEY, t)
  else window.localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(init?.headers as Record<string, string> ?? {}) }
  if (token && !headers['Authorization']) headers['Authorization'] = `Bearer ${token}`
  const response = await fetch(`${API_BASE}${path}`, { headers, ...init })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: '请求失败，请稍后重试' }))
    throw new Error(body.detail ?? '请求失败，请稍后重试')
  }
  return response.json() as Promise<T>
}

export interface User {
  id: string
  email: string
  name: string | null
  created_at: string
}

export interface AuthResult {
  token: string
  user: User
}

export const api = {
  // Auth
  register: (email: string, password: string, name?: string) =>
    request<AuthResult>('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password, name }) }),
  login: (email: string, password: string) =>
    request<AuthResult>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/api/auth/me'),

  projects: () => request<Project[]>('/api/projects'),
  project: (id: string) => request<Project>(`/api/projects/${id}`),
  create: (prompt: string, llmMode = false) =>
    request<Project>('/api/projects', { method: 'POST', body: JSON.stringify({ prompt, llm_mode: llmMode }) }),
  health: () => request<{ status: string; llm_enabled: boolean; provider?: string; model?: string; api_base?: string }>('/api/health'),
  iterate: (id: string, prompt: string) =>
    request<Project>(`/api/projects/${id}/iterate`, { method: 'POST', body: JSON.stringify({ prompt }) }),
  restore: (id: string, version: number) =>
    request<Project>(`/api/projects/${id}/restore`, { method: 'POST', body: JSON.stringify({ version_number: version }) }),
  publish: (id: string) =>
    request<Project>(`/api/projects/${id}/publish`, { method: 'POST', body: JSON.stringify({}) }),
  shared: (token: string) => request<Project>(`/api/share/${token}`),
  event: (id: string, event: AppEvent) =>
    request<Project>(`/api/projects/${id}/events`, { method: 'POST', body: JSON.stringify(event) }),
  sharedEvent: (token: string, event: AppEvent) => request<Project>(`/api/share/${token}/events`, { method: 'POST', body: JSON.stringify(event) }),
  projectHtml: (id: string) => request<{ html: string }>(`/api/projects/${id}/html`)
}
