import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import type { ProfileSummary, RelationshipCategory, RelationshipPage } from '../types/domain';

interface RelationshipTableProps {
  sessionId: string;
  summary: ProfileSummary;
}

const PAGE_SIZE = 50;
const emptyPage: RelationshipPage = { items: [], total: 0, offset: 0, limit: PAGE_SIZE };

const categories: Array<{ value: RelationshipCategory; label: string; count: (summary: ProfileSummary) => number }> = [
  { value: 'all', label: 'Todos', count: (summary) => summary.mutuals + summary.followers_only + summary.following_only },
  { value: 'mutuals', label: 'Mutuos', count: (summary) => summary.mutuals },
  { value: 'followers_only', label: 'Solo te siguen', count: (summary) => summary.followers_only },
  { value: 'following_only', label: 'No te siguen', count: (summary) => summary.following_only },
  { value: 'followers', label: 'Seguidores', count: (summary) => summary.followers },
  { value: 'following', label: 'Seguidos', count: (summary) => summary.following },
];

const relationshipLabels = {
  mutuals: 'Mutuo',
  followers_only: 'Solo te sigue',
  following_only: 'No te sigue',
};

export function RelationshipTable({ sessionId, summary }: RelationshipTableProps) {
  const [category, setCategory] = useState<RelationshipCategory>('all');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<RelationshipPage>(emptyPage);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  useEffect(() => {
    const currentRequest = ++requestId.current;
    const timer = window.setTimeout(async () => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await api.listRelationships(sessionId, category, search, offset, PAGE_SIZE);
        if (currentRequest === requestId.current) setPage(result);
      } catch (requestError) {
        if (currentRequest === requestId.current) {
          setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar la lista.');
        }
      } finally {
        if (currentRequest === requestId.current) setIsLoading(false);
      }
    }, 220);
    return () => window.clearTimeout(timer);
  }, [category, offset, search, sessionId]);

  const changeCategory = (next: RelationshipCategory) => {
    setCategory(next);
    setOffset(0);
  };

  const firstItem = page.total === 0 ? 0 : offset + 1;
  const lastItem = Math.min(offset + PAGE_SIZE, page.total);

  return (
    <div className="relationships-view">
      <div className="list-controls">
        <div className="category-pills" data-tour="directory-filters">
          {categories.map((item) => (
            <button className={category === item.value ? 'active' : ''} key={item.value} onClick={() => changeCategory(item.value)}>
              {item.label}<span>{item.count(summary).toLocaleString('es-ES')}</span>
            </button>
          ))}
        </div>
        <div className="list-actions" data-tour="directory-search">
          <label className="search-field"><span>⌕</span><input value={search} onChange={(event) => { setSearch(event.target.value); setOffset(0); }} placeholder="Buscar usuario…" /></label>
          <a className="csv-button" href={api.csvUrl(sessionId, category)} download>↓ Exportar CSV</a>
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead><tr><th>Perfil</th><th>Relación contigo</th><th>Conexiones conocidas</th></tr></thead>
          <tbody>
            {!isLoading && page.items.map((item) => (
              <tr key={item.username}>
                <td><span className="avatar-placeholder">{item.username.slice(0, 1).toUpperCase()}</span><strong>@{item.username}</strong></td>
                <td><span className={`relationship-badge ${item.relationship}`}>{relationshipLabels[item.relationship]}</span></td>
                <td>{item.known_connections.toLocaleString('es-ES')}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <div className="table-state"><i className="spinner dark" /> Cargando perfiles…</div>}
        {error && <div className="table-state error-text">{error}</div>}
        {!isLoading && !error && page.items.length === 0 && <div className="table-state">No hay perfiles que coincidan con esta búsqueda.</div>}
      </div>

      <div className="pagination"><span>Mostrando {firstItem}–{lastItem} de {page.total.toLocaleString('es-ES')}</span><div><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Anterior</button><button disabled={offset + PAGE_SIZE >= page.total} onClick={() => setOffset(offset + PAGE_SIZE)}>Siguiente</button></div></div>
    </div>
  );
}
