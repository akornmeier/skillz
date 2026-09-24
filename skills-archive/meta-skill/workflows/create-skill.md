# Create Skill

1. Scope the Capability - Establish what the skill does and what it produces. One skill is one capability; if the ask covers two unrelated jobs, say so and scope to one.
2. Choose the Location - Personal skills go in `~/.claude/skills/<name>/`, project skills in `.claude/skills/<name>/` where git shares them with the team. Ask only if the prompt leaves it genuinely ambiguous.
3. Write the Description First - Both halves in one field: what the skill does, and when to fire, in the phrasing a user actually types. It is the only part always in context — a skill that never triggers is a skill that does not exist.
4. Author SKILL.md - Fill in `templates/SKILL.md`. Read `references/context-engineering-claude5.md` for what belongs in the router, what belongs behind a condition, and what to cut outright.
5. Add Supporting Files - Only where a route needs one: a template for an output shape, a reference for depth, a script for what is better executed than described. Each gets a *read it when* row in the Files table. A file no route reads should not exist.
6. Grade - Run `references/skill-review-rubric.md` against the result and apply the edit each failing dimension names. Loop until every dimension passes.
