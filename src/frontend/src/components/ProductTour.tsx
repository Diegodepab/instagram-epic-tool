import { useCallback, useEffect, useLayoutEffect, useMemo, useState } from 'react';

type AppView = 'graph' | 'list' | 'risks';
type Rect = { top: number; left: number; width: number; height: number };

type ProductTourProps = {
  open: boolean;
  hasAnalysis: boolean;
  onClose: () => void;
  onFillExample: () => void;
  onOpenDemo: () => Promise<void>;
  onSetView: (view: AppView) => void;
  onDemoGraphFilters: () => void;
  onRestoreGraphFilters: () => void;
  onDemoGraphSearch: () => void;
  onCleanupDemo: () => Promise<void>;
};

type Step = {
  target: string;
  eyebrow: string;
  title: string;
  copy: string;
  placement: 'top' | 'bottom' | 'left' | 'right';
  prepare?: () => void | Promise<void>;
};

const waitForTarget = async (selector: string): Promise<void> => {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    if (document.querySelector(selector)) return;
    await new Promise((resolve) => window.setTimeout(resolve, 100));
  }
};

export function ProductTour({ open, hasAnalysis, onClose, onFillExample, onOpenDemo, onSetView, onDemoGraphFilters, onRestoreGraphFilters, onDemoGraphSearch, onCleanupDemo }: ProductTourProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const [isPreparing, setIsPreparing] = useState(false);

  const steps = useMemo<Step[]>(() => [
    { target: '[data-tour="username"]', eyebrow: '1 · PERFIL CENTRAL', title: 'Identifica al propietario', copy: 'La guía acaba de rellenar un usuario ficticio. En un análisis real escribirías el usuario asociado al ZIP.', placement: 'right', prepare: onFillExample },
    { target: '[data-tour="upload"]', eyebrow: '2 · IMPORTACIÓN', title: 'Añade la exportación oficial', copy: 'Este control valida el ZIP y localiza seguidores y seguidos. Los navegadores impiden seleccionar archivos automáticamente.', placement: 'right' },
    { target: '[data-tour="demo"]', eyebrow: '3 · DATOS DE PRUEBA', title: 'Carga una red sintética', copy: 'Pulsa Siguiente: crearemos una sesión ficticia de 180 perfiles y continuaremos sobre la aplicación real.', placement: 'top' },
    { target: '[data-tour="metrics"]', eyebrow: '4 · MÉTRICAS', title: 'Compara los grupos principales', copy: 'Estas cifras son exactas para los datos importados: mutuos, solo seguidores y cuentas que no te siguen.', placement: 'right', prepare: async () => { await onOpenDemo(); await waitForTarget('[data-tour="metrics"]'); } },
    { target: '[data-tour="quick-filters"]', eyebrow: '5 · FILTROS EN ACCIÓN', title: 'Aísla un grupo en el mapa', copy: 'Hemos ocultado automáticamente dos grupos. El mapa muestra ahora únicamente relaciones mutuas.', placement: 'bottom', prepare: onDemoGraphFilters },
    { target: '[data-tour="graph-search"]', eyebrow: '6 · BÚSQUEDA EN EL GRAFO', title: 'Localiza un perfil', copy: 'La guía ha buscado “amigo_001”. El nodo coincidente permanece visible y destacado.', placement: 'left', prepare: onDemoGraphSearch },
    { target: '[data-tour="graph"]', eyebrow: '7 · EXPLORACIÓN', title: 'Mueve, acerca y selecciona', copy: 'Arrastra el fondo, usa la rueda y selecciona un nodo para ver sus conexiones conocidas. Hemos restaurado todos los grupos.', placement: 'left', prepare: () => { onRestoreGraphFilters(); onSetView('graph'); } },
    { target: '[data-tour="view-switch"]', eyebrow: '8 · VISTAS', title: 'Cambia sin perder el análisis', copy: 'Mapa, Directorio y Seguridad trabajan sobre la misma sesión temporal.', placement: 'bottom' },
    { target: '[data-tour="directory-filters"]', eyebrow: '9 · FILTROS DEL DIRECTORIO', title: 'Consulta solo relaciones mutuas', copy: 'Hemos abierto el Directorio y activado “Mutuos”. La tabla y sus totales se actualizan al instante.', placement: 'bottom', prepare: async () => { onSetView('list'); await waitForTarget('[data-tour="directory-filters"]'); (document.querySelector('[data-tour="directory-filters"] button:nth-child(2)') as HTMLButtonElement | null)?.click(); } },
    { target: '[data-tour="directory-search"]', eyebrow: '10 · BÚSQUEDA Y CSV', title: 'Busca y exporta el resultado', copy: 'Puedes buscar dentro de la categoría activa y descargar exactamente esa selección como CSV.', placement: 'left' },
    { target: '[data-tour="merge"]', eyebrow: '11 · SEGUNDO NIVEL', title: 'Amplía la red con consentimiento', copy: 'Otra persona puede aportar su ZIP autorizado. CircleScope combina ambas redes sin consultar perfiles ajenos.', placement: 'right', prepare: () => { onSetView('graph'); } },
    { target: '[data-tour="security-console"]', eyebrow: '12 · FUNCIONES AVANZADAS', title: 'Revisa límites antes de activar', copy: 'El Centro de seguridad muestra integraciones, disponibilidad y barreras de uso. Al terminar borraremos toda la demo.', placement: 'top', prepare: async () => { onSetView('risks'); await waitForTarget('[data-tour="security-console"]'); } },
  ], [onDemoGraphFilters, onDemoGraphSearch, onFillExample, onOpenDemo, onRestoreGraphFilters, onSetView]);

  const step = steps[stepIndex];

  const updateRect = useCallback(() => {
    const element = document.querySelector(step.target);
    if (!(element instanceof HTMLElement)) { setRect(null); return; }
    const bounds = element.getBoundingClientRect();
    const padding = 8;
    setRect({ top: Math.max(8, bounds.top - padding), left: Math.max(8, bounds.left - padding), width: Math.min(window.innerWidth - 16, bounds.width + padding * 2), height: Math.min(window.innerHeight - 16, bounds.height + padding * 2) });
  }, [step.target]);

  useEffect(() => {
    if (!open) return;
    setStepIndex(hasAnalysis ? 3 : 0);
  }, [open, hasAnalysis]);

  useLayoutEffect(() => {
    if (!open) return;
    const element = document.querySelector(step.target);
    if (element instanceof HTMLElement) element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    const timer = window.setTimeout(updateRect, 220);
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);
    return () => { window.clearTimeout(timer); window.removeEventListener('resize', updateRect); window.removeEventListener('scroll', updateRect, true); };
  }, [open, step, updateRect]);

  useEffect(() => {
    if (!open) return;
    const keyHandler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        localStorage.setItem('circlescope_guided_tour_v3_seen', 'true');
        onClose();
        void onCleanupDemo();
      }
      if (event.key === 'ArrowRight') void advance();
      if (event.key === 'ArrowLeft' && stepIndex > 0) setStepIndex((current) => current - 1);
    };
    window.addEventListener('keydown', keyHandler);
    return () => window.removeEventListener('keydown', keyHandler);
  });

  const finish = async () => { localStorage.setItem('circlescope_guided_tour_v3_seen', 'true'); onClose(); await onCleanupDemo(); };
  const advance = async () => {
    if (isPreparing) return;
    if (stepIndex === steps.length - 1) { await finish(); return; }
    setIsPreparing(true);
    try {
      const nextStep = steps[stepIndex + 1];
      await nextStep.prepare?.();
      setStepIndex((current) => current + 1);
    } finally { setIsPreparing(false); }
  };

  if (!open) return null;

  const cardStyle = (() => {
    if (!rect) return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' };
    const width = Math.min(350, window.innerWidth - 28);
    let left = rect.left + rect.width / 2 - width / 2;
    let top = rect.top + rect.height + 18;
    if (step.placement === 'top') top = rect.top - 18;
    if (step.placement === 'right') { left = rect.left + rect.width + 18; top = rect.top; }
    if (step.placement === 'left') { left = rect.left - width - 18; top = rect.top; }
    left = Math.max(14, Math.min(window.innerWidth - width - 14, left));
    const estimatedHeight = 240;
    if (step.placement === 'top') top -= estimatedHeight;
    top = Math.max(14, Math.min(window.innerHeight - estimatedHeight - 14, top));
    return { width, left, top };
  })();

  return <div className="guided-tour" aria-live="polite">
    {rect && <><div className="tour-mask mask-top" style={{ height: rect.top }} /><div className="tour-mask mask-left" style={{ top: rect.top, width: rect.left, height: rect.height }} /><div className="tour-mask mask-right" style={{ top: rect.top, left: rect.left + rect.width, height: rect.height }} /><div className="tour-mask mask-bottom" style={{ top: rect.top + rect.height }} /><div className="tour-focus" style={rect} /></>}
    {!rect && <div className="tour-mask mask-full" />}
    <section className="coach-card" style={cardStyle} role="dialog" aria-modal="true" aria-labelledby="coach-title">
      <div className="coach-top"><span>GUÍA FUNCIONAL · {stepIndex + 1} DE {steps.length}</span><button onClick={() => void finish()} aria-label="Cerrar tutorial">×</button></div>
      <div className="coach-eyebrow">{step.eyebrow}</div>
      <h2 id="coach-title">{step.title}</h2><p>{step.copy}</p>
      <div className="coach-progress">{steps.map((item, index) => <i key={item.title} className={index === stepIndex ? 'current' : index < stepIndex ? 'done' : ''} />)}</div>
      <footer><button className="coach-skip" onClick={() => void finish()}>Salir y limpiar</button><div>{stepIndex > 0 && <button className="coach-back" onClick={() => setStepIndex((current) => current - 1)}>Atrás</button>}<button className="coach-next" onClick={() => void advance()} disabled={isPreparing}>{isPreparing ? 'Preparando…' : stepIndex === steps.length - 1 ? 'Terminar y limpiar' : 'Siguiente'} <span>→</span></button></div></footer>
    </section>
  </div>;
}
