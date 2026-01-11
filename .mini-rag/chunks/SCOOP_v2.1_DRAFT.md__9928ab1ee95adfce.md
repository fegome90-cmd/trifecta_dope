## 10) Owners + Stakeholders (con veto power)

**STAKEHOLDERS**:

1. **Felipe Gonzalez** (Owner/Maintainer)
   Usa: Todos los workflows (append, query, ctx sync)
   Dolor si se rompe: Project blocked (único dev)
   Veto power: **SÍ** (absolute veto)
   Si veto: Approval required BEFORE merge
   Contact: GitHub issues / direct

2. **CI Pipeline** (Automated stakeholder)
   Usa: `session append` en integration tests
   Dolor si se rompe: Tests fail, CI red
   Veto power: **SÍ (automated)** - failing tests = auto-veto
   Si veto: Cannot merge until tests green
   Contact: GitHub Actions logs

3. **Future Contributors** (hypothetical)
   Usa: TBD (depende de adoption)
   Dolor si se rompe: Onboarding friction
   Veto power: **CONSULTIVO** (feedback only, no block)
   Contact: GitHub issues

---
