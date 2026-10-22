/**
 * "Try" query chips shown below the search bar.
 *
 * To add a new chip, append an entry to this array.
 * The first entry is auto-selected on load and its mockData (if provided)
 * is displayed immediately without hitting the backend.
 *
 * shape:
 * {
 *   id:       string   — unique key
 *   label:    string   — button text
 *   query:    string   — pre-fills the search input when selected
 *   mockData: object|null — if non-null, used instead of a real API call
 *             { clusters: PrecedentCluster[] }
 * }
 */
import MISREPRESENTATION_MOCK from '../mock/misrepresentation.js';

const CHIPS = [

  //FIRST CHIP: a very common public legal issue, backed by full mock data so the UI is immediately populated with realistic content.

  {
    id: 'misrepresentation',
    label: 'Misrepresentation in contract',
    query: 'Misrepresentation in contract formation under Sri Lankan law',
    mockData: MISREPRESENTATION_MOCK,
  },

  //Other chips — no mock data; these call the live backend.
  {
    id: 'fundamental-rights',
    label: 'Fundamental rights breach',
    query: 'Fundamental rights breach under Article 17 of Sri Lankan constitution',
    mockData: null,
  },
  {
    id: 'employer-negligence',
    label: 'Employer liability negligence',
    query: 'Employer liability for negligence in Sri Lankan workplace injury cases',
    mockData: null,
  },
];

export default CHIPS;
