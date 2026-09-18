export type User = { id: string; email: string; role: 'donor' | 'staff' | 'admin'; is_active: boolean }
const API = '/api'
export function token() { return localStorage.getItem('blood-token') }
export function saveSession(accessToken: string, user: User) { localStorage.setItem('blood-token', accessToken); localStorage.setItem('blood-user', JSON.stringify(user)) }
export function clearSession() { localStorage.removeItem('blood-token'); localStorage.removeItem('blood-user') }
export function storedUser(): User | null { try { return JSON.parse(localStorage.getItem('blood-user') || 'null') } catch { return null } }
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...init.headers } })
  if (response.status === 401) { clearSession(); window.location.reload() }
  const data = await response.json().catch(() => ({ detail: 'Network error' }))
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed')
  return data as T
}
