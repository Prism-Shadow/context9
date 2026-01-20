/**
 * MCP (Model Context Protocol) Streamable HTTP client.
 * Connects to a streamable HTTP MCP server via POST with JSON-RPC.
 * All requests go through the backend /api/mcp-proxy to avoid CORS and ensure
 * headers (e.g. Authorization) are correctly received by the MCP server.
 * @see https://modelcontextprotocol.io/specification
 */

import { API_BASE_URL, TOKEN_KEY } from '../utils/constants';

export interface McpHeader {
  key: string;
  value: string;
}

export interface McpTool {
  name: string;
  description?: string;
  inputSchema: {
    type: 'object';
    properties?: Record<string, { type?: string; description?: string; [k: string]: unknown }>;
    required?: string[];
  };
  /** Optional JSON Schema for structured tool output (MCP 2025-06-18+). */
  outputSchema?: unknown;
  [k: string]: unknown;
}

export interface ListToolsResult {
  tools: McpTool[];
}

export interface CallToolResult {
  content?: Array<{ type: string; text?: string; [k: string]: unknown }>;
  isError?: boolean;
  [k: string]: unknown;
}

let _requestId = 0;
function nextId(): string {
  return `mcp-${++_requestId}-${Date.now()}`;
}

function buildHeaders(userHeaders: McpHeader[]): Record<string, string> {
  const out: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
  };
  for (const h of userHeaders) {
    const k = (h.key || '').trim();
    if (k) out[k] = h.value || '';
  }
  return out;
}

const PROXY_URL = `${API_BASE_URL}/api/mcp-proxy`;

/**
 * Send a JSON-RPC message to the MCP endpoint via the backend proxy to avoid CORS.
 * For requests (with id), returns parsed JSON.
 * For notifications (no id), 202 or 200 with empty body is success.
 * When the server returns Mcp-Session-Id in the response, it is returned as sessionId; pass it back in sessionId for all subsequent requests.
 */
export async function mcpRequest(
  baseUrl: string,
  userHeaders: McpHeader[],
  message: { jsonrpc: string; id?: string; method: string; params?: unknown },
  sessionId?: string | null
): Promise<{ result?: unknown; error?: { code?: number; message?: string }; ok?: boolean; sessionId?: string }> {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
  const proxyHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) proxyHeaders['Authorization'] = `Bearer ${token}`;

  const mcpHeaders = { ...buildHeaders(userHeaders), ...(sessionId ? { 'mcp-session-id': sessionId } : {}) };

  const res = await fetch(PROXY_URL, {
    method: 'POST',
    headers: proxyHeaders,
    body: JSON.stringify({
      target_url: baseUrl,
      headers: mcpHeaders,
      body: message,
    }),
  });

  const newSessionId = res.headers.get('mcp-session-id') || undefined;

  if (res.status === 202) return { ok: true, sessionId: newSessionId };
  if (!res.ok) {
    const text = await res.text();
    let err: { message?: string; data?: unknown } = { message: `HTTP ${res.status}: ${text}` };
    try {
      const j = JSON.parse(text);
      if (j.detail) err = { message: typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail) };
      else if (j.error) err = { message: j.error.message || String(j.error), data: j.error };
    } catch {
      // ignore
    }
    throw new Error(err.message || `MCP request failed: ${res.status}`);
  }

  const text = await res.text();
  if (!text) return { ok: true, sessionId: newSessionId };

  const contentType = res.headers.get('Content-Type') || '';
  if (contentType.includes('text/event-stream')) {
    const parsed = parseSSEAndFindResponse(text, message.id);
    if (parsed) return { ...parsed, sessionId: newSessionId };
    if (!message.id) return { ok: true, sessionId: newSessionId };
    throw new Error('No JSON-RPC response found in SSE stream');
  }

  const data = JSON.parse(text);
  if (data.error) return { error: data.error, sessionId: newSessionId };
  return { result: data.result, sessionId: newSessionId };
}

/**
 * Parse SSE (Server-Sent Events) and find the JSON-RPC response with matching id.
 * SSE format: "event: xxx\ndata: {...}\n\n" (data may be multi-line; one JSON per data: line).
 */
function parseSSEAndFindResponse(
  raw: string,
  requestId: string | undefined
): { result?: unknown; error?: { code?: number; message?: string }; ok?: boolean } | null {
  const blocks = raw.split(/\n\n+/);
  for (const block of blocks) {
    const lines = block.split(/\n/);
    for (const line of lines) {
      if (line.startsWith('data:')) {
        const jsonStr = line.slice(5).trim();
        if (!jsonStr) continue;
        try {
          const obj = JSON.parse(jsonStr) as { id?: string; result?: unknown; error?: { code?: number; message?: string } };
          if (typeof obj !== 'object' || obj === null) continue;
          // For a request we need the response with matching id; for notification we expect no response
          if (requestId == null) continue;
          if (obj.id !== requestId) continue;
          if ('error' in obj && obj.error != null) return { error: obj.error };
          if ('result' in obj) return { result: obj.result };
        } catch {
          // not JSON, skip
        }
      }
    }
  }
  return null;
}

/**
 * Initialize the MCP session. Must be called first.
 * Returns init result plus sessionId when the server uses sessions; pass sessionId to all later calls.
 */
export async function mcpInitialize(
  baseUrl: string,
  userHeaders: McpHeader[]
): Promise<{ protocolVersion?: string; capabilities?: unknown; serverInfo?: unknown; sessionId?: string }> {
  const { result, error, sessionId } = await mcpRequest(
    baseUrl,
    userHeaders,
    {
      jsonrpc: '2.0',
      id: nextId(),
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        clientInfo: { name: 'context9-inspector', version: '1.0.0' },
      },
    },
    undefined
  );
  if (error) throw new Error(error.message || 'Initialize failed');
  return { ...(result as object || {}), sessionId };
}

/**
 * Send notifications/initialized after initialize. No response expected.
 */
export async function mcpSendInitialized(
  baseUrl: string,
  userHeaders: McpHeader[],
  sessionId?: string | null
): Promise<void> {
  await mcpRequest(
    baseUrl,
    userHeaders,
    { jsonrpc: '2.0', method: 'notifications/initialized' },
    sessionId
  );
}

/**
 * List tools from the MCP server.
 */
export async function mcpListTools(
  baseUrl: string,
  userHeaders: McpHeader[],
  sessionId?: string | null
): Promise<ListToolsResult> {
  const { result, error } = await mcpRequest(
    baseUrl,
    userHeaders,
    { jsonrpc: '2.0', id: nextId(), method: 'tools/list' },
    sessionId
  );
  if (error) throw new Error(error.message || 'tools/list failed');
  const list = (result || {}) as { tools?: McpTool[] };
  return { tools: list.tools || [] };
}

/**
 * Call a tool by name with arguments.
 */
export async function mcpCallTool(
  baseUrl: string,
  userHeaders: McpHeader[],
  name: string,
  args: Record<string, unknown>,
  sessionId?: string | null
): Promise<CallToolResult> {
  const { result, error } = await mcpRequest(
    baseUrl,
    userHeaders,
    { jsonrpc: '2.0', id: nextId(), method: 'tools/call', params: { name, arguments: args } },
    sessionId
  );
  if (error) throw new Error(error.message || 'tools/call failed');
  return (result || {}) as CallToolResult;
}
