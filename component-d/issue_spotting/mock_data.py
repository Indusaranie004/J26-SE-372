# component-d/issue_spotting/mock_data.py

MOCK_ISSUE_TREE = {
    "query": "wrongful termination after employee complaint",
    "main_issue": "Was the employee's dismissal legally valid, procedurally fair, and non-retaliatory?",
    "main_research_question": "What are the legal requirements for a lawful dismissal and what remedies are available for wrongful termination under Sri Lankan labor law?",
    "global_missing_facts": [
        "Exact dates of the overtime complaint and the subsequent dismissal",
        "The specific terms of the client's employment contract",
        "Whether the company has a written disciplinary policy"
    ],
    "urgent": None,
    "issues": [
        {
            "id": "i1",
            "question": "Was there a valid reason for the dismissal?",
            "research_question": "What must an employer show to justify a dismissal for misconduct?",
            "legal_elements": ["A reason was given", "It is legally permissible", "Evidence supports it"],
            "relevant_facts": ["Client was dismissed by the employer"],
            "missing_facts": ["Reason the employer gave"],
            "applicable_law": [],
            "authority_hints": ["valid reason for dismissal", "unfair termination"],
            "status": "needs_facts",
            "children": [
                {
                   "id": "i1.1",
                   "question": "What reason did the employer give?",
                   "research_question": "Is the stated reason one the law permits?",
                   "legal_elements": ["Employer's stated reason"],
                   "relevant_facts": [],
                   "missing_facts": ["The specific reason provided by the employer"],
                   "applicable_law": [],
                   "authority_hints": [],
                   "status": "needs_facts",
                   "children": []
                },
                {
                   "id": "i1.2",
                   "question": "Is there evidence for that reason?",
                   "research_question": "How strong must the employer’s evidence be?",
                   "legal_elements": ["Factual proof of misconduct"],
                   "relevant_facts": [],
                   "missing_facts": ["Evidence supporting the reason"],
                   "applicable_law": [],
                   "authority_hints": ["pereraabc2014"],
                   "status": "needs_facts",
                   "children": []
                }
            ]
        },
        {
            "id": "i2",
            "question": "Was the dismissal procedure lawful?",
            "research_question": "What are the mandatory procedural steps an employer must follow before terminating an employee?",
            "legal_elements": ["Proper notice must be provided", "A disciplinary process or domestic inquiry must be conducted"],
            "relevant_facts": [],
            "missing_facts": ["Whether notice or an inquiry took place"],
            "applicable_law": [],
            "authority_hints": ["domestic inquiry", "procedural fairness"],
            "status": "needs_facts",
            "children": [
                {
                   "id": "i2.1",
                   "question": "Was proper notice given?",
                   "research_question": "What notice does the law require?",
                   "legal_elements": ["Written notice of termination"],
                   "relevant_facts": [],
                   "missing_facts": ["Date and method of notice"],
                   "applicable_law": [],
                   "authority_hints": [],
                   "status": "needs_facts",
                   "children": []
                }           
            ]
        },
        {
            "id": "i3",
            "question": "Was the dismissal retaliatory?",
            "research_question": "Does the law prohibit retaliation?",
            "legal_elements": ["A complaint was made", "Dismissal followed it", "Close timing"],
            "relevant_facts": ["Employee complained about unpaid overtime", "Dismissal occurred shortly afterwards"],
            "missing_facts": ["Date and form of the overtime complaint"],
            "applicable_law": [],
            "authority_hints": ["retaliatory dismissal", "victimization"],
            "status": "needs_facts",
            "children": []
        },
        {
            "id": "i4",
            "question": "What remedies are available?",
            "research_question": "When is reinstatement ordered and can compensation be claimed?",
            "legal_elements": ["Assessment of financial loss", "Feasibility of reinstatement"],
            "relevant_facts": ["Client was dismissed", "Client is owed unpaid overtime"],
            "missing_facts": [],
            "applicable_law": [],
            "authority_hints": ["compensation", "reinstatement", "recovery of unpaid wages"],
            "status": "ready",
            "children": []
        }
    ]
}