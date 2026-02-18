# Code Review

Run a thorough code review using the code-reviewer agent. Usage: `/review [target]`

## Determine Scope

Parse the argument to determine what to review:
- No argument: review all uncommitted changes (`git diff` + `git diff --cached`)
- File path: review that specific file
- `--staged`: review only staged changes
- `--branch`: review all changes on current branch vs main (`git diff main...HEAD`)
- `--phase <A-E>`: review all files touched in that execution phase

## Execute Review

1. **Gather changes**: Run appropriate git diff to collect the code to review
2. **Launch code-reviewer agent**: Delegate the review using the Task tool with:
   - subagent_type: "general-purpose"
   - The agent definition from `.claude/agents/code-reviewer.md`
   - Full diff content and file contents for context
   - Project invariants from CLAUDE.md
3. **Present findings**: Show the review summary table and all findings by severity

## Post-Review Actions

Based on the verdict:
- **APPROVE**: Suggest `/pr-checklist` to finalize
- **REQUEST CHANGES**: List fixes needed, offer to auto-fix MINOR issues
- **BLOCK**: List CRITICAL issues that must be resolved before proceeding

## Integration Points

- Runs automatically as part of `/pr-checklist` (step 6: diff review)
- Can be triggered at any checkpoint gate alongside security-correctness-reviewer
- Works with `/bug-investigation` for post-fix verification
