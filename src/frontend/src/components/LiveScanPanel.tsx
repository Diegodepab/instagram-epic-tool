import { useState } from 'react';
import { api } from '../services/api';
import type { ImportResponse, LiveProfileItem, LiveScanResult } from '../types/domain';

interface LiveScanPanelProps {
  currentSessionId: string | null;
  onAnalysisReady: (result: ImportResponse) => void;
}

type ScanPhase = 'idle' | 'connecting' | 'fetching_followers' | 'fetching_following' | 'processing_pics' | 'done';

const phaseLabels: Record<ScanPhase, string> = {
  idle: '',
  connecting: 'Conectando con Instagram…',
  fetching_followers: 'Descargando seguidores…',
  fetching_following: 'Descargando seguidos…',
  processing_pics: 'Procesando fotos de perfil…',
  done: 'Listo',
};

function ProfileAvatar({ item }: { item: LiveProfileItem }) {
  return (
    <div className={`avatar-circle ${item.is_private ? 'private' : 'public'}`}>
      {item.profile_pic_b64
        ? <img src={item.profile_pic_b64} alt={item.username} loading="lazy" />
        : <span>{item.username[0]?.toUpperCase() ?? '?'}</span>}
    </div>
  );
}

function ProfileRow({ item, index }: { item: LiveProfileItem; index: number }) {
  return (
    <div className="profile-list-item" style={{ animationDelay: `${Math.min(index * 30, 600)}ms` }}>
      <ProfileAvatar item={item} />
      <div className="profile-list-info">
        <strong>@{item.username}</strong>
        {item.full_name && <small>{item.full_name}</small>}
      </div>
      <span className={`badge-visibility ${item.is_private ? 'badge-private' : 'badge-public'}`}>
        {item.is_private ? 'Privado' : 'Público'}
      </span>
    </div>
  );
}

export function LiveScanPanel({ currentSessionId, onAnalysisReady }: LiveScanPanelProps) {
  const [tempUser, setTempUser] = useState('');
  const [tempPass, setTempPass] = useState('');
  const [targetUser, setTargetUser] = useState('');
  const [consent, setConsent] = useState(false);
  const [phase, setPhase] = useState<ScanPhase>('idle');
  const [scanResult, setScanResult] = useState<LiveScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCommitting, setIsCommitting] = useState(false);
  const [commitMessage, setCommitMessage] = useState<string | null>(null);
  const [listTab, setListTab] = useState<'followers' | 'following'>('followers');

  const isScanning = phase !== 'idle' && phase !== 'done';

  const startScan = async () => {
    if (!tempUser.trim() || !tempPass || !targetUser.trim() || !consent) {
      setError('Completa todos los campos y confirma la autorización.');
      return;
    }
    setError(null);
    setScanResult(null);
    setCommitMessage(null);
    setPhase('connecting');

    // Simulate phases for UX since the backend call is a single long request
    const phaseTimer = setTimeout(() => setPhase('fetching_followers'), 4000);
    const phaseTimer2 = setTimeout(() => setPhase('fetching_following'), 12000);
    const phaseTimer3 = setTimeout(() => setPhase('processing_pics'), 20000);

    try {
      const result = await api.liveScan(
        tempUser.trim().replace(/^@/, ''),
        tempPass,
        targetUser.trim().replace(/^@/, ''),
        consent,
      );
      setScanResult(result);
      setPhase('done');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo completar la exploración.');
      setPhase('idle');
    } finally {
      clearTimeout(phaseTimer);
      clearTimeout(phaseTimer2);
      clearTimeout(phaseTimer3);
      setTempPass(''); // Never keep password in state after request
    }
  };

  const commitScan = async (mergeIntoExisting: boolean) => {
    if (!scanResult) return;
    setIsCommitting(true);
    setError(null);
    try {
      const result = await api.commitScan(
        scanResult.scan_id,
        mergeIntoExisting ? (currentSessionId ?? undefined) : undefined,
      );
      onAnalysisReady(result);
      setCommitMessage(`Red de @${scanResult.preview.username} cargada en el mapa.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron guardar los datos.');
    } finally {
      setIsCommitting(false);
    }
  };

  const discardScan = () => {
    setScanResult(null);
    setPhase('idle');
    setCommitMessage(null);
    setError(null);
  };

  const resetAll = () => {
    discardScan();
    setTempUser('');
    setTempPass('');
    setTargetUser('');
    setConsent(false);
  };

  const preview = scanResult?.preview;

  return (
    <div className="live-scan-panel">
      <section className="scan-hero">
        <div>
          <span className="risk-kicker">EXPLORACIÓN EN VIVO</span>
          <h2>Panel de exploración</h2>
          <p>Escanea cuentas autorizadas para construir el grafo de conexiones sin archivos ZIP.</p>
        </div>
      </section>

      <div className="scan-security-banner" role="note">
        <span aria-hidden="true">⌁</span>
        <div>
          <strong>Privado por diseño</strong>
          <p>Las credenciales se usan una sola vez y se destruyen tras la consulta. Los datos se procesan en memoria y se borran al cerrar la sesión. Solo se recopila información pública.</p>
        </div>
      </div>

      {/* Step 1: Connection form */}
      {!preview && (
        <section className="scan-step scan-connect">
          <div className="scan-step-header">
            <span className="scan-step-number">1</span>
            <div>
              <h3>Conexión</h3>
              <p>Introduce las credenciales de la cuenta temporal y la cuenta a explorar.</p>
            </div>
          </div>

          <div className="scan-form-grid">
            <div className="scan-form-group">
              <label className="scan-label">
                <span className="scan-label-text">Cuenta temporal</span>
                <small>Usuario de la cuenta "quemable" para la sesión</small>
              </label>
              <div className="scan-input-row">
                <label className="scan-field">
                  <span>@</span>
                  <input
                    value={tempUser}
                    onChange={(e) => setTempUser(e.target.value)}
                    placeholder="cuenta_temporal"
                    autoComplete="username"
                    disabled={isScanning}
                  />
                </label>
                <label className="scan-field password-field">
                  <span>🔒</span>
                  <input
                    type="password"
                    value={tempPass}
                    onChange={(e) => setTempPass(e.target.value)}
                    placeholder="Contraseña"
                    autoComplete="current-password"
                    disabled={isScanning}
                  />
                </label>
              </div>
            </div>

            <div className="scan-form-group">
              <label className="scan-label">
                <span className="scan-label-text">Cuenta objetivo</span>
                <small>La cuenta cuyas conexiones quieres mapear</small>
              </label>
              <label className="scan-field">
                <span>@</span>
                <input
                  value={targetUser}
                  onChange={(e) => setTargetUser(e.target.value)}
                  placeholder="perfil_a_explorar"
                  autoComplete="off"
                  disabled={isScanning}
                />
              </label>
            </div>
          </div>

          <label className="scan-consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              disabled={isScanning}
            />
            <span>Confirmo que tengo autorización expresa del propietario de la cuenta objetivo, acepto los riesgos y respetaré los términos de Instagram.</span>
          </label>

          <button
            className="primary-button scan-button"
            onClick={startScan}
            disabled={isScanning || !consent || !tempUser.trim() || !tempPass || !targetUser.trim()}
          >
            {isScanning
              ? <><i className="spinner" /> {phaseLabels[phase]}</>
              : 'Escanear cuenta'}
          </button>

          {isScanning && (
            <div className="scan-progress">
              <div className="scan-progress-bar">
                <span
                  className="scan-progress-fill"
                  style={{
                    width: phase === 'connecting' ? '15%'
                      : phase === 'fetching_followers' ? '40%'
                      : phase === 'fetching_following' ? '70%'
                      : phase === 'processing_pics' ? '90%'
                      : '100%',
                  }}
                />
              </div>
              <span className="scan-progress-label">{phaseLabels[phase]}</span>
            </div>
          )}
        </section>
      )}

      {/* Error display */}
      {error && <div className="error-banner" role="alert">{error}</div>}
      {commitMessage && <div className="scan-success-banner" role="status">{commitMessage}</div>}

      {/* Step 2: Preview */}
      {preview && !commitMessage && (
        <section className="scan-step scan-preview">
          <div className="scan-step-header">
            <span className="scan-step-number">2</span>
            <div>
              <h3>Previsualización</h3>
              <p>Revisa los datos antes de guardarlos. Nada se ha guardado todavía.</p>
            </div>
          </div>

          <div className="profile-preview-card">
            <div className="preview-card-avatar">
              {preview.profile_pic_b64
                ? <img src={preview.profile_pic_b64} alt={preview.username} />
                : <div className="avatar-placeholder">{preview.username[0]?.toUpperCase()}</div>}
            </div>
            <div className="preview-card-info">
              <strong>@{preview.username}</strong>
              {preview.full_name && <span>{preview.full_name}</span>}
              <span className={`badge-visibility ${preview.is_private ? 'badge-private' : 'badge-public'}`}>
                {preview.is_private ? 'Cuenta privada' : 'Cuenta pública'}
              </span>
            </div>
            <div className="preview-card-stats">
              <div><strong>{preview.follower_count.toLocaleString('es-ES')}</strong><span>seguidores</span></div>
              <div><strong>{preview.following_count.toLocaleString('es-ES')}</strong><span>seguidos</span></div>
              <div><strong>{preview.followers.length + preview.following.length}</strong><span>relaciones obtenidas</span></div>
            </div>
          </div>

          {scanResult?.warnings.map((w) => (
            <div className="data-warning" role="status" key={w}><strong>Aviso</strong><span>{w}</span></div>
          ))}

          <div className="profile-list-tabs">
            <button
              className={listTab === 'followers' ? 'active' : ''}
              onClick={() => setListTab('followers')}
            >
              Seguidores ({preview.followers.length}{preview.followers_complete ? '' : '+'})
            </button>
            <button
              className={listTab === 'following' ? 'active' : ''}
              onClick={() => setListTab('following')}
            >
              Seguidos ({preview.following.length}{preview.following_complete ? '' : '+'})
            </button>
          </div>

          <div className="profile-list">
            {(listTab === 'followers' ? preview.followers : preview.following).map((item, i) => (
              <ProfileRow key={item.username} item={item} index={i} />
            ))}
            {(listTab === 'followers' ? preview.followers : preview.following).length === 0 && (
              <p className="profile-list-empty">No se encontraron perfiles en esta categoría.</p>
            )}
          </div>

          <div className="commit-actions">
            <button className="discard-button" onClick={discardScan} disabled={isCommitting}>
              Descartar
            </button>
            {currentSessionId && (
              <button className="secondary-button" onClick={() => commitScan(true)} disabled={isCommitting}>
                {isCommitting ? <><i className="spinner" /> Fusionando…</> : 'Añadir al mapa actual'}
              </button>
            )}
            <button className="primary-button" onClick={() => commitScan(false)} disabled={isCommitting}>
              {isCommitting ? <><i className="spinner" /> Guardando…</> : 'Guardar y analizar'}
            </button>
          </div>
        </section>
      )}

      {/* Post-commit: offer to scan another or go to graph */}
      {commitMessage && (
        <section className="scan-step scan-complete">
          <div className="scan-step-header">
            <span className="scan-step-number">✓</span>
            <div>
              <h3>Exploración completada</h3>
              <p>Los datos se han cargado en el mapa de relaciones.</p>
            </div>
          </div>
          <div className="commit-actions">
            <button className="secondary-button" onClick={resetAll}>Escanear otra cuenta</button>
          </div>
        </section>
      )}
    </div>
  );
}
