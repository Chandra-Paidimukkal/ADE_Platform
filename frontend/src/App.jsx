import { useState, useEffect, useCallback, useRef } from "react";

// ─── API Client ──────────────────────────────────────────────────────────────

const API_BASE = "http://localhost:8000/api/v1";

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

// ─── Icons ───────────────────────────────────────────────────────────────────

const Icon = ({ name, size = 18 }) => {
  const icons = {
    upload: "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12",
    file: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6",
    schema: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    extract: "M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9a2 2 0 00-2-2h-2M9 21H5a2 2 0 01-2-2V9a2 2 0 012-2h2",
    check: "M20 6L9 17l-5-5",
    x: "M18 6L6 18M6 6l12 12",
    plus: "M12 5v14M5 12h14",
    trash: "M3 6h18M8 6V4h8v2M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6",
    download: "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3",
    refresh: "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15",
    settings: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z",
    eye: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 9a3 3 0 100 6 3 3 0 000-6z",
    brain: "M9.5 2A2.5 2.5 0 017 4.5v1A2.5 2.5 0 014.5 8H4a2 2 0 00-2 2v2a2 2 0 002 2h.5A2.5 2.5 0 017 16.5v1A2.5 2.5 0 009.5 20h5a2.5 2.5 0 002.5-2.5v-1a2.5 2.5 0 012.5-2.5H20a2 2 0 002-2v-2a2 2 0 00-2-2h-.5A2.5 2.5 0 0117 5.5v-1A2.5 2.5 0 0014.5 2h-5z",
    layers: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    zap: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
    grid: "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z",
    alert: "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01",
    copy: "M8 17.929H6c-1.105 0-2-.895-2-2V5c0-1.105.895-2 2-2h8c1.105 0 2 .895 2 2v1M11 21h8c1.105 0 2-.895 2-2V9c0-1.105-.895-2-2-2h-8c-1.105 0-2 .895-2 2v10c0 1.105.895 2 2 2z",
    server: "M20 6v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h12a2 2 0 012 2zM12 12h.01M8 12h.01M16 12h.01",
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={icons[name] || icons.file} />
    </svg>
  );
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');
  
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  
  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #1a1a28;
    --surface3: #222235;
    --border: #2a2a40;
    --accent: #6c63ff;
    --accent2: #ff6584;
    --accent3: #43d9ad;
    --text: #e8e8f0;
    --text2: #8888aa;
    --text3: #555570;
    --success: #43d9ad;
    --warning: #ffd700;
    --error: #ff6584;
    --radius: 10px;
    --font-display: 'Syne', sans-serif;
    --font-mono: 'DM Mono', monospace;
  }
  
  body { background: var(--bg); color: var(--text); font-family: var(--font-mono); overflow-x: hidden; }
  
  .app { display: grid; grid-template-columns: 240px 1fr; grid-template-rows: 56px 1fr; min-height: 100vh; }
  
  .topbar {
    grid-column: 1/-1;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 16px; padding: 0 24px;
    position: sticky; top: 0; z-index: 100;
  }
  .topbar-logo { font-family: var(--font-display); font-weight: 800; font-size: 20px; color: var(--accent); letter-spacing: -0.5px; }
  .topbar-logo span { color: var(--accent3); }
  .topbar-tag { font-size: 10px; color: var(--text3); background: var(--surface3); padding: 2px 8px; border-radius: 20px; border: 1px solid var(--border); }
  .topbar-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
  .provider-badge { display: flex; align-items: center; gap: 6px; background: var(--surface2); border: 1px solid var(--border); border-radius: 6px; padding: 4px 12px; font-size: 11px; cursor: pointer; transition: border-color 0.2s; }
  .provider-badge:hover { border-color: var(--accent); }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); }
  .dot.inactive { background: var(--error); }
  
  .sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 20px 0;
    display: flex; flex-direction: column; gap: 4px;
    overflow-y: auto;
  }
  .nav-section { padding: 8px 16px 4px; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; color: var(--text3); }
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 20px; font-size: 12px; color: var(--text2);
    cursor: pointer; border-left: 2px solid transparent;
    transition: all 0.15s;
  }
  .nav-item:hover { color: var(--text); background: var(--surface2); }
  .nav-item.active { color: var(--accent); background: rgba(108,99,255,0.08); border-left-color: var(--accent); }
  
  .main { background: var(--bg); overflow-y: auto; padding: 32px; }
  
  .page-header { margin-bottom: 32px; }
  .page-title { font-family: var(--font-display); font-size: 28px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
  .page-subtitle { font-size: 12px; color: var(--text2); }
  
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 20px;
  }
  .card-title { font-family: var(--font-display); font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
  
  .btn {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 8px 16px; border-radius: 6px; font-size: 12px;
    font-family: var(--font-mono); font-weight: 500; cursor: pointer;
    border: 1px solid transparent; transition: all 0.15s; white-space: nowrap;
  }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover { background: #7c75ff; }
  .btn-secondary { background: var(--surface2); color: var(--text); border-color: var(--border); }
  .btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
  .btn-success { background: var(--success); color: #000; }
  .btn-danger { background: transparent; color: var(--error); border-color: var(--error); }
  .btn-danger:hover { background: var(--error); color: white; }
  .btn-sm { padding: 4px 10px; font-size: 11px; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  
  .upload-zone {
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 48px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
  }
  .upload-zone::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(circle at 50% 50%, rgba(108,99,255,0.05), transparent 70%);
    pointer-events: none;
  }
  .upload-zone:hover, .upload-zone.drag-over {
    border-color: var(--accent);
    background: rgba(108,99,255,0.04);
  }
  .upload-icon { color: var(--accent); margin: 0 auto 16px; display: block; }
  .upload-title { font-family: var(--font-display); font-size: 16px; font-weight: 600; margin-bottom: 6px; }
  .upload-sub { font-size: 11px; color: var(--text3); }
  
  .doc-list { display: flex; flex-direction: column; gap: 10px; }
  .doc-item {
    display: flex; align-items: center; gap: 14px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 16px; cursor: pointer;
    transition: all 0.15s;
  }
  .doc-item:hover { border-color: var(--accent); }
  .doc-item.selected { border-color: var(--accent); background: rgba(108,99,255,0.06); }
  .doc-info { flex: 1; min-width: 0; }
  .doc-name { font-size: 13px; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .doc-meta { font-size: 10px; color: var(--text3); margin-top: 2px; }
  .status-badge {
    font-size: 10px; padding: 2px 8px; border-radius: 20px;
    text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap;
  }
  .status-parsed { background: rgba(67,217,173,0.1); color: var(--success); border: 1px solid rgba(67,217,173,0.2); }
  .status-pending { background: rgba(255,215,0,0.1); color: var(--warning); border: 1px solid rgba(255,215,0,0.2); }
  .status-parsing { background: rgba(108,99,255,0.1); color: var(--accent); border: 1px solid rgba(108,99,255,0.2); }
  .status-error { background: rgba(255,101,132,0.1); color: var(--error); border: 1px solid rgba(255,101,132,0.2); }
  
  .schema-editor { font-family: var(--font-mono); }
  .schema-field {
    display: grid; grid-template-columns: 1fr 160px auto;
    gap: 8px; align-items: center;
    padding: 10px 0; border-bottom: 1px solid var(--surface3);
  }
  .field-input {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 10px; font-size: 12px;
    color: var(--text); font-family: var(--font-mono);
    transition: border-color 0.15s;
  }
  .field-input:focus { outline: none; border-color: var(--accent); }
  .field-select {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 10px; font-size: 12px;
    color: var(--text2); font-family: var(--font-mono); cursor: pointer;
  }
  .field-select:focus { outline: none; border-color: var(--accent); }
  
  .json-view {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px; font-size: 11px;
    font-family: var(--font-mono); color: var(--text2);
    overflow-x: auto; white-space: pre-wrap; max-height: 400px; overflow-y: auto;
  }
  .json-key { color: var(--accent); }
  .json-string { color: var(--accent3); }
  .json-number { color: var(--warning); }
  .json-null { color: var(--text3); }
  
  .result-field {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid var(--surface3);
  }
  .result-key { font-size: 11px; color: var(--text3); min-width: 140px; padding-top: 2px; }
  .result-value { font-size: 12px; color: var(--text); flex: 1; word-break: break-word; }
  .confidence-bar { height: 3px; border-radius: 2px; margin-top: 4px; }
  .confidence-high { background: var(--success); }
  .confidence-med { background: var(--warning); }
  .confidence-low { background: var(--error); }
  
  .tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
  .tab {
    padding: 10px 18px; font-size: 12px; cursor: pointer;
    color: var(--text2); border-bottom: 2px solid transparent;
    transition: all 0.15s;
  }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
  .tab:hover { color: var(--text); }
  
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  
  .stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px;
  }
  .stat-value { font-family: var(--font-display); font-size: 32px; font-weight: 700; color: var(--text); }
  .stat-label { font-size: 11px; color: var(--text3); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
  
  .suggestion-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.2);
    border-radius: 20px; padding: 4px 12px; font-size: 11px; cursor: pointer;
    color: var(--accent); transition: all 0.15s; margin: 4px;
  }
  .suggestion-chip:hover { background: rgba(108,99,255,0.2); }
  
  .progress-bar { height: 4px; background: var(--surface3); border-radius: 2px; overflow: hidden; margin-top: 8px; }
  .progress-fill { height: 100%; background: var(--accent); border-radius: 2px; transition: width 0.3s; }
  
  .input { 
    background: var(--surface2); border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 12px; font-size: 12px; color: var(--text); font-family: var(--font-mono);
    width: 100%;
  }
  .input:focus { outline: none; border-color: var(--accent); }
  
  .modal-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
    display: flex; align-items: center; justify-content: center; z-index: 200;
  }
  .modal {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 32px; width: 600px; max-width: 95vw; max-height: 85vh; overflow-y: auto;
  }
  .modal-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; margin-bottom: 20px; }
  
  .alert { border-radius: 8px; padding: 12px 16px; font-size: 12px; display: flex; gap: 10px; align-items: flex-start; margin-bottom: 12px; }
  .alert-error { background: rgba(255,101,132,0.1); border: 1px solid rgba(255,101,132,0.2); color: var(--error); }
  .alert-success { background: rgba(67,217,173,0.1); border: 1px solid rgba(67,217,173,0.2); color: var(--success); }
  .alert-info { background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.2); color: var(--accent); }
  
  .spin { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  .fade-in { animation: fadeIn 0.3s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  
  .empty-state { text-align: center; padding: 48px 24px; color: var(--text3); }
  .empty-state-icon { margin: 0 auto 16px; opacity: 0.4; }
  .empty-state-title { font-size: 14px; margin-bottom: 6px; color: var(--text2); }
  .empty-state-sub { font-size: 12px; }
  
  .tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; border: 1px solid var(--border); color: var(--text3); }
  
  select option { background: var(--surface2); }
  
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--surface3); border-radius: 2px; }
  
  .two-panel { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  
  textarea.field-input { resize: vertical; min-height: 80px; }
  
  @media (max-width: 900px) {
    .app { grid-template-columns: 1fr; }
    .sidebar { display: none; }
    .grid-2, .grid-3, .two-panel { grid-template-columns: 1fr; }
  }
`;

// ─── Sub-components ───────────────────────────────────────────────────────────

function JsonHighlight({ data }) {
  const render = (obj, indent = 0) => {
    if (obj === null) return <span className="json-null">null</span>;
    if (typeof obj === "boolean") return <span className="json-null">{obj.toString()}</span>;
    if (typeof obj === "number") return <span className="json-number">{obj}</span>;
    if (typeof obj === "string") return <span className="json-string">"{obj}"</span>;
    if (Array.isArray(obj)) {
      if (obj.length === 0) return <span>{"[]"}</span>;
      return (
        <span>
          {"[\n"}
          {obj.map((item, i) => (
            <span key={i}>
              {"  ".repeat(indent + 1)}{render(item, indent + 1)}{i < obj.length - 1 ? "," : ""}{"\n"}
            </span>
          ))}
          {"  ".repeat(indent) + "]"}
        </span>
      );
    }
    if (typeof obj === "object") {
      const keys = Object.keys(obj);
      if (keys.length === 0) return <span>{"{}"}</span>;
      return (
        <span>
          {"{\n"}
          {keys.map((k, i) => (
            <span key={k}>
              {"  ".repeat(indent + 1)}<span className="json-key">"{k}"</span>{": "}{render(obj[k], indent + 1)}{i < keys.length - 1 ? "," : ""}{"\n"}
            </span>
          ))}
          {"  ".repeat(indent) + "}"}
        </span>
      );
    }
    return <span>{String(obj)}</span>;
  };
  return <div className="json-view">{render(data)}</div>;
}

function StatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{status}</span>;
}

function Alert({ type = "info", children }) {
  return <div className={`alert alert-${type}`}><Icon name="alert" size={14} />{children}</div>;
}

// ─── Provider Setup Modal ────────────────────────────────────────────────────

function ProviderModal({ onClose, onSaved }) {
  const [name, setName] = useState("my-openai");
  const [type, setType] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [isDefault, setIsDefault] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const providerTypes = {
    openai: { label: "OpenAI", fields: ["api_key", "model", "base_url"] },
    anthropic: { label: "Anthropic", fields: ["api_key", "model"] },
    google: { label: "Google AI", fields: ["api_key", "model"] },
    ollama: { label: "Ollama (Local)", fields: ["base_url", "model"] },
    custom: { label: "Custom API", fields: ["endpoint", "api_key"] },
  };

  const save = async () => {
    if (!name || !type) return setError("Name and type are required");
    setLoading(true);
    setError("");
    try {
      const config = {};
      if (apiKey) config.api_key = apiKey;
      if (model) config.model = model;
      if (baseUrl) config[type === "ollama" ? "base_url" : "endpoint"] = baseUrl;

      await api("/jobs/providers/register", {
        method: "POST",
        body: JSON.stringify({ name, provider_type: type, config, is_default: isDefault }),
      });
      onSaved();
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal fade-in" onClick={e => e.stopPropagation()}>
        <div className="modal-title">Connect AI Provider</div>
        {error && <Alert type="error">{error}</Alert>}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>PROVIDER TYPE</div>
            <select className="field-select" style={{ width: "100%" }} value={type} onChange={e => setType(e.target.value)}>
              {Object.entries(providerTypes).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
          </div>
          <div>
            <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>PROVIDER NAME</div>
            <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. my-openai" />
          </div>
          {(type !== "ollama") && (
            <div>
              <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>API KEY</div>
              <input className="input" type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="sk-..." />
            </div>
          )}
          <div>
            <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>MODEL (optional)</div>
            <input className="input" value={model} onChange={e => setModel(e.target.value)} placeholder={type === "anthropic" ? "claude-opus-4-6" : type === "ollama" ? "llama3" : "gpt-4o"} />
          </div>
          {(type === "ollama" || type === "custom") && (
            <div>
              <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>{type === "ollama" ? "BASE URL" : "ENDPOINT URL"}</div>
              <input className="input" value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder={type === "ollama" ? "http://localhost:11434" : "https://api.example.com/v1/chat"} />
            </div>
          )}
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, cursor: "pointer" }}>
            <input type="checkbox" checked={isDefault} onChange={e => setIsDefault(e.target.checked)} />
            Set as default provider
          </label>
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 24, justifyContent: "flex-end" }}>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={save} disabled={loading}>
            {loading ? <span className="spin">↻</span> : <Icon name="check" size={14} />}
            {loading ? "Connecting..." : "Connect Provider"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Upload Page ─────────────────────────────────────────────────────────────

function UploadPage({ onDocumentUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploads, setUploads] = useState([]);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef();

  const handleFiles = async (files) => {
    setUploading(true);
    const results = [];
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await fetch(`${API_BASE}/documents/upload`, { method: "POST", body: formData });
        const data = await res.json();
        results.push({ name: file.name, status: res.ok ? "success" : "error", data });
      } catch (e) {
        results.push({ name: file.name, status: "error", error: e.message });
      }
    }
    setUploads(prev => [...results, ...prev]);
    setUploading(false);
    if (onDocumentUploaded) onDocumentUploaded();
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">Document Upload</div>
        <div className="page-subtitle">Upload PDFs, images, and document batches for AI-powered extraction</div>
      </div>

      <div className="card">
        <div
          className={`upload-zone ${dragging ? "drag-over" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => {
            e.preventDefault(); setDragging(false);
            handleFiles(Array.from(e.dataTransfer.files));
          }}
        >
          <input ref={inputRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg" style={{ display: "none" }}
            onChange={e => handleFiles(Array.from(e.target.files))} />
          <Icon name="upload" size={40} className="upload-icon" />
          <div className="upload-title">{uploading ? "Uploading..." : "Drop documents here"}</div>
          <div className="upload-sub">PDF, PNG, JPEG · Up to 50MB per file · Batch upload supported</div>
          {uploading && <div style={{ marginTop: 16 }}><div className="progress-bar"><div className="progress-fill" style={{ width: "60%" }} /></div></div>}
        </div>
      </div>

      {uploads.length > 0 && (
        <div className="card">
          <div className="card-title"><Icon name="file" size={16} />Recent Uploads</div>
          <div className="doc-list">
            {uploads.map((u, i) => (
              <div key={i} className="doc-item">
                <Icon name="file" size={20} />
                <div className="doc-info">
                  <div className="doc-name">{u.name}</div>
                  <div className="doc-meta">{u.data?.id ? `ID: ${u.data.id.slice(0, 8)}...` : u.error}</div>
                </div>
                <StatusBadge status={u.status === "success" ? "parsed" : "error"} />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid-3">
        {[
          { icon: "file", title: "PDF Support", desc: "Full text, table, and layout extraction from PDF documents" },
          { icon: "eye", title: "Image OCR", desc: "Tesseract-powered text recognition from PNG and JPEG images" },
          { icon: "grid", title: "Batch Processing", desc: "Upload multiple files at once and process them in parallel" },
        ].map(f => (
          <div key={f.title} className="stat-card">
            <div style={{ color: "var(--accent)", marginBottom: 12 }}><Icon name={f.icon} size={24} /></div>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 600, marginBottom: 6 }}>{f.title}</div>
            <div style={{ fontSize: 11, color: "var(--text2)" }}>{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Documents Page ───────────────────────────────────────────────────────────

function DocumentsPage({ onSelect }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api("/documents/");
      setDocs(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, [load]);

  const selectDoc = async (doc) => {
    setSelected(doc.id);
    if (onSelect) onSelect(doc);
    if (doc.status === "parsed") {
      try {
        const d = await api(`/documents/${doc.id}`);
        setDetail(d);
      } catch (e) {}
    }
  };

  const del = async (e, id) => {
    e.stopPropagation();
    if (!confirm("Delete this document?")) return;
    await api(`/documents/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="fade-in">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div className="page-title">Documents</div>
          <div className="page-subtitle">{docs.length} document{docs.length !== 1 ? "s" : ""} in workspace</div>
        </div>
        <button className="btn btn-secondary" onClick={load}><Icon name="refresh" size={14} />Refresh</button>
      </div>

      <div className="two-panel">
        <div>
          {loading && docs.length === 0 ? (
            <div className="empty-state"><div className="spin" style={{ fontSize: 24, marginBottom: 12 }}>↻</div>Loading...</div>
          ) : docs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon"><Icon name="file" size={40} /></div>
              <div className="empty-state-title">No documents yet</div>
              <div className="empty-state-sub">Upload documents to get started</div>
            </div>
          ) : (
            <div className="doc-list">
              {docs.map(doc => (
                <div key={doc.id} className={`doc-item ${selected === doc.id ? "selected" : ""}`} onClick={() => selectDoc(doc)}>
                  <Icon name="file" size={22} />
                  <div className="doc-info">
                    <div className="doc-name">{doc.filename}</div>
                    <div className="doc-meta">{(doc.file_size / 1024).toFixed(1)}KB · {doc.page_count || "?"} pages · {doc.file_type?.split("/")[1]?.toUpperCase()}</div>
                  </div>
                  <StatusBadge status={doc.status} />
                  <button className="btn btn-sm btn-danger" onClick={e => del(e, doc.id)}><Icon name="trash" size={12} /></button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          {detail ? (
            <div className="card">
              <div className="card-title"><Icon name="eye" size={16} />Document Preview</div>
              <div style={{ fontSize: 12, color: "var(--text2)", marginBottom: 12 }}>
                <strong>{detail.filename}</strong> · {detail.page_count} pages
              </div>
              {detail.parsed_content?.pages?.slice(0, 1).map((page, pi) => (
                <div key={pi} style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 10, color: "var(--text3)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Page {page.page_number}</div>
                  {page.blocks?.slice(0, 8).map((block, bi) => (
                    <div key={bi} style={{
                      padding: "6px 10px", marginBottom: 4, borderRadius: 4,
                      background: block.type === "title" ? "rgba(108,99,255,0.08)" : block.type === "table" ? "rgba(67,217,173,0.05)" : "var(--surface2)",
                      fontSize: block.type === "title" ? 13 : 11,
                      fontWeight: block.type === "title" ? 600 : 400,
                      color: block.type === "title" ? "var(--text)" : "var(--text2)",
                      borderLeft: `2px solid ${block.type === "table" ? "var(--accent3)" : block.type === "title" ? "var(--accent)" : "transparent"}`,
                    }}>
                      {block.type === "table" ? `[TABLE: ${block.rows?.length || 0} rows]` : block.text?.slice(0, 120)}
                    </div>
                  ))}
                </div>
              ))}
              {detail.layout_data?.document_structure && (
                <div style={{ marginTop: 12, padding: "10px", background: "var(--surface2)", borderRadius: 6, fontSize: 11, color: "var(--text2)" }}>
                  <strong>Layout:</strong> {detail.layout_data.document_structure}
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300 }}>
              <div className="empty-state">
                <div className="empty-state-icon"><Icon name="eye" size={36} /></div>
                <div className="empty-state-title">Select a document</div>
                <div className="empty-state-sub">Click a document to preview its parsed content</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Schema Builder Page ──────────────────────────────────────────────────────

function SchemaPage() {
  const [schemas, setSchemas] = useState([]);
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [rawJson, setRawJson] = useState("{}");
  const [jsonError, setJsonError] = useState("");
  const [creating, setCreating] = useState(false);
  const [templates, setTemplates] = useState([]);

  const load = useCallback(async () => {
    const data = await api("/schemas/");
    setSchemas(data);
    try {
      const tmpl = await api("/schemas/templates/list");
      setTemplates(tmpl);
    } catch (e) {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const selectSchema = (s) => {
    setSelected(s);
    setEditing(s);
    setName(s.name);
    setDesc(s.description || "");
    setRawJson(JSON.stringify(s.schema_definition, null, 2));
  };

  const save = async () => {
    try {
      const parsed = JSON.parse(rawJson);
      setJsonError("");
      if (editing?.id) {
        await api(`/schemas/${editing.id}`, { method: "PUT", body: JSON.stringify({ name, description: desc, schema_definition: parsed }) });
      } else {
        await api("/schemas/", { method: "POST", body: JSON.stringify({ name, description: desc, schema_definition: parsed }) });
      }
      setCreating(false);
      setEditing(null);
      load();
    } catch (e) {
      if (e instanceof SyntaxError) setJsonError("Invalid JSON: " + e.message);
      else setJsonError(e.message);
    }
  };

  const useTemplate = (tmpl) => {
    setCreating(true);
    setEditing(null);
    setName(tmpl.name);
    setDesc(tmpl.description);
    setRawJson(JSON.stringify(tmpl.schema_definition, null, 2));
  };

  const del = async (id) => {
    if (!confirm("Delete this schema?")) return;
    await api(`/schemas/${id}`, { method: "DELETE" });
    load();
    setEditing(null);
  };

  return (
    <div className="fade-in">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div className="page-title">Schema Builder</div>
          <div className="page-subtitle">Define extraction schemas to guide AI data extraction</div>
        </div>
        <button className="btn btn-primary" onClick={() => { setCreating(true); setEditing(null); setName(""); setDesc(""); setRawJson("{}"); }}>
          <Icon name="plus" size={14} />New Schema
        </button>
      </div>

      <div className="two-panel">
        <div>
          <div className="card">
            <div className="card-title"><Icon name="layers" size={16} />Saved Schemas</div>
            {schemas.length === 0 ? (
              <div className="empty-state" style={{ padding: 24 }}>
                <div className="empty-state-title">No schemas yet</div>
                <div className="empty-state-sub">Create one or use a template below</div>
              </div>
            ) : (
              <div className="doc-list">
                {schemas.map(s => (
                  <div key={s.id} className={`doc-item ${selected?.id === s.id ? "selected" : ""}`} onClick={() => selectSchema(s)}>
                    <Icon name="schema" size={20} />
                    <div className="doc-info">
                      <div className="doc-name">{s.name}</div>
                      <div className="doc-meta">{s.description || "No description"}</div>
                    </div>
                    <button className="btn btn-sm btn-danger" onClick={e => { e.stopPropagation(); del(s.id); }}><Icon name="trash" size={12} /></button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-title"><Icon name="zap" size={16} />Templates</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {templates.map(t => (
                <button key={t.name} className="suggestion-chip" onClick={() => useTemplate(t)}>{t.name}</button>
              ))}
            </div>
          </div>
        </div>

        <div>
          {(creating || editing) && (
            <div className="card fade-in">
              <div className="card-title">{editing ? "Edit Schema" : "New Schema"}</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>NAME</div>
                  <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Invoice Schema" />
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>DESCRIPTION</div>
                  <input className="input" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Extracts fields from invoice documents" />
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>SCHEMA DEFINITION (JSON)</div>
                  {jsonError && <Alert type="error">{jsonError}</Alert>}
                  <textarea
                    className="field-input"
                    style={{ width: "100%", minHeight: 280, fontFamily: "var(--font-mono)", fontSize: 11, resize: "vertical" }}
                    value={rawJson}
                    onChange={e => { setRawJson(e.target.value); setJsonError(""); }}
                    spellCheck={false}
                  />
                </div>
                <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                  <button className="btn btn-secondary" onClick={() => { setCreating(false); setEditing(null); }}>Cancel</button>
                  <button className="btn btn-primary" onClick={save}><Icon name="check" size={14} />Save Schema</button>
                </div>
              </div>
            </div>
          )}
          {!creating && !editing && (
            <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300 }}>
              <div className="empty-state">
                <div className="empty-state-icon"><Icon name="schema" size={36} /></div>
                <div className="empty-state-title">Select or create a schema</div>
                <div className="empty-state-sub">Schemas define what data to extract from documents</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Extraction Page ──────────────────────────────────────────────────────────

function ExtractionPage() {
  const [docs, setDocs] = useState([]);
  const [schemas, setSchemas] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [selectedSchema, setSelectedSchema] = useState("");
  const [running, setRunning] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [suggestion, setSuggestion] = useState(null);
  const [suggesting, setSuggesting] = useState(false);
  const [error, setError] = useState("");
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("");

  useEffect(() => {
    Promise.all([api("/documents/"), api("/schemas/"), api("/jobs/providers/list")])
      .then(([d, s, p]) => { setDocs(d); setSchemas(s); setProviders(p.providers || []); })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!jobId || jobStatus?.status === "completed" || jobStatus?.status === "failed") return;
    const t = setInterval(async () => {
      const job = await api(`/jobs/${jobId}`);
      setJobStatus(job);
      if (job.status === "completed") {
        setRunning(false);
        loadResults();
      }
    }, 1500);
    return () => clearInterval(t);
  }, [jobId, jobStatus]);

  const loadResults = async () => {
    if (!selectedDoc) return;
    const data = await api(`/extraction/results/${selectedDoc}`);
    setResults(data);
  };

  const suggestSchema = async () => {
    if (!selectedDoc) return setError("Select a document first");
    setSuggesting(true);
    setError("");
    try {
      const data = await api(`/documents/${selectedDoc}/suggest-schema`, { method: "POST" });
      setSuggestion(data);
    } catch (e) {
      setError(e.message);
    }
    setSuggesting(false);
  };

  const useSchemaFromSuggestion = async () => {
    if (!suggestion) return;
    const s = await api("/schemas/", {
      method: "POST",
      body: JSON.stringify({
        name: `AI Suggested - ${suggestion.document_type || "Unknown"}`,
        description: `Auto-suggested schema (confidence: ${(suggestion.confidence * 100).toFixed(0)}%)`,
        schema_definition: suggestion.schema,
      }),
    });
    setSchemas(prev => [s, ...prev]);
    setSelectedSchema(s.id);
    setSuggestion(null);
  };

  const run = async () => {
    if (!selectedDoc || !selectedSchema) return setError("Select a document and schema");
    setRunning(true);
    setError("");
    setResults([]);
    setJobStatus(null);
    try {
      const job = await api("/extraction/run", {
        method: "POST",
        body: JSON.stringify({
          document_id: selectedDoc,
          schema_id: selectedSchema,
          provider: selectedProvider || undefined,
          validate: true,
        }),
      });
      setJobId(job.job_id);
      setJobStatus({ status: "queued", progress: 0 });
    } catch (e) {
      setError(e.message);
      setRunning(false);
    }
  };

  const exportData = (fmt) => {
    window.open(`${API_BASE}/export/${selectedDoc}/${fmt}`, "_blank");
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">Extraction</div>
        <div className="page-subtitle">AI-powered schema-guided data extraction</div>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title"><Icon name="file" size={16} />Select Document</div>
          <select className="field-select" style={{ width: "100%" }} value={selectedDoc} onChange={e => { setSelectedDoc(e.target.value); setResults([]); }}>
            <option value="">Choose a document...</option>
            {docs.filter(d => d.status === "parsed" || d.status === "split").map(d => (
              <option key={d.id} value={d.id}>{d.filename}</option>
            ))}
          </select>
          <div style={{ marginTop: 12 }}>
            <button className="btn btn-secondary" style={{ width: "100%" }} onClick={suggestSchema} disabled={!selectedDoc || suggesting}>
              {suggesting ? <span className="spin">↻</span> : <Icon name="brain" size={14} />}
              {suggesting ? "Analyzing..." : "AI Schema Suggestion"}
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-title"><Icon name="schema" size={16} />Select Schema</div>
          <select className="field-select" style={{ width: "100%" }} value={selectedSchema} onChange={e => setSelectedSchema(e.target.value)}>
            <option value="">Choose a schema...</option>
            {schemas.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          {providers.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 10, color: "var(--text3)", marginBottom: 6 }}>PROVIDER (optional)</div>
              <select className="field-select" style={{ width: "100%" }} value={selectedProvider} onChange={e => setSelectedProvider(e.target.value)}>
                <option value="">Use default provider</option>
                {providers.map(p => <option key={p.name} value={p.name}>{p.name} ({p.type})</option>)}
              </select>
            </div>
          )}
        </div>
      </div>

      {suggestion && (
        <div className="card fade-in" style={{ borderColor: "rgba(108,99,255,0.3)" }}>
          <div className="card-title"><Icon name="brain" size={16} />AI Schema Suggestion</div>
          <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
            <span className="tag">Type: {suggestion.document_type}</span>
            <span className="tag">Confidence: {(suggestion.confidence * 100).toFixed(0)}%</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", marginBottom: 16 }}>
            {(suggestion.suggestions || []).map(s => (
              <span key={s} className="suggestion-chip"><Icon name="check" size={10} />{s}</span>
            ))}
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" onClick={useSchemaFromSuggestion}><Icon name="plus" size={14} />Use This Schema</button>
            <button className="btn btn-secondary" onClick={() => setSuggestion(null)}><Icon name="x" size={14} />Dismiss</button>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 24 }}>
        <button className="btn btn-primary" onClick={run} disabled={running || !selectedDoc || !selectedSchema} style={{ padding: "10px 24px" }}>
          {running ? <span className="spin">↻</span> : <Icon name="zap" size={14} />}
          {running ? "Extracting..." : "Run Extraction"}
        </button>
        {results.length > 0 && (
          <>
            <button className="btn btn-secondary" onClick={() => exportData("json")}><Icon name="download" size={14} />JSON</button>
            <button className="btn btn-secondary" onClick={() => exportData("csv")}><Icon name="download" size={14} />CSV</button>
            <button className="btn btn-secondary" onClick={() => exportData("excel")}><Icon name="download" size={14} />Excel</button>
          </>
        )}
      </div>

      {jobStatus && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 12 }}>Job Status: <strong>{jobStatus.status}</strong></span>
            <StatusBadge status={jobStatus.status === "completed" ? "parsed" : jobStatus.status === "failed" ? "error" : "parsing"} />
          </div>
          <div className="progress-bar" style={{ marginTop: 10 }}>
            <div className="progress-fill" style={{ width: `${(jobStatus.progress || 0) * 100}%` }} />
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="card fade-in">
          <div className="card-title"><Icon name="check" size={16} />Extraction Results ({results.length} segment{results.length !== 1 ? "s" : ""})</div>
          {results.map((r, i) => (
            <div key={r.id} style={{ marginBottom: i < results.length - 1 ? 24 : 0, paddingBottom: i < results.length - 1 ? 24 : 0, borderBottom: i < results.length - 1 ? "1px solid var(--border)" : "none" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>Segment {i + 1}</span>
                {r.validation_passed
                  ? <span className="status-badge status-parsed">✓ Validated</span>
                  : <span className="status-badge status-error">⚠ Validation Issues</span>}
              </div>
              {r.validation_errors?.length > 0 && (
                <Alert type="error">{r.validation_errors.map(e => `${e.field}: ${e.error}`).join("; ")}</Alert>
              )}
              <ResultTree data={r.extracted_data} confidence={r.confidence_scores} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ResultTree({ data, confidence = {}, path = "" }) {
  if (!data) return null;
  return (
    <div>
      {Object.entries(data).map(([key, value]) => {
        const fullPath = path ? `${path}.${key}` : key;
        const conf = confidence[key] || confidence[fullPath];
        if (Array.isArray(value) && value.length > 0 && typeof value[0] === "object") {
          return (
            <div key={key} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>{key} ({value.length} items)</div>
              <div style={{ background: "var(--surface2)", borderRadius: 6, padding: 12, overflowX: "auto" }}>
                <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
                  <thead>
                    <tr>{Object.keys(value[0]).map(k => <th key={k} style={{ textAlign: "left", padding: "4px 8px", color: "var(--text3)", borderBottom: "1px solid var(--border)" }}>{k}</th>)}</tr>
                  </thead>
                  <tbody>
                    {value.map((row, ri) => (
                      <tr key={ri}>
                        {Object.values(row).map((cell, ci) => (
                          <td key={ci} style={{ padding: "4px 8px", color: "var(--text2)", borderBottom: "1px solid var(--surface3)" }}>{String(cell ?? "—")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        }
        if (typeof value === "object" && value !== null && !Array.isArray(value)) {
          return (
            <div key={key} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: "var(--accent)", marginBottom: 6 }}>{key}</div>
              <div style={{ paddingLeft: 16, borderLeft: "2px solid var(--border)" }}>
                <ResultTree data={value} confidence={confidence} path={fullPath} />
              </div>
            </div>
          );
        }
        const confVal = typeof conf === "number" ? conf : null;
        return (
          <div key={key} className="result-field">
            <div className="result-key">{key}</div>
            <div style={{ flex: 1 }}>
              <div className="result-value">{value === null || value === undefined ? <span style={{ color: "var(--text3)" }}>—</span> : String(value)}</div>
              {confVal !== null && (
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
                  <div className="progress-bar" style={{ width: 60, height: 2, margin: 0 }}>
                    <div className={`progress-fill ${confVal > 0.8 ? "confidence-high" : confVal > 0.5 ? "confidence-med" : "confidence-low"}`}
                      style={{ width: `${confVal * 100}%`, background: confVal > 0.8 ? "var(--success)" : confVal > 0.5 ? "var(--warning)" : "var(--error)" }} />
                  </div>
                  <span style={{ fontSize: 10, color: "var(--text3)" }}>{(confVal * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Jobs Dashboard ───────────────────────────────────────────────────────────

function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const load = useCallback(async () => {
    const data = await api("/jobs/");
    setJobs(data);
  }, []);

  useEffect(() => { load(); const t = setInterval(load, 3000); return () => clearInterval(t); }, [load]);

  return (
    <div className="fade-in">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div className="page-title">Processing Jobs</div>
          <div className="page-subtitle">Monitor background extraction tasks</div>
        </div>
        <button className="btn btn-secondary" onClick={load}><Icon name="refresh" size={14} />Refresh</button>
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        {["completed", "running", "failed"].map(s => {
          const count = jobs.filter(j => j.status === s).length;
          const colors = { completed: "var(--success)", running: "var(--accent)", failed: "var(--error)" };
          return (
            <div key={s} className="stat-card">
              <div className="stat-value" style={{ color: colors[s] }}>{count}</div>
              <div className="stat-label">{s}</div>
            </div>
          );
        })}
      </div>

      {jobs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><Icon name="server" size={40} /></div>
          <div className="empty-state-title">No jobs yet</div>
          <div className="empty-state-sub">Run extractions to see jobs here</div>
        </div>
      ) : (
        <div className="card">
          <div className="card-title"><Icon name="grid" size={16} />All Jobs</div>
          <div className="doc-list">
            {jobs.map(job => (
              <div key={job.id} className="doc-item" style={{ cursor: "default" }}>
                <Icon name="zap" size={20} />
                <div className="doc-info">
                  <div className="doc-name">{job.job_type} · {job.id.slice(0, 8)}...</div>
                  <div className="doc-meta">
                    {job.created_at ? new Date(job.created_at).toLocaleString() : ""} · {job.processed_items}/{job.total_items} items
                  </div>
                  {job.status === "running" && (
                    <div className="progress-bar" style={{ marginTop: 6 }}>
                      <div className="progress-fill" style={{ width: `${(job.progress || 0) * 100}%` }} />
                    </div>
                  )}
                  {job.error_message && <div style={{ fontSize: 10, color: "var(--error)", marginTop: 4 }}>{job.error_message}</div>}
                </div>
                <StatusBadge status={job.status === "completed" ? "parsed" : job.status === "failed" ? "error" : "parsing"} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Settings Page ────────────────────────────────────────────────────────────

function SettingsPage({ onProviderAdded }) {
  const [providers, setProviders] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [apiStatus, setApiStatus] = useState(null);

  const load = useCallback(async () => {
    try {
      const [prov, health] = await Promise.all([api("/jobs/providers/list"), api("/health").catch(() => null)]);
      setProviders(prov.providers || []);
      setApiStatus(health);
    } catch (e) {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const removeProvider = async (name) => {
    if (!confirm(`Remove provider "${name}"?`)) return;
    await api(`/jobs/providers/${name}`, { method: "DELETE" });
    load();
    if (onProviderAdded) onProviderAdded();
  };

  const setDefault = async (name) => {
    await api(`/jobs/providers/${name}/set-default`, { method: "POST" });
    load();
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">Settings</div>
        <div className="page-subtitle">Configure AI providers and platform settings</div>
      </div>

      {showModal && <ProviderModal onClose={() => setShowModal(false)} onSaved={() => { load(); if (onProviderAdded) onProviderAdded(); }} />}

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div className="card-title" style={{ margin: 0 }}><Icon name="server" size={16} />LLM Providers</div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}><Icon name="plus" size={14} />Add Provider</button>
        </div>

        {providers.length === 0 ? (
          <Alert type="info">No AI providers configured. Add a provider to enable extraction.</Alert>
        ) : (
          <div className="doc-list">
            {providers.map(p => (
              <div key={p.name} className="doc-item">
                <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(108,99,255,0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon name="brain" size={18} />
                </div>
                <div className="doc-info">
                  <div className="doc-name">{p.name} {p.is_default && <span className="tag" style={{ marginLeft: 8 }}>DEFAULT</span>}</div>
                  <div className="doc-meta">{p.type}</div>
                </div>
                <div className="dot" />
                <div style={{ display: "flex", gap: 8 }}>
                  {!p.is_default && <button className="btn btn-secondary btn-sm" onClick={() => setDefault(p.name)}>Set Default</button>}
                  <button className="btn btn-danger btn-sm" onClick={() => removeProvider(p.name)}><Icon name="trash" size={12} /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {apiStatus && (
        <div className="card">
          <div className="card-title"><Icon name="check" size={16} />API Status</div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <span className="status-badge status-parsed">● API Online</span>
            <span style={{ fontSize: 12, color: "var(--text2)" }}>Queue: {apiStatus.queue?.running ? "Running" : "Idle"}</span>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-title"><Icon name="layers" size={16} />Supported Providers</div>
        <div className="grid-3">
          {[
            { name: "OpenAI", type: "openai", models: "GPT-4o, GPT-4, GPT-3.5" },
            { name: "Anthropic", type: "anthropic", models: "Claude Opus, Sonnet, Haiku" },
            { name: "Google AI", type: "google", models: "Gemini 1.5 Pro/Flash" },
            { name: "Ollama", type: "ollama", models: "Llama 3, Mistral, any local" },
            { name: "Custom API", type: "custom", models: "Any OpenAI-compatible endpoint" },
          ].map(p => (
            <div key={p.type} className="stat-card" style={{ cursor: "pointer" }} onClick={() => setShowModal(true)}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{p.name}</div>
              <div style={{ fontSize: 10, color: "var(--text3)" }}>{p.models}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState("upload");
  const [providers, setProviders] = useState([]);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadProviders = useCallback(async () => {
    try {
      const data = await api("/jobs/providers/list");
      setProviders(data.providers || []);
    } catch (e) {}
  }, []);

  useEffect(() => { loadProviders(); }, [loadProviders]);

  const defaultProvider = providers.find(p => p.is_default);
  const hasProvider = providers.some(p => p.available);

  const nav = [
    { id: "upload", label: "Upload", icon: "upload", section: "INGEST" },
    { id: "documents", label: "Documents", icon: "file", section: null },
    { id: "schema", label: "Schemas", icon: "schema", section: "DEFINE" },
    { id: "extract", label: "Extract", icon: "extract", section: "PROCESS" },
    { id: "jobs", label: "Jobs", icon: "grid", section: null },
    { id: "settings", label: "Settings", icon: "settings", section: "CONFIGURE" },
  ];

  return (
    <>
      <style>{styles}</style>
      <div className="app">
        <div className="topbar">
          <div className="topbar-logo">Doc<span>Extract</span></div>
          <div className="topbar-tag">Agentic Extraction Platform</div>
          <div className="topbar-right">
            {!hasProvider && (
              <Alert type="info" style={{ margin: 0 }}>
                <span>No AI provider configured.</span>
              </Alert>
            )}
            <button
              className="provider-badge"
              onClick={() => setPage("settings")}
            >
              <div className={`dot ${hasProvider ? "" : "inactive"}`} />
              {defaultProvider ? defaultProvider.name : "No Provider"}
            </button>
          </div>
        </div>

        <nav className="sidebar">
          {nav.map(item => (
            <div key={item.id}>
              {item.section && <div className="nav-section">{item.section}</div>}
              <div
                className={`nav-item ${page === item.id ? "active" : ""}`}
                onClick={() => setPage(item.id)}
              >
                <Icon name={item.icon} size={16} />
                {item.label}
              </div>
            </div>
          ))}
        </nav>

        <main className="main">
          {!hasProvider && page !== "settings" && (
            <Alert type="info">
              No AI provider configured. <button className="btn btn-secondary btn-sm" style={{ marginLeft: 8 }} onClick={() => setPage("settings")}>Add Provider →</button>
            </Alert>
          )}
          {page === "upload" && <UploadPage onDocumentUploaded={() => setRefreshKey(k => k + 1)} />}
          {page === "documents" && <DocumentsPage key={refreshKey} />}
          {page === "schema" && <SchemaPage />}
          {page === "extract" && <ExtractionPage />}
          {page === "jobs" && <JobsPage />}
          {page === "settings" && <SettingsPage onProviderAdded={loadProviders} />}
        </main>
      </div>
    </>
  );
}
