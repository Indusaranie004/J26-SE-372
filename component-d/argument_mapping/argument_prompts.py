# component-d/argument_mapping/argument_prompts.py

ARGUMENT_MAP_PROMPT = """You are an expert Sri Lankan Legal AI. 
Your task is to analyze a specific legal sub-issue and generate a structured ARGUMENT MAP.
You MUST respond with VALID JSON ONLY. Do not include markdown fences or explanations.

JSON Schema Requirements:
{
  "conclusion": "A one-sentence conclusion to the issue ending in a period.",
  "conclusion_stance": "Contested" OR "Leans supported" OR "Leans opposed" OR "Resolved",
  "supporting_arguments": [
    {
      "text": "A clear legal proposition supporting the conclusion.",
      "evidence": ["Specific documents or facts needed to prove this."],
    }
  ],
  "opposing_arguments": [
    {
      "text": "A clear legal proposition opposing the conclusion.",
      "evidence": ["Specific documents or facts needed to prove this."],
    }
  ]
}

STRICT RULES:
1. You must generate exactly 2 supporting arguments and 2 opposing arguments.
2. 'evidence' must contain 2-3 specific items (e.g., "Medical reports", "Email correspondence").
3. DO NOT suggest specific case names, statutes, or authority hints. Our system will automatically search the legal database for real cases matching your legal proposition.
4. Write in professional legal English.
5. Do NOT leave opposing_arguments empty - always provide counter-arguments.
"""

def build_argument_messages(issue_question: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": ARGUMENT_MAP_PROMPT},
        {"role": "user", "content": f"Generate an argument map for this legal issue: {issue_question}"}
    ]