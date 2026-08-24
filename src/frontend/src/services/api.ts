import type { APIGraphPayload, DefensiveAssessment, ImportResponse, LabStatus, LiveCommitResponse, LiveScanResult, OwnAccountResult, RelationshipCategory, RelationshipPage } from '../types/domain';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

function uploadExport(
  path: string,
  file: File,
  username: string,
  onProgress: (percentage: number) => void,
  signal: AbortSignal,
  consent?: boolean,
): Promise<ImportResponse> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append('export', file);
    form.append('username', username);
    if (consent !== undefined) form.append('consent', String(consent));
    const request = new XMLHttpRequest();
    request.open('POST', `${API_BASE}${path}`);
    request.responseType = 'json';
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.min(100, Math.round((event.loaded / event.total) * 100)));
    };
    request.onload = () => request.status >= 200 && request.status < 300
      ? resolve(request.response as ImportResponse)
      : reject(new Error((request.response as { detail?: string } | null)?.detail ?? 'No se pudo analizar el archivo.'));
    request.onerror = () => reject(new Error('Se interrumpió la conexión durante la subida.'));
    request.onabort = () => reject(new DOMException('La importación fue cancelada.', 'AbortError'));
    const abort = () => request.abort();
    signal.addEventListener('abort', abort, { once: true });
    request.onloadend = () => signal.removeEventListener('abort', abort);
    request.send(form);
  });
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = 'No se pudo completar la solicitud.';
    try {
      const body = await response.json() as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // The friendly fallback is more useful than a JSON parsing error.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  async labStatus(): Promise<LabStatus> {
    return parseResponse(await fetch(`${API_BASE}/lab/status`));
  },

  async defensiveAssessment(): Promise<DefensiveAssessment> {
    return parseResponse(await fetch(`${API_BASE}/lab/instagram-bruter/static-assessment`));
  },

  async inspectOwnAccount(username: string, password: string): Promise<OwnAccountResult> {
    return parseResponse(await fetch(`${API_BASE}/lab/instagrapi/own-account`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, relationship_limit: 25, media_limit: 6, consent: true }),
    }));
  },

  async createDemo(): Promise<ImportResponse> {
    const response = await fetch(`${API_BASE}/analysis/demo`, { method: 'POST' });
    return parseResponse(response);
  },

  importExport(
    file: File,
    username: string,
    onProgress: (percentage: number) => void,
    signal: AbortSignal,
  ): Promise<ImportResponse> {
    return uploadExport('/analysis/imports', file, username, onProgress, signal);
  },

  mergeExport(sessionId: string, file: File, username: string, consent: boolean): Promise<ImportResponse> {
    return uploadExport(
      `/analysis/sessions/${encodeURIComponent(sessionId)}/imports`,
      file,
      username,
      () => undefined,
      new AbortController().signal,
      consent,
    );
  },

  async expandNode(sessionId: string, nodeId: string): Promise<APIGraphPayload> {
    const session = encodeURIComponent(sessionId);
    const node = encodeURIComponent(nodeId);
    const response = await fetch(`${API_BASE}/analysis/sessions/${session}/nodes/${node}`);
    return parseResponse(response);
  },

  async listRelationships(
    sessionId: string,
    category: RelationshipCategory,
    search: string,
    offset: number,
    limit = 50,
  ): Promise<RelationshipPage> {
    const params = new URLSearchParams({
      category,
      search,
      offset: String(offset),
      limit: String(limit),
    });
    const session = encodeURIComponent(sessionId);
    const response = await fetch(`${API_BASE}/analysis/sessions/${session}/relationships?${params}`);
    return parseResponse(response);
  },

  csvUrl(sessionId: string, category: RelationshipCategory): string {
    const session = encodeURIComponent(sessionId);
    return `${API_BASE}/analysis/sessions/${session}/relationships.csv?category=${category}`;
  },

  async deleteSession(sessionId: string): Promise<void> {
    await fetch(`${API_BASE}/analysis/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
  },

  async liveScan(
    tempUsername: string,
    tempPassword: string,
    targetUsername: string,
    consent: boolean,
  ): Promise<LiveScanResult> {
    return parseResponse(await fetch(`${API_BASE}/lab/live-scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        temp_username: tempUsername,
        temp_password: tempPassword,
        target_username: targetUsername,
        consent,
      }),
    }));
  },

  async commitScan(scanId: string, sessionId?: string): Promise<LiveCommitResponse> {
    return parseResponse(await fetch(`${API_BASE}/lab/live-scan/commit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scan_id: scanId,
        session_id: sessionId ?? null,
      }),
    }));
  },
};
