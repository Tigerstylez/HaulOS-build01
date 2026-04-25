import { API_BASE_URL } from '../config';

async function parseJsonSafe(response: Response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  const body = await parseJsonSafe(response);

  if (!response.ok) {
    throw new Error(typeof body === 'object' && body && 'detail' in body ? String((body as any).detail) : `GET ${path} failed`);
  }

  return body as T;
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const body = await parseJsonSafe(response);

  if (!response.ok) {
    throw new Error(typeof body === 'object' && body && 'detail' in body ? String((body as any).detail) : `POST ${path} failed`);
  }

  return body as T;
}
