import { FormEvent, ReactNode, useEffect, useState } from 'react'
import { api, clearSession, saveSession, storedUser, User } from './api'

type Dashboard = { available_units: number; expiring_soon: number; pending_requests: number; donors: number; inventory_by_group: Record<string, number> }
type Product = { id: string; unit_code: string; component: string; blood_group: string; volume_ml: number; expires_on: string; status: string }
type RequestItem = { id: string; component: string; blood_group: string; units_requested: number; priority: string; status: string; needed_by?: string }
type Donor = { id: string; donor_code: string; first_name: string; last_name: string; blood_group: string; phone: string; is_deferred: boolean }

const nav = ['Dashboard', 'Inventory', 'Requests', 'Donors'] as const
type Page = typeof nav[number]

function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(''); try { const data = await api<{ access_token: string; user: User }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }); saveSession(data.access_token, data.user); onLogin(data.user) } catch (err) { setError(err instanceof Error ? err.message : 'Unable to sign in') } finally { setBusy(false) } }
  return <main className="login-shell"><section className="login-copy"><span className="mark">♥</span><h1>VitalFlow</h1><p>Blood donation department management, made reliable.</p><small>Authorized staff access only. Every action is recorded.</small></section><form className="login-card" onSubmit={submit}><h2>Sign in</h2><label>Email<input type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required /></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required minLength={12}/></label>{error && <p className="error">{error}</p>}<button disabled={busy}>{busy ? 'Signing in…' : 'Sign in securely'}</button></form></main>
}

function Metric({ value, label, alert }: { value: number; label: string; alert?: boolean }) { return <article className={`metric ${alert ? 'alert' : ''}`}><strong>{value}</strong><span>{label}</span></article> }

function App() {
  const [user, setUser] = useState<User | null>(storedUser()); const [page, setPage] = useState<Page>('Dashboard'); const [dashboard, setDashboard] = useState<Dashboard | null>(null); const [inventory, setInventory] = useState<Product[]>([]); const [requests, setRequests] = useState<RequestItem[]>([]); const [donors, setDonors] = useState<Donor[]>([]); const [error, setError] = useState('')
  const staff = user?.role === 'staff' || user?.role === 'admin'
  async function load() { if (!staff) return; setError(''); try { const [d, i, r, ds] = await Promise.all([api<Dashboard>('/dashboard'), api<Product[]>('/inventory'), api<RequestItem[]>('/requests'), api<Donor[]>('/donors')]); setDashboard(d); setInventory(i); setRequests(r); setDonors(ds) } catch (e) { setError(e instanceof Error ? e.message : 'Could not load data') } }
  useEffect(() => { load() }, [user])
  if (!user) return <Login onLogin={setUser}/>
  if (!staff) return <main className="donor-home"><h1>Welcome, donor</h1><p>Your donor portal is connected. Donation history and appointment management can be accessed by the care team.</p><button onClick={() => { clearSession(); setUser(null) }}>Sign out</button></main>
  return <div className="app"><aside><div className="brand"><span>♥</span> VitalFlow</div><nav>{nav.map(item => <button key={item} onClick={() => setPage(item)} className={page === item ? 'active' : ''}>{item}</button>)}</nav><div className="account"><b>{user.email}</b><small>{user.role}</small><button onClick={() => { clearSession(); setUser(null) }}>Sign out</button></div></aside><main className="content"><header><div><p className="eyebrow">Blood donation department</p><h1>{page}</h1></div><button className="secondary" onClick={load}>Refresh</button></header>{error && <p className="error">{error}</p>}{page === 'Dashboard' && <DashboardPage data={dashboard}/>} {page === 'Inventory' && <InventoryPage items={inventory}/>} {page === 'Requests' && <RequestsPage items={requests}/>} {page === 'Donors' && <DonorsPage items={donors}/>}</main></div>
}

function DashboardPage({ data }: { data: Dashboard | null }) { if (!data) return <p>Loading live department data…</p>; return <><section className="metrics"><Metric value={data.available_units} label="Available units"/><Metric value={data.expiring_soon} label="Expiring in 7 days" alert/><Metric value={data.pending_requests} label="Open requests"/><Metric value={data.donors} label="Registered donors"/></section><section className="panel"><h2>Available inventory by blood group</h2><div className="blood-grid">{['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(g => <div key={g}><b>{g}</b><span>{data.inventory_by_group[g] || 0} units</span></div>)}</div></section></> }
function InventoryPage({ items }: { items: Product[] }) { return <section className="panel"><h2>Traceable blood units</h2><Table headers={['Unit', 'Component', 'Group', 'Volume', 'Expiry', 'Status']} rows={items.map(p => [p.unit_code, p.component.replace('_', ' '), p.blood_group, `${p.volume_ml} ml`, p.expires_on, <span className={`badge ${p.status}`}>{p.status}</span>])}/></section> }
function RequestsPage({ items }: { items: RequestItem[] }) { return <section className="panel"><h2>Recipient requests</h2><Table headers={['Component', 'Group', 'Units', 'Priority', 'Status']} rows={items.map(r => [r.component.replace('_', ' '), r.blood_group, String(r.units_requested), <span className={`priority ${r.priority}`}>{r.priority}</span>, <span className="badge">{r.status}</span>])}/></section> }
function DonorsPage({ items }: { items: Donor[] }) { return <section className="panel"><h2>Donor directory</h2><Table headers={['Code', 'Donor', 'Group', 'Telephone', 'Eligibility']} rows={items.map(d => [d.donor_code, `${d.first_name} ${d.last_name}`, d.blood_group, d.phone, d.is_deferred ? 'Deferred' : 'Eligible'])}/></section> }
function Table({ headers, rows }: { headers: string[]; rows: ReactNode[][] }) { return <div className="table-wrap"><table><thead><tr>{headers.map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{rows.length ? rows.map((row, i) => <tr key={i}>{row.map((cell, x) => <td key={x}>{cell}</td>)}</tr>) : <tr><td colSpan={headers.length}>No records found.</td></tr>}</tbody></table></div> }
export default App
