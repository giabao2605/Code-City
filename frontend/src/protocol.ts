/** CC-002-only diagnostic IPC contract, not a new product V1 command. */
export const SCHEMA_VERSION = 1;
export const MAX_REQUEST_BYTES = 4096;
export const MAX_MESSAGE_BYTES = 128;

export type Envelope = {
  schemaVersion: 1;
  requestId?: string | null;
  event: string;
  payload: Record<string, unknown>;
};

export function parseEnvelope(raw: string): Envelope | null {
  try {
    const o: unknown = JSON.parse(raw);
    if (typeof o !== 'object' || o === null || Array.isArray(o)) return null;
    const value = o as Record<string, unknown>;
    if (value.schemaVersion !== SCHEMA_VERSION ||
        typeof value.event !== 'string' ||
        typeof value.payload !== 'object' || value.payload === null ||
        Array.isArray(value.payload) ||
        (value.requestId !== undefined && value.requestId !== null &&
         typeof value.requestId !== 'string')) return null;
    return value as Envelope;
  } catch {
    return null;
  }
}

export function makePing(requestId: string, message: string): string {
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(requestId) ||
      new TextEncoder().encode(message).length > MAX_MESSAGE_BYTES) {
    throw new Error('Invalid diagnostic input');
  }
  const raw = JSON.stringify({
    schemaVersion: SCHEMA_VERSION,
    requestId,
    command: 'diagnostics.ping',
    payload: { message },
  });
  if (new TextEncoder().encode(raw).length > MAX_REQUEST_BYTES) {
    throw new Error('Diagnostic request exceeds 4 KiB');
  }
  return raw;
}
