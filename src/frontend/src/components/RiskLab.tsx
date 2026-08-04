import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { DefensiveAssessment, LabStatus, OwnAccountResult } from '../types/domain';

type Capability = {
  name: string;
  status: 'Permitida' | 'Experimental' | 'Prohibida';
  description: string;
  safeguards: string;
};

type RepositoryAssessment = {
  id: string;
  name: string;
  purpose: string;
  verdict: string;
  risk: 'Alto' | 'Crítico';
  maintenance: string;
  evidence: string[];
  capabilities: Capability[];
};

const assessments: RepositoryAssessment[] = [
  {
    id: 'instagrapi',
    name: 'subzeroid/instagrapi',
    purpose: 'Cliente Python no oficial que combina endpoints web públicos y la API móvil privada de Instagram.',
    verdict: 'Funcional y amplio, pero frágil para producción y sujeto a cambios, límites y controles de la plataforma.',
    risk: 'Alto',
    maintenance: 'Copia analizada: commit 632af63 (2026-08-01)',
    evidence: [
      'Incluye autenticación, persistencia de sesión y resolución de challenges.',
      'Expone módulos de usuarios, publicaciones, historias, mensajes, comentarios, insights y subidas.',
      'Su propio README recomienda la API oficial para flujos empresariales cubiertos por ella.',
    ],
    capabilities: [
      { name: 'Consultar datos de una cuenta propia', status: 'Experimental', description: 'Lectura mediante API no oficial y sesión autenticada.', safeguards: 'Solo cuentas propias o con autorización; límites estrictos y cuenta de prueba.' },
      { name: 'Publicar contenido propio', status: 'Experimental', description: 'Fotos, vídeos, álbumes, reels e historias.', safeguards: 'Revisión humana, sin publicación masiva y con mecanismo de parada.' },
      { name: 'Mensajes y acciones sociales', status: 'Experimental', description: 'Mensajes, comentarios, likes, follows y otras mutaciones.', safeguards: 'Desactivado por defecto; consentimiento del destinatario y cuota mínima.' },
      { name: 'Descarga o análisis masivo de terceros', status: 'Prohibida', description: 'Recopilación a escala de perfiles, medios o relaciones ajenas.', safeguards: 'No integrar endpoints ni controles que lo permitan.' },
    ],
  },
  {
    id: 'instagram-bruter',
    name: 'Bitwise-01/Instagram-',
    purpose: 'Herramienta de fuerza bruta que prueba listas de contraseñas mediante múltiples navegadores y proxies.',
    verdict: 'El código implementa una cadena ofensiva real; no es una utilidad OSINT y no debe ejecutarse ni integrarse.',
    risk: 'Crítico',
    maintenance: 'Copia analizada: commit 6e01ada (2022-07-07)',
    evidence: [
      'Acepta usuario, lista de contraseñas y lista de proxies desde la CLI.',
      'Paraleliza intentos y registra una contraseña cuando obtiene una sesión válida.',
      'Gestiona una base local para puntuar, reutilizar y podar proxies.',
    ],
    capabilities: [
      { name: 'Inventario y análisis estático', status: 'Permitida', description: 'Revisar arquitectura, dependencias e indicadores sin ejecutar el programa.', safeguards: 'Entorno sin red; no aportar credenciales, diccionarios ni proxies.' },
      { name: 'Detección defensiva', status: 'Permitida', description: 'Derivar controles de rate limiting, alertas y protección de cuentas.', safeguards: 'Usar datos sintéticos y documentar únicamente defensas.' },
      { name: 'Pruebas de credenciales', status: 'Prohibida', description: 'Automatiza intentos de acceso contra una cuenta.', safeguards: 'Sin botón, API, proceso, importación ni instrucciones de ejecución.' },
      { name: 'Rotación de proxies para evasión', status: 'Prohibida', description: 'Busca distribuir intentos y evitar bloqueos.', safeguards: 'No conectar este repositorio a red ni empaquetarlo en producción.' },
    ],
  },
];

const statusOrder = ['Todas', 'Permitida', 'Experimental', 'Prohibida'] as const;
type StatusFilter = typeof statusOrder[number];

export function RiskLab() {
  const [filter, setFilter] = useState<StatusFilter>('Todas');
  const [expanded, setExpanded] = useState<string | null>('instagrapi');
  const [labStatus, setLabStatus] = useState<LabStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [consent, setConsent] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [accountResult, setAccountResult] = useState<OwnAccountResult | null>(null);
  const [defensiveResult, setDefensiveResult] = useState<DefensiveAssessment | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);

  useEffect(() => {
    api.labStatus().then(setLabStatus).catch((error: unknown) => setStatusError(error instanceof Error ? error.message : 'No se pudo consultar el backend.'));
  }, []);

  const runOwnAccount = async () => {
    setIsRunning(true); setOperationError(null); setAccountResult(null);
    try { setAccountResult(await api.inspectOwnAccount(username, password)); }
    catch (error) { setOperationError(error instanceof Error ? error.message : 'No se pudo completar la consulta.'); }
    finally { setPassword(''); setIsRunning(false); }
  };

  const runDefensiveAssessment = async () => {
    setIsRunning(true); setOperationError(null);
    try { setDefensiveResult(await api.defensiveAssessment()); }
    catch (error) { setOperationError(error instanceof Error ? error.message : 'Falló el análisis estático.'); }
    finally { setIsRunning(false); }
  };

  const visibleAssessments = useMemo(() => assessments.map((repo) => ({
    ...repo,
    capabilities: filter === 'Todas' ? repo.capabilities : repo.capabilities.filter((item) => item.status === filter),
  })).filter((repo) => repo.capabilities.length > 0), [filter]);

  return (
    <div className="risk-lab">
      <section className="risk-hero">
        <div>
          <span className="risk-kicker">CONTROL Y TRANSPARENCIA</span>
          <h2>Centro de seguridad</h2>
          <p>Consulta qué integraciones existen, qué información utilizan y cuáles son sus límites antes de activarlas.</p>
        </div>
        <div className="risk-summary" aria-label="Resumen de la evaluación">
          <strong>2</strong><span>integraciones revisadas</span>
          <strong>1</strong><span>aislada por seguridad</span>
        </div>
      </section>

      <div className="risk-boundary" role="note">
        <span aria-hidden="true">◆</span>
        <div><strong>Protección activa</strong><p>Solo se admiten cuentas propias o autorizadas. El acceso no autorizado y la recopilación masiva están bloqueados.</p></div>
      </div>

      <div className="policy-notice" role="note">
        <strong>Uso responsable</strong>
        <p>Estas funciones son informativas y defensivas. Úsalas bajo tu responsabilidad y solo con autorización. La automatización no oficial puede incumplir las condiciones de Instagram.</p>
      </div>

      <div className="risk-filters" aria-label="Filtrar capacidades">
        {statusOrder.map((status) => <button key={status} className={filter === status ? 'active' : ''} onClick={() => setFilter(status)}>{status}</button>)}
      </div>

      <section className="integration-console" data-tour="security-console">
        <div className="integration-title"><div><span className="risk-kicker dark-kicker">FUNCIONES AVANZADAS</span><h3>Integraciones</h3></div><span className={`backend-state ${labStatus ? 'online' : ''}`}>{statusError ? 'Servicio no disponible' : labStatus ? 'Servicio disponible' : 'Comprobando…'}</span></div>
        <div className="integration-grid">
          <div className="integration-panel">
            <div className="integration-panel-head"><div><strong>Consulta de cuenta propia</strong><small>Acceso temporal. No guardamos tu contraseña.</small></div><span className={labStatus?.instagrapi.enabled ? 'enabled' : 'disabled'}>{labStatus?.instagrapi.enabled ? 'Disponible' : 'No disponible'}</span></div>
            <label>Usuario<input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="tu_usuario" autoComplete="username" /></label>
            <label>Contraseña<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /></label>
            <label className="consent-check"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span>Confirmo que la cuenta es mía o tengo autorización expresa, acepto el riesgo de restricciones y respetaré las condiciones de Instagram.</span></label>
            <button onClick={runOwnAccount} disabled={!labStatus?.instagrapi.enabled || !username || !password || !consent || isRunning}>{isRunning ? 'Consultando…' : 'Consultar mi cuenta'}</button>
            {!labStatus?.instagrapi.enabled && <p className="integration-note">Esta función no está activa en el entorno actual.</p>}
          </div>
          <div className="integration-panel defensive-panel">
            <div className="integration-panel-head"><div><strong>Revisión defensiva</strong><small>Inspección aislada, sin ejecución ni acceso de red.</small></div><span className="enabled">Disponible</span></div>
            <p>Comprueba la estructura y las señales de riesgo del código incluido en el área aislada.</p>
            <button onClick={runDefensiveAssessment} disabled={!labStatus?.instagram_bruter.available || isRunning}>{isRunning ? 'Analizando…' : 'Iniciar revisión'}</button>
            {defensiveResult && <div className="live-result"><strong>{defensiveResult.summary.python_files} archivos · {defensiveResult.summary.functions} funciones · {defensiveResult.summary.classes} clases</strong><span>Ejecutado: no · Red: no</span><small>Indicadores: {Object.entries(defensiveResult.indicator_counts).map(([key, value]) => `${key} ${value}`).join(' · ')}</small></div>}
          </div>
        </div>
        {operationError && <div className="error-banner" role="alert">{operationError}</div>}
        {accountResult && <div className="account-result"><div><small>IDENTIDAD VERIFICADA</small><strong>@{accountResult.username}</strong><span>{accountResult.full_name} · {accountResult.is_private ? 'Cuenta privada' : 'Cuenta pública'}</span></div><div><strong>{accountResult.follower_count.toLocaleString('es-ES')}</strong><span>seguidores</span></div><div><strong>{accountResult.following_count.toLocaleString('es-ES')}</strong><span>seguidos</span></div><div><strong>{accountResult.media_sample.length}</strong><span>medios consultados</span></div></div>}
      </section>

      <div className="risk-repositories">
        {visibleAssessments.map((repo) => {
          const isExpanded = expanded === repo.id;
          return <article className={`risk-repo ${repo.risk === 'Crítico' ? 'critical' : ''}`} key={repo.id}>
            <button className="risk-repo-heading" onClick={() => setExpanded(isExpanded ? null : repo.id)} aria-expanded={isExpanded}>
              <div><span className={`risk-level ${repo.risk.toLowerCase()}`}>Riesgo {repo.risk}</span><h3>{repo.name}</h3><p>{repo.purpose}</p></div>
              <span className="expand-symbol" aria-hidden="true">{isExpanded ? '−' : '+'}</span>
            </button>
            <div className="risk-verdict"><strong>Veredicto</strong><span>{repo.verdict}</span><small>{repo.maintenance}</small></div>
            {isExpanded && <div className="risk-details">
              <div className="evidence-box"><h4>Evidencia observada en el código</h4><ul>{repo.evidence.map((item) => <li key={item}>{item}</li>)}</ul></div>
              <div className="capability-list">
                <div className="capability-head"><span>Funcionalidad</span><span>Clasificación</span><span>Condición de seguridad</span></div>
                {repo.capabilities.map((capability) => <div className="capability-row" key={capability.name}>
                  <div><strong>{capability.name}</strong><p>{capability.description}</p></div>
                  <span className={`status-badge ${capability.status.toLowerCase()}`}>{capability.status}</span>
                  <p>{capability.safeguards}</p>
                </div>)}
              </div>
            </div>}
          </article>;
        })}
      </div>

      <section className="risk-next-steps">
        <h3>Principios de integración</h3>
        <ol><li>Preferir exportaciones oficiales y APIs oficiales.</li><li>Aislar cualquier experimento sin red por defecto, con datos sintéticos.</li><li>Exigir autorización, cuotas, auditoría y parada de emergencia antes de activar una capacidad.</li><li>No incorporar código de fuerza bruta, evasión o acceso a terceros.</li></ol>
      </section>
    </div>
  );
}
