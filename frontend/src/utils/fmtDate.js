export function fmtDate(s) {
  if (!s) return '';
  const d = new Date(s);
  return isNaN(d.getTime())
    ? s
    : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}
