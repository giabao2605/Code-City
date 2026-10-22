import { useEffect, useRef, useState } from 'react';
import { makePing, parseEnvelope } from './protocol';
import type { QtBridge } from './qt';
import './style.css';

export default function App() {
  const [bridge, setBridge] = useState<QtBridge | null>(null);
  const [status, setStatus] = useState('waiting for Qt WebChannel');
  const [lastId, setLastId] = useState('-');
  const [pong, setPong] = useState('-');
  const [error, setError] = useState('');
  const [successes, setSuccesses] = useState(0);
  const [failures, setFailures] = useState(0);
  const [events, setEvents] = useState<string[]>([]);
  const count = useRef(0);

  useEffect(() => {
    const timeout = window.setTimeout(() => setStatus((s) => s.startsWith('connected')
      ? s : 'ERROR: Qt bridge initialization timed out'), 10000);
    const transport = window.qt?.webChannelTransport;
    const constructor = window.QWebChannel;
    if (!transport || !constructor) {
      setStatus('ERROR: Qt WebEngine transport or qwebchannel.js unavailable');
      window.clearTimeout(timeout);
      return;
    }
    new constructor(transport, (channel) => {
      const api = channel.objects.spike;
      if (!api) {
        setStatus('ERROR: Qt QObject missing');
        window.clearTimeout(timeout);
        return;
      }
      window.__ccBridge = api;
      api.pushed.connect((raw) => {
        const event = parseEnvelope(raw);
        if (!event) {
          setError('Invalid Python event envelope');
          return;
        }
        setEvents((list) => [`${event.event}: ${JSON.stringify(event.payload)}`, ...list].slice(0, 8));
      });
      setBridge(api);
      setStatus('connected to Qt WebChannel');
      window.clearTimeout(timeout);
      api.clientReady();
    });
    return () => {
      window.clearTimeout(timeout);
      delete window.__ccBridge;
    };
  }, []);

  const sendPing = () => {
    if (!bridge) return;
    const requestId = `ping-${Date.now()}-${++count.current}`;
    const message = 'hello from React';
    setLastId(requestId);
    setError('');
    try {
      bridge.request(makePing(requestId, message), (raw) => {
        const response = parseEnvelope(raw);
        if (response?.event !== 'diagnostics.pong' || response.requestId !== requestId ||
            response.payload.status !== 'ok' || response.payload.message !== message) {
          setFailures((n) => n + 1);
          setError(response?.event === 'diagnostics.error'
            ? String(response.payload.code ?? 'UNKNOWN_ERROR') : 'Invalid/mismatched Pong');
          return;
        }
        setPong(`${response.payload.message} [${requestId}]`);
        setSuccesses((n) => n + 1);
      });
    } catch (err) {
      setFailures((n) => n + 1);
      setError(String(err));
    }
  };

  return <main>
    <h1>Code City: CC-002 integration</h1>
    <p>React / TypeScript static assets inside Qt WebEngine. No dev server.</p>
    <section>
      <strong>Frontend:</strong> <span data-testid="frontend">mounted</span><br />
      <strong>Bridge:</strong> <span data-testid="bridge">{status}</span>
    </section>
    <section>
      <button data-testid="ping" onClick={sendPing} disabled={!bridge}>Send Ping</button>
      <p>Request ID: <span data-testid="request-id">{lastId}</span></p>
      <p>Pong: <span data-testid="pong">{pong}</span></p>
      <p>Successes: <span data-testid="successes">{successes}</span>;
         failures: <span data-testid="failures">{failures}</span></p>
      <p role="alert" data-testid="error">{error}</p>
    </section>
    <section>
      <h2>Unsolicited Python events</h2>
      <ul data-testid="events">{events.map((event, n) => <li key={n}>{event}</li>)}</ul>
    </section>
  </main>;
}
