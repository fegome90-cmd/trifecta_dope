### ❌ Missing: `trifecta load` Command

**What needs to be added**:

1. **LoadContextUseCase** in `src/application/use_cases.py`
2. **load command** in `src/infrastructure/cli.py`
3. **Fish completions** in `completions/trifecta.fish`

**Implementation**:
```python
class LoadContextUseCase:
    def execute(self, segment: str, task: str) -> str:
        files = self.select_files(task, segment)
        return self.format_context(files)
    
    def select_files(self, task: str, segment: str) -> list[Path]:
        base = Path(f\"/path/to/{segment}\")
        files = [base / \"skill.md\"]  # Always
        
        task_lower = task.lower()
        if any(kw in task_lower for kw in [\"implement\", \"debug\", \"fix\"]):
            files.append(base / \"_ctx/agent.md\")
        if any(kw in task_lower for kw in [\"plan\", \"design\"]):
            files.append(base / \"_ctx/prime_{segment}.md\")
        if any(kw in task_lower for kw in [\"session\", \"handoff\"]):
            files.append(base / \"_ctx/session_{segment}.md\")
        
        files.append(base / \"README_TF.md\")
        return [f for f in files if f.exists()]
```

**Exit Criteria**:
- ✅ `trifecta load --segment debug-terminal --task \"implement DT2-S1\"` works
- ✅ Correct files selected based on keywords
- ✅ Output is valid markdown
- ✅ Works with any agent (Claude, Gemini, GPT)

---
