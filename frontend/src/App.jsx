import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import EntityOnboardingForm from './components/EntityOnboardingForm';
import DocumentVault from './components/DocumentVault';
import FinancialMetricsDisplay from './components/FinancialMetricsDisplay';
import CreditScoringDisplay from './components/CreditScoringDisplay';
import UnderwritingDashboard from './components/UnderwritingDashboard';
import ResearchDashboard from './components/ResearchDashboard';
import { ExplainabilityDashboard } from './components/ExplainabilityDashboard';
import ExtractionReviewDashboard from './components/ExtractionReviewDashboard';
import { CAMHistoryDashboard } from './components/CAMHistoryDashboard';
import { entityService } from './services/entityService';
import { documentService } from './services/documentService';

const API_BASE = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';

const tabs = [
  ['documents', 'Document Vault'],
  ['metrics', 'Financial Metrics'],
  ['scoring', 'Credit Scoring'],
  ['underwriting', 'Underwriting'],
  ['research', 'Research'],
  ['explainability', 'Explainability'],
  ['review', 'Extraction Review'],
  ['cam', 'CAM History'],
];

function App() {
  const [mode, setMode] = useState('login');
  const [activeTab, setActiveTab] = useState('documents');
  const [email, setEmail] = useState('analyst@example.com');
  const [password, setPassword] = useState('Password123!');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [entityId, setEntityId] = useState(localStorage.getItem('active_entity_id') || '');
  const [entityName, setEntityName] = useState('');
  const [latestDocumentId, setLatestDocumentId] = useState(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState('');
  const token = localStorage.getItem('access_token');

  const isAuthenticated = Boolean(token);
  const hasEntity = Boolean(entityId);
  const hasDocument = Boolean(latestDocumentId);

  const authClient = useMemo(() => axios.create({ baseURL: API_BASE }), []);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common.Authorization;
    }
  }, [token]);

  const refreshEntityContext = useCallback(async (targetEntityId) => {
    if (!targetEntityId) return;
    setContextLoading(true);
    setContextError('');

    try {
      const [entityResponse, documentResponse] = await Promise.all([
        entityService.getEntity(Number(targetEntityId)),
        documentService.getEntityDocuments(Number(targetEntityId)),
      ]);

      const loadedEntity = entityResponse?.data;
      const docs = documentResponse?.data?.documents || [];

      setEntityName(loadedEntity?.company_name || `Entity ${targetEntityId}`);
      setLatestDocumentId(docs.length > 0 ? docs[0].id : null);
    } catch (error) {
      setContextError(error.response?.data?.detail || 'Failed to load entity context');
    } finally {
      setContextLoading(false);
    }
  }, []);

  const hydrateLatestEntity = useCallback(async () => {
    if (!isAuthenticated || hasEntity) return;

    try {
      setContextLoading(true);
      setContextError('');
      const response = await entityService.getLatestEntity();
      const latestEntity = response?.data;

      if (latestEntity?.id) {
        const resolvedEntityId = String(latestEntity.id);
        setEntityId(resolvedEntityId);
        setEntityName(latestEntity.company_name || `Entity ${resolvedEntityId}`);
        localStorage.setItem('active_entity_id', resolvedEntityId);
      }
    } catch (error) {
      if (error.response?.status !== 404) {
        setContextError(error.response?.data?.detail || 'Failed to load latest entity context');
      }
    } finally {
      setContextLoading(false);
    }
  }, [isAuthenticated, hasEntity]);

  useEffect(() => {
    if (isAuthenticated && hasEntity) {
      refreshEntityContext(entityId);
    }
  }, [isAuthenticated, hasEntity, entityId, refreshEntityContext, activeTab]);

  useEffect(() => {
    hydrateLatestEntity();
  }, [hydrateLatestEntity]);

  const handleAuth = async () => {
    setAuthLoading(true);
    setAuthError('');
    try {
      const endpoint = mode === 'signup' ? '/auth/signup' : '/auth/login';
      const payload = mode === 'signup'
        ? { email, password, role: 'credit_analyst' }
        : { email, password };
      const response = await authClient.post(endpoint, payload);
      localStorage.setItem('access_token', response.data.access_token);
      axios.defaults.headers.common.Authorization = `Bearer ${response.data.access_token}`;
      setAuthLoading(false);
      window.location.reload();
    } catch (error) {
      setAuthError(error.response?.data?.detail || 'Authentication failed');
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('active_entity_id');
    window.location.reload();
  };

  const handleEntityCreated = (entity) => {
    const newEntityId = String(entity.id);
    setEntityId(newEntityId);
    setEntityName(entity.company_name || `Entity ${newEntityId}`);
    localStorage.setItem('active_entity_id', newEntityId);
    setActiveTab('documents');
    refreshEntityContext(newEntityId);
  };

  const handleStartNewOnboarding = () => {
    setEntityId('');
    setEntityName('');
    setLatestDocumentId(null);
    localStorage.removeItem('active_entity_id');
  };

  const handleNavigateToReview = () => {
    setActiveTab('review');
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 text-white px-6 py-12">
        <div className="mx-auto max-w-md rounded-2xl border border-white/10 bg-white/10 p-8 backdrop-blur">
          <h1 className="text-3xl font-bold">Credit Underwriting Workbench</h1>
          <p className="mt-2 text-sm text-slate-300">Sign in first. If the user does not exist yet, switch to sign up once.</p>
          <div className="mt-6 space-y-4">
            <div>
              <label className="mb-1 block text-sm text-slate-300">Email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-4 py-3 outline-none" />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-300">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-4 py-3 outline-none" />
            </div>
            {authError && <div className="rounded-lg border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">{authError}</div>}
            <button onClick={handleAuth} disabled={authLoading} className="w-full rounded-lg bg-blue-500 px-4 py-3 font-semibold text-white hover:bg-blue-400 disabled:bg-slate-600">
              {authLoading ? 'Working...' : mode === 'signup' ? 'Create Account' : 'Sign In'}
            </button>
            <button onClick={() => setMode(mode === 'signup' ? 'login' : 'signup')} className="w-full text-sm text-slate-300 underline underline-offset-4">
              {mode === 'signup' ? 'Use existing account instead' : 'Create a new account instead'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!hasEntity) {
    return (
      <div className="min-h-screen bg-slate-100 text-slate-900">
        <header className="bg-slate-950 text-white">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
            <div>
              <h1 className="text-2xl font-bold">Credit Underwriting Workbench</h1>
              <p className="text-sm text-slate-300">Step 1 of 2: Complete entity onboarding</p>
            </div>
            <button onClick={handleLogout} className="rounded-lg border border-white/20 px-4 py-2 text-sm hover:bg-white/10">Log Out</button>
          </div>
        </header>
        <EntityOnboardingForm onEntityCreated={handleEntityCreated} title="Onboarding" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="bg-slate-950 text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold">Credit Underwriting Workbench</h1>
            <p className="text-sm text-slate-300">Step 2 of 2: Main workspace</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleStartNewOnboarding} className="rounded-lg border border-white/20 px-4 py-2 text-sm hover:bg-white/10">New Onboarding</button>
            <button onClick={handleLogout} className="rounded-lg border border-white/20 px-4 py-2 text-sm hover:bg-white/10">Log Out</button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-6">
        <section className="mb-6 rounded-2xl bg-white p-5 shadow-sm">
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Entity</p>
              <p className="text-base font-semibold text-slate-900">{entityName || `Entity ${entityId}`}</p>
              <p className="text-sm text-slate-600">ID: {entityId}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Latest Document</p>
              <p className="text-base font-semibold text-slate-900">{latestDocumentId ? `Document ${latestDocumentId}` : 'No documents uploaded yet'}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Backend</p>
              <p className="text-base font-semibold text-slate-900">{API_BASE}</p>
              {contextLoading && <p className="text-sm text-blue-600">Refreshing context...</p>}
              {contextError && <p className="text-sm text-red-600">{contextError}</p>}
            </div>
          </div>
        </section>

        <nav className="mb-6 flex flex-wrap gap-2">
          {tabs.map(([key, label]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`rounded-full px-4 py-2 text-sm font-medium ${activeTab === key ? 'bg-slate-950 text-white' : 'bg-white text-slate-700 shadow-sm'}`}
            >
              {label}
            </button>
          ))}
        </nav>

        {activeTab === 'documents' && (
          <DocumentVault
            entityId={Number(entityId)}
            onNavigateToReview={handleNavigateToReview}
          />
        )}
        {activeTab === 'metrics' && (hasDocument ? <FinancialMetricsDisplay documentId={Number(latestDocumentId)} entityId={Number(entityId)} /> : <DependencyNotice text="Upload at least one document in Document Vault before opening Financial Metrics." />)}
        {activeTab === 'scoring' && (hasDocument ? <CreditScoringDisplay documentId={Number(latestDocumentId)} entityId={Number(entityId)} entityName={entityName} /> : <DependencyNotice text="Upload at least one document in Document Vault before opening Credit Scoring." />)}
        {activeTab === 'underwriting' && <UnderwritingDashboard entityId={Number(entityId)} entityName={entityName} />}
        {activeTab === 'research' && <ResearchDashboard entityId={Number(entityId)} entityName={entityName} onClose={() => {}} />}
        {activeTab === 'explainability' && <ExplainabilityDashboard entityId={Number(entityId)} entityName={entityName} onClose={() => {}} />}
        {activeTab === 'review' && <ExtractionReviewDashboard entityId={Number(entityId)} entityName={entityName} />}
        {activeTab === 'cam' && <CAMHistoryDashboard entityId={Number(entityId)} entityName={entityName} />}
      </div>
    </div>
  );
}

function DependencyNotice({ text }) {
  return (
    <div className="rounded-2xl border border-amber-300 bg-amber-50 p-6 text-amber-800">
      <p className="font-medium">Dependency missing</p>
      <p className="mt-1 text-sm">{text}</p>
    </div>
  );
}

export default App;