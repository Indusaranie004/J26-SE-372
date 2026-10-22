/**
 * Mock response for the "Misrepresentation in contract" chip.
 * Shape mirrors the backend /retrieve response: { clusters: PrecedentCluster[] }
 *
 * Covers the very common public legal issue of being misled into signing a
 * contract — relevant to land sales, business agreements, consumer purchases.
 */
const MISREPRESENTATION_MOCK = {
  clusters: [
    {
      case_id: 'SC/FR/451/2001',
      summary:
        'The Supreme Court held that a party induced to enter a contract by a material misrepresentation of fact is entitled to rescission regardless of whether the misrepresentation was fraudulent or innocent, reaffirming the equitable principle that the representor cannot retain the benefit of a false statement.',
      rrf_score: 0.94,
      is_seed: true,
      legal_context: {
        litigation_history: [
          { related_id: 'DC/COL/1234/1997', hops: 2, court: 'District Court Colombo', judge: 'Edussuriya J' },
          { related_id: 'CA/123/1999',       hops: 1, court: 'Court of Appeal',        judge: 'Gooneratne JA' },
          { related_id: 'SC/FR/451/2001',    hops: 0, court: 'Supreme Court of Sri Lanka', judge: 'Amarasinghe CJ, Wadugodapitiya J, Gamini Amaratunga J' },
        ],
        judicial_treatment: [
          {
            target_id: 'SC/APPEAL/22/2007',
            citation_type: 'Followed',
            direction: 'cited_by',
            evidence: 'The Court of Appeal affirmed that the principle of rescission for innocent misrepresentation applies equally to commercial lease agreements, extending the doctrine beyond pure sale-of-goods disputes.',
            scope: 'Ratio Decidendi',
            effective_date: '2007-03-14',
          },
          {
            target_id: 'SC/FR/88/2009',
            citation_type: 'Distinguished',
            direction: 'cited_by',
            evidence: 'The court distinguished the present authority on the basis that the representee had independent means of verifying the false statement and chose not to, holding that reliance must be reasonable.',
            scope: 'Ratio Decidendi',
            effective_date: '2009-11-02',
          },
          {
            target_id: 'CA/CIVIL/344/1995',
            citation_type: 'Followed',
            direction: 'cases_cited',
            evidence: "The Supreme Court drew on the Court of Appeal's earlier analysis of the threshold of materiality, adopting the objective reasonable-person standard rather than a purely subjective test.",
            scope: 'Ratio Decidendi',
            effective_date: '1995-06-22',
          },
          {
            target_id: 'SC/APPEAL/67/2014',
            citation_type: 'Overruled',
            direction: 'cited_by',
            evidence: 'The subsequent bench overruled the quantum of damages element of this decision, holding that consequential losses arising from fraudulent misrepresentation are governed by tort principles, not the contractual expectation measure.',
            scope: 'Obiter Dictum',
            effective_date: '2014-09-08',
          },
          {
            target_id: 'CA/CIVIL/201/1988',
            citation_type: 'Followed',
            direction: 'cases_cited',
            evidence: 'The foundational articulation of misrepresentation doctrine in Sri Lankan civil law was adopted, confirming that the Roman-Dutch principle of dolus in contrahendo underlies local jurisprudence.',
            scope: 'Ratio Decidendi',
            effective_date: '1988-04-17',
          },
        ],
        legislative_foundation: [
          { act_id: 'LKA-ACT-1866-001', name: 'Prevention of Frauds Ordinance',       section: 'Section 2 — written contracts for land' },
          { act_id: 'LKA-ACT-1978-032', name: 'Sale of Goods Ordinance (as amended)',  section: 'Section 15 — implied conditions as to title' },
          { act_id: 'LKA-ACT-1956-014', name: 'Prescription Ordinance',                section: 'Section 7 — limitation of actions in contract' },
        ],
      },
    },
    {
      case_id: 'CA/CIVIL/344/1995',
      summary:
        "The Court of Appeal established that materiality of a misrepresentation is assessed objectively — the statement must be one that would influence a reasonable person of the representee's class, not merely this particular representee.",
      rrf_score: 0.81,
      is_seed: false,
      legal_context: {
        litigation_history: [
          { related_id: 'DC/COL/788/1991',   hops: 1, court: 'District Court Colombo', judge: 'Seneviratne J' },
          { related_id: 'CA/CIVIL/344/1995', hops: 0, court: 'Court of Appeal',        judge: 'Gooneratne JA, Sripavan JA' },
        ],
        judicial_treatment: [
          {
            target_id: 'SC/FR/451/2001',
            citation_type: 'Followed',
            direction: 'cited_by',
            evidence: 'The Supreme Court adopted the objective materiality standard and built the seed-case doctrine on it.',
            scope: 'Ratio Decidendi',
            effective_date: '2001-08-19',
          },
          {
            target_id: 'CA/CIVIL/500/2003',
            citation_type: 'Followed',
            direction: 'cited_by',
            evidence: 'The materiality standard was applied to a consumer goods dispute, confirming its broad doctrinal reach.',
            scope: 'Obiter Dictum',
            effective_date: '2003-05-12',
          },
        ],
        legislative_foundation: [
          { act_id: 'LKA-ACT-1978-032', name: 'Sale of Goods Ordinance (as amended)', section: 'Section 15 — implied conditions as to title' },
        ],
      },
    },
    {
      case_id: 'SC/APPEAL/22/2007',
      summary:
        'The Supreme Court extended the equitable remedy of rescission for innocent misrepresentation to commercial lease agreements, rejecting the argument that such relief is confined to contracts for the sale of goods.',
      rrf_score: 0.76,
      is_seed: false,
      legal_context: {
        litigation_history: [
          { related_id: 'DC/KANDY/101/2003',  hops: 2, court: 'District Court Kandy',      judge: 'Wijesuriya J' },
          { related_id: 'CA/CIVIL/77/2005',   hops: 1, court: 'Court of Appeal',            judge: 'Bandaranayake JA' },
          { related_id: 'SC/APPEAL/22/2007',  hops: 0, court: 'Supreme Court of Sri Lanka', judge: 'Shirani Bandaranayake CJ' },
        ],
        judicial_treatment: [
          {
            target_id: 'SC/FR/451/2001',
            citation_type: 'Followed',
            direction: 'cases_cited',
            evidence: 'The seed case was expressly followed as authority for the availability of rescission independent of fraud.',
            scope: 'Ratio Decidendi',
            effective_date: '2001-08-19',
          },
        ],
        legislative_foundation: [
          { act_id: 'LKA-ACT-1956-014', name: 'Prescription Ordinance',  section: 'Section 7 — limitation of actions in contract' },
          { act_id: 'LKA-ACT-1979-007', name: 'Rent Act (as amended)',   section: 'Section 22 — landlord and tenant obligations' },
        ],
      },
    },
    {
      case_id: 'SC/FR/88/2009',
      summary:
        'Where a representee had reasonable means of discovering the falsity of a representation and failed to exercise due diligence, the court held that the reliance element of misrepresentation is not satisfied and the remedy of rescission is unavailable.',
      rrf_score: 0.68,
      is_seed: false,
      legal_context: {
        litigation_history: [
          { related_id: 'DC/COL/3312/2005', hops: 1, court: 'District Court Colombo',     judge: 'Paranagama J' },
          { related_id: 'SC/FR/88/2009',    hops: 0, court: 'Supreme Court of Sri Lanka', judge: 'Marsoof J, Rajapaksa J' },
        ],
        judicial_treatment: [
          {
            target_id: 'SC/FR/451/2001',
            citation_type: 'Distinguished',
            direction: 'cases_cited',
            evidence: 'Distinguished on the ground that the representee conducted independent enquiries before contracting and did not act on the faith of the statement.',
            scope: 'Ratio Decidendi',
            effective_date: '2001-08-19',
          },
        ],
        legislative_foundation: [
          { act_id: 'LKA-ACT-1866-001', name: 'Prevention of Frauds Ordinance', section: 'Section 2 — written contracts for land' },
        ],
      },
    },
  ],
};

export default MISREPRESENTATION_MOCK;
