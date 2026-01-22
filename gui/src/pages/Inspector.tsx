import React, { useState, useCallback } from 'react';
import { useLocale } from '../contexts/LocaleContext';
import {
  mcpInitialize,
  mcpSendInitialized,
  mcpListTools,
  mcpCallTool,
  type McpHeader,
  type McpTool,
  type CallToolResult,
} from '../services/mcpClient';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

/* Icons for connection actions */
const ConnectIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M13.828 10.172a4 4 0 0 0-5.656 0l-4 4a4 4 0 1 0 5.656 5.656l1.102-1.101m-.758-4.899a4 4 0 0 0 5.656 0l4-4a4 4 0 0 0-5.656-5.656l-1.1 1.1" />
  </svg>
);
const ReconnectIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
  </svg>
);
const DisconnectIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
  </svg>
);
const EyeIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
    <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
  </svg>
);
const EyeOffIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M3.98 8.223A10.477 10.477 0 0 0 1.946 12c1.054 4.712 5.048 8 10.054 8 2.06 0 4.02-.573 5.634-1.624" />
    <path d="M6.324 15.43a10.48 10.48 0 0 0 1.746 2.147 10.477 10.477 0 0 0 5.556 3.027" />
    <path d="M12 4.5c-1.23 0-2.4.21-3.48.58" />
    <path d="M21.27 2.5 2.73 21.5" />
  </svg>
);

/** Tokenize JSON string (no sticky regex). */
function tokenizeJson(s: string): Array<{ type: 'key' | 'string' | 'number' | 'keyword' | 'punct' | 'space'; value: string }> {
  const out: Array<{ type: 'key' | 'string' | 'number' | 'keyword' | 'punct' | 'space'; value: string }> = [];
  let i = 0;
  while (i < s.length) {
    const rest = s.slice(i);
    let m = rest.match(/^(\s+)/);
    if (m) {
      out.push({ type: 'space', value: m[1] });
      i += m[1].length;
      continue;
    }
    m = rest.match(/^"(?:[^"\\]|\\.)*"/);
    if (m) {
      const raw = m[0];
      const afterRest = s.slice(i + raw.length).match(/^\s*:/);
      out.push({ type: afterRest ? 'key' : 'string', value: raw });
      i += raw.length;
      continue;
    }
    m = rest.match(/^(-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/);
    if (m) {
      out.push({ type: 'number', value: m[1] });
      i += m[1].length;
      continue;
    }
    m = rest.match(/^(true|false|null)/);
    if (m) {
      out.push({ type: 'keyword', value: m[1] });
      i += m[1].length;
      continue;
    }
    m = rest.match(/^([{}\[\],:])/);
    if (m) {
      out.push({ type: 'punct', value: m[1] });
      i += m[1].length;
      continue;
    }
    out.push({ type: 'punct', value: s[i] });
    i += 1;
  }
  return out;
}

function JsonHighlight({ data, fallback }: { data: unknown; fallback: string }) {
  if (data == null) {
    return <span style={{ color: 'var(--json-hl-fallback)' }}>{fallback}</span>;
  }
  let str: string;
  try {
    str = JSON.stringify(data, null, 2);
  } catch {
    return <span style={{ color: 'var(--json-hl-err)' }}>{String(data)}</span>;
  }
  const tokens = tokenizeJson(str);
  return (
    <>
      {tokens.map((t, i) =>
        t.type === 'space' ? (
          <React.Fragment key={i}>{t.value}</React.Fragment>
        ) : (
          <span key={i} style={{ color: `var(--json-hl-${t.type})` }}>{t.value}</span>
        )
      )}
    </>
  );
}

const DEFAULT_MCP_SERVER_URL = 'http://localhost:8011/api/mcp/';

function buildEmptyHeaders(): McpHeader[] {
  return [{ key: 'Authorization', value: '' }];
}

function parseSchemaValue(
  type: string | undefined,
  raw: string
): string | number | boolean | object | null {
  const t = (type || 'string').toLowerCase();
  if (raw.trim() === '') return t === 'boolean' ? false : null;
  if (t === 'number') return Number(raw);
  if (t === 'boolean') return /^(true|1|on|yes)$/i.test(raw.trim());
  if (t === 'object' || t === 'array') {
    try {
      return JSON.parse(raw) as object;
    } catch {
      return raw;
    }
  }
  return raw;
}

function ToolForm({
  tool,
  onRun,
  running,
  t,
}: {
  tool: McpTool;
  onRun: (args: Record<string, unknown>) => void;
  running: boolean;
  t: (key: string) => string;
}) {
  const schema = tool.inputSchema || { type: 'object', properties: {}, required: [] };
  const props = schema.properties || {};
  const required = new Set(schema.required || []);
  const [values, setValues] = useState<Record<string, string>>(() => {
    const v: Record<string, string> = {};
    for (const k of Object.keys(props)) v[k] = '';
    return v;
  });
  const [err, setErr] = useState<string | null>(null);

  const handleRun = () => {
    setErr(null);
    const args: Record<string, unknown> = {};
    for (const k of Object.keys(props)) {
      const p = props[k];
      const raw = (values[k] ?? '').trim();
      if (required.has(k) && !raw) {
        setErr(`"${k}" ${t('inspector.required')}`);
        return;
      }
      const val = parseSchemaValue(p?.type as string | undefined, raw);
      if (val != null) args[k] = val;
    }
    onRun(args);
  };

  return (
    <div className="space-y-3 pt-2">
      {Object.entries(props).map(([key, prop]) => {
        const sch = (prop || {}) as { type?: string; description?: string };
        const t = (sch.type || 'string').toLowerCase();
        const isReq = required.has(key);
        const inputId = `tool-${tool.name}-${key}`;
        return (
          <div key={key}>
            <label
              htmlFor={inputId}
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              {key} {isReq && <span className="text-red-500">*</span>}
            </label>
            {sch.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{sch.description}</p>
            )}
            {t === 'boolean' ? (
              <div className="flex items-center gap-2">
                <input
                  id={inputId}
                  type="checkbox"
                  checked={/^(true|1|on|yes)$/i.test((values[key] ?? '').trim())}
                  onChange={(e) =>
                    setValues((s) => ({ ...s, [key]: e.target.checked ? 'true' : 'false' }))
                  }
                  className="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
            ) : t === 'number' ? (
              <input
                id={inputId}
                type="number"
                value={values[key] ?? ''}
                onChange={(e) => setValues((s) => ({ ...s, [key]: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
              />
            ) : t === 'object' || t === 'array' ? (
              <textarea
                id={inputId}
                value={values[key] ?? ''}
                onChange={(e) => setValues((s) => ({ ...s, [key]: e.target.value }))}
                placeholder='{} or []'
                rows={3}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 font-mono text-sm"
              />
            ) : (
              <input
                id={inputId}
                type="text"
                value={values[key] ?? ''}
                onChange={(e) => setValues((s) => ({ ...s, [key]: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
              />
            )}
          </div>
        );
      })}
      {Object.keys(props).length === 0 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">{t('inspector.noParameters')}</p>
      )}
      {err && <p className="text-sm text-red-600 dark:text-red-400">{err}</p>}
      <Button onClick={handleRun} disabled={running} size="sm">
        {running ? t('inspector.running') : t('inspector.run')}
      </Button>
    </div>
  );
}

function formatCallResult(r: CallToolResult): string {
  if (r.isError) {
    const parts = (r.content || [])
      .filter((c) => c.type === 'text' && c.text)
      .map((c) => (c as { text: string }).text);
    return `Error: ${parts.join('\n') || 'Unknown error'}`;
  }
  const parts = (r.content || [])
    .filter((c) => c.type === 'text' && c.text)
    .map((c) => (c as { text: string }).text);
  if (parts.length) return parts.join('\n');
  try {
    return JSON.stringify(r, null, 2);
  } catch {
    return String(r);
  }
}

/** Strip leading "Bearer " from value for display in the token-only input. */
function stripBearerPrefix(v: string): string {
  return (v || '').replace(/^Bearer\s+/i, '');
}

/** Build header value: add "Bearer " prefix when non-empty and not already present. */
function withBearerPrefix(v: string): string {
  const raw = (v || '').trim();
  return raw === '' ? '' : /^Bearer\s+/i.test(raw) ? raw : `Bearer ${raw}`;
}

export const Inspector: React.FC = () => {
  const { t } = useLocale();
  const [url, setUrl] = useState(DEFAULT_MCP_SERVER_URL);
  const [headers, setHeaders] = useState<McpHeader[]>(buildEmptyHeaders);
  const [visibleValueIndex, setVisibleValueIndex] = useState<number | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [tools, setTools] = useState<McpTool[]>([]);
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [result, setResult] = useState<{ tool: string; result: string; isError?: boolean } | null>(
    null
  );
  const [selectedTool, setSelectedTool] = useState<McpTool | null>(null);

  const baseUrl = (url || DEFAULT_MCP_SERVER_URL).trim() || DEFAULT_MCP_SERVER_URL;
  const userHeaders = headers
    .filter((h) => (h.key || '').trim())
    .map((h) => ({ key: (h.key || '').trim(), value: withBearerPrefix(h.value || '') }));

  const handleConnect = useCallback(async () => {
    setConnectError(null);
    setConnecting(true);
    try {
      const initRet = await mcpInitialize(baseUrl, userHeaders);
      setSessionId(initRet.sessionId ?? null);
      await mcpSendInitialized(baseUrl, userHeaders, initRet.sessionId);
      const { tools: list } = await mcpListTools(baseUrl, userHeaders, initRet.sessionId);
      setTools(list);
      setConnected(true);
      setResult(null);
    } catch (e: unknown) {
      setConnectError(e instanceof Error ? e.message : String(e));
    } finally {
      setConnecting(false);
    }
  }, [baseUrl, userHeaders]);

  const handleDisconnect = useCallback(() => {
    setConnected(false);
    setSessionId(null);
    setTools([]);
    setSelectedTool(null);
    setResult(null);
    setConnectError(null);
  }, []);

  const handleReconnect = useCallback(async () => {
    handleDisconnect();
    await handleConnect();
  }, [handleDisconnect, handleConnect]);

  const handleRunTool = useCallback(
    async (name: string, args: Record<string, unknown>) => {
      setRunningTool(name);
      try {
        const r = await mcpCallTool(baseUrl, userHeaders, name, args, sessionId);
        setResult({
          tool: name,
          result: formatCallResult(r),
          isError: r.isError,
        });
      } catch (e: unknown) {
        setResult({
          tool: name,
          result: e instanceof Error ? e.message : String(e),
          isError: true,
        });
      } finally {
        setRunningTool(null);
      }
    },
    [baseUrl, userHeaders, sessionId]
  );

  const addHeader = () => setHeaders((h) => [...h, { key: '', value: '' }]);
  const removeHeader = (i: number) => {
    setHeaders((h) => h.filter((_, idx) => idx !== i));
    setVisibleValueIndex((v) => (v === i ? null : v != null && v > i ? v - 1 : v));
  };
  const updateHeader = (i: number, field: 'key' | 'value', val: string) =>
    setHeaders((h) => {
      const n = [...h];
      n[i] = { ...n[i], [field]: val };
      return n;
    });
  const toggleValueVisibility = (i: number) =>
    setVisibleValueIndex((v) => (v === i ? null : i));

  const handleSelectTool = useCallback((t: McpTool) => {
    setResult(null);
    setSelectedTool(t);
  }, []);

  return (
    <div className="flex flex-col w-full max-w-full">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('inspector.title')}</h1>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {t('inspector.intro')}
      </p>

      {/* Connection */}
      <section className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 mb-4 flex-shrink-0">
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('inspector.connection')}</h2>
          {connected && (
            <span className="flex items-center gap-1.5 text-sm font-medium text-green-600 dark:text-green-400">
              <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" aria-hidden />
              {t('inspector.connected')}
            </span>
          )}
          {connectError && !connected && (
            <span className="flex items-center gap-1.5 text-sm font-medium text-red-600 dark:text-red-400">
              <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" aria-hidden />
              {t('inspector.notConnected')}
            </span>
          )}
        </div>
        <div className="space-y-3">
          <Input
            label={t('inspector.serverUrl')}
            type="url"
            value={url}
            onValueChange={setUrl}
            placeholder={DEFAULT_MCP_SERVER_URL}
          />
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                {t('inspector.requestHeaders')}
              </label>
              <Button type="button" variant="secondary" size="sm" onClick={addHeader}>
                {t('inspector.addHeader')}
              </Button>
            </div>
            <div className="space-y-2">
              {headers.map((h, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <input
                    value={h.key}
                    onChange={(e) => updateHeader(i, 'key', e.target.value)}
                    placeholder={t('inspector.headerName')}
                    className="flex-1 px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 text-sm"
                  />
                  <div className="flex-1 flex items-center gap-1 min-w-0">
                    <input
                      type={visibleValueIndex === i ? 'text' : 'password'}
                      value={`Bearer ${stripBearerPrefix(h.value)}`}
                      onChange={(e) =>
                        updateHeader(i, 'value', e.target.value.replace(/^Bearer\s*/i, ''))
                      }
                      placeholder={t('inspector.headerValue')}
                      className="flex-1 min-w-0 px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => toggleValueVisibility(i)}
                      className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex-shrink-0"
                      aria-label={visibleValueIndex === i ? t('inspector.hideValue') : t('inspector.showValue')}
                      title={visibleValueIndex === i ? t('inspector.hide') : t('inspector.show')}
                    >
                      {visibleValueIndex === i ? (
                        <EyeOffIcon className="w-4 h-4" />
                      ) : (
                        <EyeIcon className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <Button
                    type="button"
                    variant="danger"
                    size="sm"
                    onClick={() => removeHeader(i)}
                    disabled={headers.length <= 1}
                  >
                    {t('inspector.remove')}
                  </Button>
                </div>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            {!connected ? (
              <Button onClick={handleConnect} disabled={connecting} className="inline-flex items-center gap-2">
                <ConnectIcon className="w-4 h-4 flex-shrink-0" />
                {connecting ? t('inspector.connecting') : t('inspector.connect')}
              </Button>
            ) : (
              <>
                <Button variant="secondary" onClick={handleReconnect} className="inline-flex items-center gap-2">
                  <ReconnectIcon className="w-4 h-4 flex-shrink-0" />
                  {t('inspector.reconnect')}
                </Button>
                <Button variant="secondary" onClick={handleDisconnect} className="inline-flex items-center gap-2">
                  <DisconnectIcon className="w-4 h-4 flex-shrink-0" />
                  {t('inspector.disconnect')}
                </Button>
              </>
            )}
          </div>
          {connectError && (
            <p className="text-sm text-red-600 dark:text-red-400">{t('inspector.connectionFailed')}: {connectError}</p>
          )}
        </div>
      </section>

      {/* Tools: left (names) + right (detail) */}
      {connected && (
        <section className="flex gap-4 mb-4">
          {/* Left: tool names in boxes */}
          <div className="w-[30%] min-w-0 flex flex-col">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">{t('inspector.tools')}</h2>
            <div className="space-y-2 pr-2">
              {tools.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('inspector.noTools')}</p>
              ) : (
                tools.map((t) => (
                  <button
                    key={t.name}
                    type="button"
                    onClick={() => handleSelectTool(t)}
                    className={`w-full text-left px-4 py-3 rounded-lg border font-mono font-medium transition-colors ${
                      selectedTool?.name === t.name
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 ring-2 ring-primary-500/50'
                        : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    {t.name}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Right: description, schema, params, run, result (top aligned with first tool: spacer = Tools h2 + mb-3) */}
          <div className="w-[70%] min-w-0 flex flex-col">
            <div className="h-10 flex-shrink-0" aria-hidden />
            <div className="flex-1 min-h-0 flex flex-col rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
            {!selectedTool ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('inspector.clickTool')}</p>
            ) : (
              <>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex-shrink-0">
                  {selectedTool.name}
                </h2>
                {/* Description */}
                {selectedTool.description && (
                  <div className="mb-4 flex-shrink-0 min-w-0">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('inspector.description')}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line break-words">{selectedTool.description}</p>
                  </div>
                )}
                {/* Output Schema (optional in tools/list) */}
                <div className="mb-4 flex-shrink-0 min-w-0">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('inspector.outputSchema')}</h3>
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700 text-xs font-mono overflow-x-auto whitespace-pre">
                    <JsonHighlight data={selectedTool.outputSchema} fallback={t('inspector.notProvided')} />
                  </div>
                </div>
                {/* Input Schema (parameters) */}
                <div className="mb-4 flex-shrink-0 min-w-0">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('inspector.inputSchema')}</h3>
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700 text-xs font-mono overflow-x-auto whitespace-pre">
                    <JsonHighlight data={selectedTool.inputSchema || { type: 'object', properties: {}, required: [] }} fallback="{}" />
                  </div>
                </div>
                {/* Parameter inputs + Run button */}
                <div className="mb-4 flex-shrink-0">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('inspector.parametersRun')}</h3>
                  <ToolForm
                    key={selectedTool.name}
                    tool={selectedTool}
                    onRun={(args) => handleRunTool(selectedTool.name, args)}
                    running={runningTool === selectedTool.name}
                    t={t}
                  />
                </div>
                {/* Result: below form, only when we have result for this tool */}
                {result && result.tool === selectedTool.name && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600 flex-shrink-0">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('inspector.status')}</h3>
                    <span
                      className={`inline-block px-2 py-1 rounded text-sm font-medium ${
                        result.isError
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                          : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                      }`}
                    >
                      {result.isError ? t('inspector.failed') : t('inspector.success')}
                    </span>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-3 mb-2">{t('inspector.result')}</h3>
                    <pre
                      className={`p-3 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre-wrap ${
                        result.isError
                          ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                      }`}
                    >
                      {result.result}
                    </pre>
                  </div>
                )}
              </>
            )}
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
