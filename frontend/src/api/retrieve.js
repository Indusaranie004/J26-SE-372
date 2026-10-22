const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const COMPONENT_A_BASE = 'https://component-a-api.onrender.com';

export async function retrievePrecedents(query) {
  const res = await fetch(`${API_BASE}/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`/retrieve ${res.status}: ${text}`);
  }

  const data = await res.json();
  const clusters = data.clusters ?? [];
  const max = clusters[0]?.rrf_score ?? 1;

  return clusters.map((c) => ({
    ...c,
    case_id: c.case_id ?? c.seed_id,
    summary: c.summary ?? null,
    rrf_score: c.rrf_score / max,
    legal_context: {
      judicial_treatment: Array.isArray(c.legal_context?.judicial_treatment)
        ? c.legal_context.judicial_treatment
        : (c.legal_context?.judicial_treatment ?? null),
      legislative_foundation: Array.isArray(c.legal_context?.legislative_foundation)
        ? c.legal_context.legislative_foundation
        : (c.legal_context?.legislative_foundation ?? null),
      litigation_history: Array.isArray(c.legal_context?.litigation_history)
        ? c.legal_context.litigation_history
        : (c.legal_context?.litigation_history ?? null),
    },
  }));
}

export async function getCaseSummary(seedId) {
  try {
    const res = await fetch(`${COMPONENT_A_BASE}/cases/${encodeURIComponent(seedId)}`);
    if (!res.ok) return null;

    const data = await res.json();
    if (!data.text_available) return null;

    const caption = data.sections?.caption?.text?.trim() ?? '';
    const bodySnippet = data.sections?.body?.text?.slice(0, 800).trim() ?? '';

    if (!caption && !bodySnippet) return null;
    return caption ? `${caption}\n\n${bodySnippet}…` : `${bodySnippet}…`;
  } catch {
    return null;
  }
}