import { useCallback, useEffect, useRef, useState } from 'react';
import { GraphCanvas } from './components/GraphCanvas';
import type { GraphLayout } from './components/GraphCanvas';
import { RelationshipTable } from './components/RelationshipTable';
import { RiskLab } from './components/RiskLab';
import { ProductTour } from './components/ProductTour';
import { useGraphState } from './hooks/useGraphState';
import { useGraphFilters } from './hooks/useGraphFilters';
import type { GraphFilters } from './hooks/useGraphFilters';
import { api } from './services/api';
import type { GraphNode, ImportResponse } from './types/domain';
import './index.css';

function Logo() {
  return <div className="logo-mark" aria-hidden="true"><span /><span /><span /></div>;
}

export default function App() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const importControllerRef = useRef<AbortController | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [username, setUsername] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [importError, setImportError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ImportResponse | null>(null);
  const [showRiskCatalog, setShowRiskCatalog] = useState(false);
  const [isTourOpen, setIsTourOpen] = useState(false);
  const [isTutorialDemo, setIsTutorialDemo] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [search, setSearch] = useState('');
  const [view, setView] = useState<'graph' | 'list' | 'risks'>('graph');
  const [graphLayout, setGraphLayout] = useState<GraphLayout>('groups');
  const [mergeUsername, setMergeUsername] = useState('');
  const [mergeFile, setMergeFile] = useState<File | null>(null);
  const [mergeStatus, setMergeStatus] = useState<string | null>(null);
  const [mergeConsent, setMergeConsent] = useState(false);
  const [isMerging, setIsMerging] = useState(false);
  const [filters, setFilters] = useState<GraphFilters>({
    showMutuals: true,
    showFans: true,
    showNonFollowers: true,
    searchQuery: '',
    nodeLimit: 250,
  });
  const { graphData, isLoading, message, loadGraph, clearGraph, expandNode } = useGraphState();
  const filteredGraphData = useGraphFilters(graphData, filters);
  const closeTour = useCallback(() => setIsTourOpen(false), []);

  useEffect(() => {
    if (!localStorage.getItem('circlescope_guided_tour_v3_seen')) setIsTourOpen(true);
  }, []);

  const chooseFile = (nextFile?: File) => {
    if (!nextFile) return;
    if (!nextFile.name.toLowerCase().endsWith('.zip')) {
      setImportError('Selecciona el archivo .zip oficial y solicita el formato JSON en Instagram.');
      return;
    }
    if (nextFile.size > 1024 * 1024 * 1024) {
      setImportError('El ZIP supera el límite de 1 GB. Solicita a Instagram una exportación que incluya solo seguidores y seguidos.');
      return;
    }
    setFile(nextFile);
    setImportError(null);
  };

  const importFile = async () => {
    if (!file || !username.trim()) {
      setImportError('Indica tu usuario y selecciona el archivo ZIP para continuar.');
      return;
    }
    setIsImporting(true);
    setUploadProgress(0);
    setImportError(null);
    const controller = new AbortController();
    importControllerRef.current = controller;
    try {
      const result = await api.importExport(file, username.trim(), setUploadProgress, controller.signal);
      openAnalysis(result);
    } catch (error) {
      setImportError(error instanceof DOMException && error.name === 'AbortError'
        ? 'Importación cancelada. El archivo no se ha guardado.'
        : error instanceof Error ? error.message : 'No pudimos analizar el archivo.');
    } finally {
      setIsImporting(false);
      setUploadProgress(0);
      importControllerRef.current = null;
    }
  };

  const cancelImport = () => importControllerRef.current?.abort();

  const openAnalysis = (result: ImportResponse) => {
    setAnalysis(result);
    loadGraph(result.graph);
    setSelectedNode(result.graph.nodes.find((node) => node.id === result.summary.username) ?? null);
    setView('graph');
  };

  const openDemo = async () => {
    setIsImporting(true);
    setImportError(null);
    try {
      openAnalysis(await api.createDemo());
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'No pudimos abrir la demostración.');
    } finally {
      setIsImporting(false);
    }
  };

  const startOver = async () => {
    if (analysis) await api.deleteSession(analysis.session_id);
    setAnalysis(null);
    setSelectedNode(null);
    setFile(null);
    setSearch('');
    setFilters({ showMutuals: true, showFans: true, showNonFollowers: true, searchQuery: '', nodeLimit: 250 });
    clearGraph();
  };

  const openTutorialDemo = async () => {
    setIsTutorialDemo(true);
    try { await openDemo(); }
    catch (error) { setIsTutorialDemo(false); throw error; }
  };

  const cleanupTutorialDemo = async () => {
    if (isTutorialDemo && analysis) await startOver();
    else if (!analysis) setUsername('');
    setIsTutorialDemo(false);
  };

  const demonstrateGraphFilters = () => setFilters((current) => ({ ...current, showMutuals: true, showFans: false, showNonFollowers: false, searchQuery: '' }));
  const restoreGraphFilters = () => { setFilters((current) => ({ ...current, showMutuals: true, showFans: true, showNonFollowers: true, searchQuery: '' })); setSearch(''); };
  const demonstrateGraphSearch = () => { setFilters((current) => ({ ...current, searchQuery: 'amigo_001' })); setSearch('amigo_001'); };

  if (!analysis && showRiskCatalog) {
    return (
      <main className="welcome-shell risk-catalog-shell">
        <ProductTour open={isTourOpen} hasAnalysis={false} onClose={closeTour} onFillExample={() => setUsername('circlescope_demo')} onOpenDemo={openTutorialDemo} onSetView={setView} onDemoGraphFilters={demonstrateGraphFilters} onRestoreGraphFilters={restoreGraphFilters} onDemoGraphSearch={demonstrateGraphSearch} onCleanupDemo={cleanupTutorialDemo} />
        <header className="topbar">
          <div className="brand"><Logo /><span>CircleScope</span></div>
          <nav className="welcome-nav"><button className="help-link link-button" onClick={() => setIsTourOpen(true)}>Guía interactiva</button><button className="help-link link-button" onClick={() => setShowRiskCatalog(false)}>Volver</button></nav>
        </header>
        <section className="standalone-risk"><RiskLab /></section>
      </main>
    );
  }

  if (!analysis) {
    return (
      <main className="welcome-shell">
        <ProductTour open={isTourOpen} hasAnalysis={false} onClose={closeTour} onFillExample={() => setUsername('circlescope_demo')} onOpenDemo={openTutorialDemo} onSetView={setView} onDemoGraphFilters={demonstrateGraphFilters} onRestoreGraphFilters={restoreGraphFilters} onDemoGraphSearch={demonstrateGraphSearch} onCleanupDemo={cleanupTutorialDemo} />
        <header className="topbar">
          <div className="brand"><Logo /><span>CircleScope</span></div>
          <nav className="welcome-nav"><button className="help-link link-button tutorial-link" onClick={() => setIsTourOpen(true)}>Guía interactiva</button><button className="help-link link-button" onClick={() => setShowRiskCatalog(true)}>Seguridad</button><a href="#como-conseguir" className="help-link">Cómo funciona</a></nav>
        </header>

        <section className="welcome-content">
          <div className="eyebrow">ANÁLISIS PRIVADO DE TU COMUNIDAD</div>
          <h1 data-tour="welcome">Tu círculo, de un vistazo.<br /><span>Sin entregar tu contraseña.</span></h1>
          <p className="lead">Convierte tu exportación oficial de Instagram en un mapa claro de seguidores, conexiones y relaciones mutuas.</p>

          <div className="import-card">
            <div className="step-heading"><span>1</span><div><h2>Tu perfil</h2><p>Será el centro del mapa.</p></div></div>
            <label className="username-field" data-tour="username">
              <span>@</span>
              <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="tu_usuario" autoComplete="off" />
            </label>

            <div className="divider" />
            <div className="step-heading"><span>2</span><div><h2>Tu archivo de Instagram</h2><p>Selecciona la exportación ZIP en formato JSON.</p></div></div>
            <div
              data-tour="upload"
              className={`dropzone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
              onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(event) => { event.preventDefault(); setIsDragging(false); chooseFile(event.dataTransfer.files[0]); }}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => { if (event.key === 'Enter') inputRef.current?.click(); }}
            >
              <input ref={inputRef} type="file" accept=".zip,application/zip" hidden onChange={(event) => chooseFile(event.target.files?.[0])} />
              <div className="upload-icon">{file ? '✓' : '↑'}</div>
              {file ? <><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(1)} MB · listo para analizar</small></> : <><strong>Suelta aquí tu archivo ZIP</strong><span>o <u>búscalo en tu equipo</u></span><small>Formato JSON · máximo 1 GB</small></>}
            </div>

            {importError && <div className="error-banner" role="alert">{importError}</div>}
            <button className="primary-button" onClick={importFile} disabled={isImporting}>
              {isImporting ? <><i className="spinner" /> {uploadProgress < 100 ? `Subiendo archivo · ${uploadProgress}%` : 'Procesando relaciones…'}</> : 'Analizar mi comunidad'}
            </button>
            {isImporting && <div className="upload-progress" aria-live="polite"><span style={{ width: `${uploadProgress}%` }} />{uploadProgress < 100 && <button onClick={cancelImport}>Cancelar</button>}</div>}
            <button className="demo-button" data-tour="demo" onClick={openDemo} disabled={isImporting}>Explorar con datos de ejemplo</button>
            <div className="privacy-note"><span>⌁</span><p><strong>Privado por diseño.</strong> El archivo se procesa temporalmente y se elimina al cerrar la sesión.</p></div>
          </div>

          <details className="download-help" id="como-conseguir"><summary>Obtener mi exportación</summary><ol><li>Abre Instagram → Configuración y actividad.</li><li>Entra en Centro de cuentas → Tu información y permisos.</li><li>Descarga tu información en formato JSON.</li></ol></details>
        </section>
      </main>
    );
  }

  const metrics = [
    { label: 'Seguidores', value: analysis.summary.followers, tone: 'violet' },
    { label: 'Seguidos', value: analysis.summary.following, tone: 'amber' },
    { label: 'Mutuos', value: analysis.summary.mutuals, tone: 'green' },
    { label: 'Solo te siguen', value: analysis.summary.followers_only, tone: 'blue' },
    { label: 'No te siguen', value: analysis.summary.following_only, tone: 'coral' },
  ];

  const toggleFilter = (key: 'showMutuals' | 'showFans' | 'showNonFollowers') => {
    setFilters((current) => ({ ...current, [key]: !current[key] }));
  };

  const mergeAdditionalExport = async () => {
    if (!mergeFile || !mergeUsername.trim() || !mergeConsent) {
      setMergeStatus('Indica el propietario, selecciona su ZIP y confirma su autorización.');
      return;
    }
    setIsMerging(true);
    setMergeStatus(null);
    try {
      const result = await api.mergeExport(analysis.session_id, mergeFile, mergeUsername.trim(), mergeConsent);
      setAnalysis(result);
      loadGraph(result.graph);
      setMergeFile(null);
      setMergeUsername('');
      setMergeConsent(false);
      setMergeStatus(`Red de @${mergeUsername.trim()} añadida correctamente.`);
    } catch (error) {
      setMergeStatus(error instanceof Error ? error.message : 'No se pudo añadir la exportación.');
    } finally {
      setIsMerging(false);
    }
  };

  return (
    <main className="dashboard-shell">
      <ProductTour open={isTourOpen} hasAnalysis onClose={closeTour} onFillExample={() => setUsername('circlescope_demo')} onOpenDemo={openTutorialDemo} onSetView={setView} onDemoGraphFilters={demonstrateGraphFilters} onRestoreGraphFilters={restoreGraphFilters} onDemoGraphSearch={demonstrateGraphSearch} onCleanupDemo={cleanupTutorialDemo} />
      <header className="dashboard-header">
        <div className="brand"><Logo /><span>CircleScope</span></div>
        <div className="profile-chip"><button className="header-tour-button" onClick={() => setIsTourOpen(true)}>Guía</button><span>@{analysis.summary.username}</span><button onClick={startOver}>Cambiar archivo</button></div>
      </header>

      <aside className="sidebar">
        <div className="sidebar-intro"><span className="status-dot" /><div><strong>Análisis completado</strong><small>Sesión privada · 1 hora</small></div></div>
        <h2>Tu comunidad</h2>
        <div className="metric-list" data-tour="metrics">{metrics.map((metric) => <div className="metric-row" key={metric.label}><span className={`metric-dot ${metric.tone}`} /><span>{metric.label}</span><strong>{metric.value.toLocaleString('es-ES')}</strong></div>)}</div>
        <div className="legend graph-filter-list"><h3>Mostrar en el mapa</h3><p className="fixed-filter"><i className="legend-dot root" />Tu perfil <small>Siempre visible</small></p><label><input type="checkbox" checked={filters.showMutuals} onChange={() => toggleFilter('showMutuals')} /><i className="legend-dot mutual" />Os seguís mutuamente</label><label><input type="checkbox" checked={filters.showFans} onChange={() => toggleFilter('showFans')} /><i className="legend-dot follower" />Solo te sigue</label><label><input type="checkbox" checked={filters.showNonFollowers} onChange={() => toggleFilter('showNonFollowers')} /><i className="legend-dot following" />Solo le sigues</label></div>
        <details className="merge-panel" data-tour="merge">
          <summary>Añadir otra exportación</summary>
          <p>Amplía nodos con el ZIP autorizado de otra persona.</p>
          <label><span>Usuario propietario</span><input value={mergeUsername} onChange={(event) => setMergeUsername(event.target.value)} placeholder="usuario" /></label>
          <label className="merge-file"><span>{mergeFile?.name ?? 'Seleccionar ZIP JSON'}</span><input type="file" accept=".zip,application/zip" onChange={(event) => setMergeFile(event.target.files?.[0] ?? null)} /></label>
          <label className="merge-consent"><input type="checkbox" checked={mergeConsent} onChange={(event) => setMergeConsent(event.target.checked)} /><span>Confirmo que el propietario autorizó este análisis.</span></label>
          <button onClick={mergeAdditionalExport} disabled={isMerging}>{isMerging ? 'Procesando…' : 'Fusionar red'}</button>
          {mergeStatus && <small role="status">{mergeStatus}</small>}
          <div className="imported-profiles">Datos disponibles: {analysis.imported_profiles.map((profile) => `@${profile}`).join(', ')}</div>
        </details>
        {selectedNode && <div className="selected-card"><small>PERFIL SELECCIONADO</small><strong>{selectedNode.username}</strong><span>{selectedNode.degree} conexiones conocidas</span></div>}
        <button className="delete-button" onClick={startOver}>Cerrar y borrar sesión</button>
      </aside>

      <section className="content-area">
        {analysis.warnings.map((warning) => <div className="data-warning" role="status" key={warning}><strong>Revisa el intervalo del export</strong><span>{warning}</span></div>)}
        <div className="content-header">
          <div><h1>{view === 'graph' ? 'Mapa de relaciones' : view === 'list' ? 'Directorio' : 'Centro de seguridad'}</h1><p>{view === 'graph' ? `${filteredGraphData.nodes.length} perfiles · ${filteredGraphData.links.length} conexiones` : view === 'list' ? 'Consulta y exporta los perfiles de tu análisis' : 'Integraciones, límites y evaluación técnica'}</p></div>
          <div className="view-switch" data-tour="view-switch"><button className={view === 'graph' ? 'active' : ''} onClick={() => setView('graph')}>Mapa</button><button className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}>Directorio</button><button className={view === 'risks' ? 'active' : ''} onClick={() => setView('risks')}>Seguridad</button></div>
        </div>
        {view === 'graph' ? <>
          {Boolean(analysis.graph.metadata.truncated) && <div className="limit-banner">Mostramos una selección equilibrada de {analysis.graph.metadata.visible_nodes as number} perfiles para mantener el mapa fluido. La lista contiene el análisis completo.</div>}
          <div className="graph-tools">
            <div className="quick-filters" data-tour="quick-filters" aria-label="Filtros rápidos">
              <button className={filters.showMutuals ? 'active mutual' : ''} onClick={() => toggleFilter('showMutuals')}><i /> Mutuos</button>
              <button className={filters.showFans ? 'active follower' : ''} onClick={() => toggleFilter('showFans')}><i /> Solo te siguen</button>
              <button className={filters.showNonFollowers ? 'active following' : ''} onClick={() => toggleFilter('showNonFollowers')}><i /> No te siguen</button>
            </div>
            <div className="graph-actions">
              <label className="layout-field"><span>Límite</span><select value={filters.nodeLimit} onChange={(event) => setFilters((current) => ({ ...current, nodeLimit: Number(event.target.value) as 100 | 250 | 600 }))}><option value="100">100 perfiles</option><option value="250">250 perfiles</option><option value="600">600 perfiles</option></select></label>
              <label className="layout-field"><span>Orden</span><select value={graphLayout} onChange={(event) => setGraphLayout(event.target.value as GraphLayout)}><option value="groups">Por grupos</option><option value="free">Libre</option></select></label>
              <label className="search-field" data-tour="graph-search"><span>⌕</span><input value={filters.searchQuery} onChange={(event) => { const query = event.target.value.toLowerCase(); setFilters((current) => ({ ...current, searchQuery: query })); setSearch(query); }} placeholder="Filtrar por nombre…" /></label>
            </div>
          </div>
          <div className="explorer-status"><strong>{filteredGraphData.nodes.length - 1}</strong> perfiles visibles de {graphData.nodes.length - 1}<span>Usa la rueda para acercar y arrastra el fondo para moverte.</span></div>
          <div className="graph-tour-target" data-tour="graph"><GraphCanvas graphData={filteredGraphData} search={search} layout={graphLayout} onNodeSelect={setSelectedNode} onNodeExpand={(nodeId) => expandNode(analysis.session_id, nodeId)} /></div>
          {(isLoading || message) && <div className="graph-message">{isLoading ? <><i className="spinner dark" /> Explorando conexiones conocidas…</> : message}</div>}
        </> : view === 'list' ? <div className="directory-tour-target" data-tour="directory"><RelationshipTable sessionId={analysis.session_id} summary={analysis.summary} /></div> : <RiskLab />}
      </section>
    </main>
  );
}
