import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useAuth } from './AutoContext';
import { api, allItems, realtimeUrl } from '../services/api';
import type { BankDecisionInput, ClientNotification, CompanyProfile, CreateApplicationInput, CreditApplication, CreditProduct, Recommendation, RecommendationInput, NextAction, StressSummary } from '../types/credit';

type Ranked = { stress: StressSummary; product: CreditProduct; offer: { amount: number; termMonths: number; monthlyPayment: number; coverage: number; eligible: boolean; reviewRequired: boolean; interestAmount: number }; selectedEvaluation: { coveragePasses: boolean; actions: NextAction[]; requiredCoverage: number; reasons: { code: string; message: string }[] }; highlights: string[]; evaluation: { reasons: { code: string; message: string }[] }; group: string; rankingReason: string };
interface CreditContextValue {
  applications: CreditApplication[]; notifications: ClientNotification[]; products: CreditProduct[];
  getCompany: (id?: string) => CompanyProfile | undefined;
  getProduct: (id: string) => CreditProduct | undefined;
  recommend: (input: RecommendationInput) => Promise<Recommendation[]>;
  createApplication: (input: CreateApplicationInput) => Promise<CreditApplication>;
  decideApplication: (id: string, decision: BankDecisionInput) => Promise<boolean>;
  respondToInfoRequest: (id: string) => Promise<boolean>;
  acceptOffer: (id: string, accepted: boolean) => Promise<boolean>;
  signApplication: (id: string) => Promise<boolean>;
  disburseApplication: (id: string) => Promise<boolean>;
  markNotificationRead: (id: string) => Promise<boolean>;
  markAllNotificationsRead: (companyId: string) => Promise<void>;
  resetDemo: () => void;
}
const CreditContext = createContext<CreditContextValue | undefined>(undefined);
export function CreditProvider({ children }: { children: ReactNode }) {
  const { currentUser } = useAuth();
  const [applications, setApplications] = useState<CreditApplication[]>([]);
  const [notifications, setNotifications] = useState<ClientNotification[]>([]);
  const [companies, setCompanies] = useState<CompanyProfile[]>([]);
  const [products, setProducts] = useState<CreditProduct[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const refreshSequence = useRef(0);
  const mutating = useRef(false);
  const generation = useRef(0);
  const refresh = useCallback(async (signal?: AbortSignal) => {
    if (!currentUser) return;
    const request = ++refreshSequence.current;
    const version = generation.current;
    try {
      const bank = currentUser.role === 'bank';
      const rows = await allItems<{ id: string }>(bank ? '/bank/applications' : '/applications', signal);
      const details: CreditApplication[] = [];
      const profiles: CompanyProfile[] = [];
      // Bounded batches avoid an unbounded burst when a queue contains many applications.
      for (let start = 0; start < rows.length; start += 8) {
        await Promise.all(rows.slice(start, start + 8).map(async row => {
          if (bank) {
            const detail = await api<{ application: CreditApplication; company: CompanyProfile }>(`/bank/applications/${encodeURIComponent(row.id)}`, undefined, signal);
            details.push(detail.application); profiles.push(detail.company);
          } else details.push(await api<CreditApplication>(`/applications/${encodeURIComponent(row.id)}`, undefined, signal));
        }));
      }
      const catalogue = await api<CreditProduct[]>('/credit-products', undefined, signal);
      if (!bank) profiles.push(await api<CompanyProfile>('/companies/me', undefined, signal));
      const notices = bank ? [] : await allItems<ClientNotification>('/notifications', signal);
      if (!signal?.aborted && version === generation.current && request === refreshSequence.current) {
        setApplications(details.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt) || a.id.localeCompare(b.id)));
        setCompanies(profiles); setProducts(catalogue); setNotifications(notices); setError(''); setReady(true);
      }
    } catch (e) { if (!signal?.aborted && request === refreshSequence.current) setError(e instanceof Error ? e.message : 'Не удалось загрузить данные'); }
  }, [currentUser]);
  useEffect(() => {
    if (!currentUser) return;
    const controller = new AbortController();
    // Initial loading synchronizes the provider with the authenticated API.
    // oxlint-disable-next-line react/set-state-in-effect
    void refresh(controller.signal);
    const socket = new WebSocket(realtimeUrl());
    socket.onmessage = () => { void refresh(controller.signal); };
    // Polling recovers missed events and websocket disconnects.
    const timer = window.setInterval(() => { if (!document.hidden) void refresh(controller.signal); }, 15000);
    return () => { controller.abort(); socket.close(); window.clearInterval(timer); };
  }, [currentUser, refresh]);
  const action = async (path: string, body: unknown = {}): Promise<boolean> => {
    if (mutating.current) return false;
    mutating.current = true; setBusy(true); generation.current++;
    try {
      const result = await api<CreditApplication>(path, body);
      if (result?.id && result.status) setApplications(old => [result, ...old.filter(x => x.id !== result.id)]);
      setError(''); await refresh(); return true;
    } catch (e) { setError(e instanceof Error ? e.message : 'Не удалось выполнить действие'); return false; }
    finally { mutating.current = false; setBusy(false); }
  };
  const recommend = useCallback(async (input: RecommendationInput): Promise<Recommendation[]> => {
    const response = await api<{ groups: Record<string, Ranked[]> }>('/recommendations', input);
    return ['requested', 'other_terms', 'reduced_amount', 'requires_action', 'unavailable'].flatMap(group =>
      response.groups[group].map(item => ({ product: item.product, ...item.offer, group,
        coveragePasses: item.selectedEvaluation.coveragePasses, stress: item.stress, actions: item.selectedEvaluation.actions, highlights: item.highlights, requiredCoverage: item.selectedEvaluation.requiredCoverage,
        reason: item.selectedEvaluation.reasons.map(reason => reason.message).join(' '),
        rankingReason: item.rankingReason, warning: item.offer.eligible ? undefined : item.selectedEvaluation.reasons.map(r => r.message).join(' '),
      })));
  }, []);
  if (!currentUser) return <>{children}</>;
  if (!ready) return <div className="page-shell" role="status">{error || 'Загружаем данные…'}{error && <button onClick={() => void refresh()}>Повторить</button>}</div>;
  return <CreditContext.Provider value={{ applications, notifications, products,
    getCompany: id => companies.find(c => c.id === id), getProduct: id => products.find(p => p.id === id), recommend,
    createApplication: async ({ companyId: _companyId, preference: _preference, ...input }) => {
      const result = await api<CreditApplication>('/applications', input);
      generation.current++;
      setApplications(old => [result, ...old.filter(x => x.id !== result.id)]);
      return result;
    },
    decideApplication: (id, decision) => action(`/bank/applications/${encodeURIComponent(id)}/decision`, decision),
    respondToInfoRequest: id => action(`/applications/${encodeURIComponent(id)}/additional-info`, { comment: 'Клиент подтвердил ранее предоставленные сведения.' }),
    acceptOffer: (id, accepted) => action(`/applications/${encodeURIComponent(id)}/accept`, { accepted }),
    signApplication: id => action(`/applications/${encodeURIComponent(id)}/sign`),
    disburseApplication: id => action(`/applications/${encodeURIComponent(id)}/disburse`),
    markNotificationRead: id => action(`/notifications/${encodeURIComponent(id)}/read`),
    markAllNotificationsRead: async companyId => {
      for (const n of notifications.filter(n => !n.read && n.companyId === companyId)) {
        if (!await action(`/notifications/${encodeURIComponent(n.id)}/read`)) break;
      }
    },
    resetDemo: () => { void refresh(); },
  }}>{error && <p className="page-shell" role="alert">{error}</p>}
    <fieldset disabled={busy} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>{children}</fieldset>
  </CreditContext.Provider>;
}
// oxlint-disable-next-line react/only-export-components
export function useCredit(): CreditContextValue {
  const value = useContext(CreditContext);
  if (!value) throw new Error('CreditProvider is missing');
  return value;
}
