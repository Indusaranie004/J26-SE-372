function IssueNode({ issue, level, selectedIssue, onSelect, knownFacts }) {
  const isRoot = level === 0;
  const isSelected = selectedIssue?.id === issue.id;
  const hasMissingFacts = (issue.missing_facts || []).length > 0;
  const allKnown = (issue.missing_facts || []).every(f => knownFacts.has(f));
  const hasAuthority = (issue.authority_hints || []).length > 0;

  let statusClass = 'cd-node-ready';
  let statusText = 'Ready to research';
  
  if (isRoot) {
    statusClass = 'cd-node-main';
    statusText = 'Main question';
  } else if (hasMissingFacts && !allKnown) {
    statusClass = 'cd-node-needs';
    const authText = hasAuthority ? ' · 1 authority' : '';
    statusText = `Needs ${issue.missing_facts.length} fact${issue.missing_facts.length > 1 ? 's' : ''}${authText}`;
  }

  return (
    <div 
      className={`cd-issue-node ${statusClass}${isSelected ? ' selected' : ''}`}
      onClick={() => onSelect(issue)}
      style={{ marginLeft: `${level * 24}px` }}
    >
      <div className="cd-node-question">{issue.question}</div>
      <div className="cd-node-status">{statusText}</div>
    </div>
  );
}

export default function IssueTreeView({ treeData, selectedIssue, onSelectIssue, knownFacts }) {
  if (!treeData) return null;

  const rootQuestion = treeData.main_issue || 'Main legal question';
  const issues = treeData.issues || [];

  return (
    <div className="cd-tree-container">
      <div className="cd-tree-root">
        <IssueNode
          issue={{ id: 'root', question: rootQuestion, missing_facts: [], authority_hints: [] }}
          level={0}
          selectedIssue={selectedIssue}
          onSelect={() => {}}
          knownFacts={knownFacts}
        />
      </div>
      <div className="cd-tree-branches">
        {issues.map(issue => (
          <div key={issue.id} className="cd-tree-branch">
            <IssueNode
              issue={issue}
              level={1}
              selectedIssue={selectedIssue}
              onSelect={onSelectIssue}
              knownFacts={knownFacts}
            />
            {(issue.children || []).map(child => (
              <IssueNode
                key={child.id}
                issue={child}
                level={2}
                selectedIssue={selectedIssue}
                onSelect={onSelectIssue}
                knownFacts={knownFacts}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}