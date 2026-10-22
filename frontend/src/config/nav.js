/**
 * Navigation bar items.
 * To add a new nav item, append an entry to this array.
 *
 * shape: { id: string, label: string, component?: string }
 * - id:        unique key used for active-tab tracking
 * - label:     text shown in the navbar button
 * - component: (future) which page component to render; currently only 'search' is wired up
 */
const NAV_ITEMS = [
  {
    id: 'search',
    label: 'Find Legal Precedents',
    component: 'search',
  },
  // Add more items here, e.g.:
  // { id: 'analytics', label: 'Analytics', component: 'analytics' },
];

export default NAV_ITEMS;
