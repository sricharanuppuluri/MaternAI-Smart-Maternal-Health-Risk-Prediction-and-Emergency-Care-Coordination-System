# MATERN_AI_DEVELOPER_1_WORKFLOW.md

## Purpose

This is the operating manual for **Developer 1** in the two-person MaternAI team.

The goal is:

```text
Parallel Development
        ↓
Controlled Synchronization
        ↓
Testing
        ↓
Integration
        ↓
Stable main
```

This document is intentionally operational. Follow these rules rather than improvising Git or integration decisions.

---

# 1. Developer 1 Role

## Primary ownership

Developer 1 is the primary owner of MaternAI's:

### Backend and data layer

- FastAPI backend
- API implementation
- PostgreSQL/Supabase schema
- Supabase migrations
- RLS policies
- backend authentication/authorization checks
- backend validation
- audit logging

### AI/ML layer

- dataset preparation and documentation
- feature engineering
- model training
- model comparison
- evaluation
- explainability
- model versioning
- prediction service
- ML input/output contract

### Safety and orchestration

- deterministic safety rules
- decision engine
- local LLM backend integration
- AI Agent backend/tools
- voice backend interfaces
- backend-side workflow transitions

Developer 1 is accountable for ensuring backend contracts remain stable and secure.

## Primary directories

Prefer working primarily in:

```text
backend/
ml/
supabase/migrations/
```

and backend-related documentation/tests.

## Developer 1 should avoid

Do not make casual changes in:

```text
frontend/src/pages/
frontend/src/components/
frontend/src/layouts/
```

unless a backend integration change genuinely requires a coordinated frontend update.

Do not change shared files without coordination.

## Developer 1's rule

> If the change affects the data contract consumed by Developer 2, announce and freeze the contract before Developer 2 continues dependent work.

---

# 2. Branch Strategy

Use short-lived feature branches.

Examples:

```text
feature/d1/database-schema
feature/d1/auth-backend
feature/d1/health-api
feature/d1/ml-pipeline
feature/d1/safety-engine
feature/d1/agent-tools
```

Start from the latest `main`.

```bash
git status
git fetch origin
git checkout main
git pull --ff-only origin main
git switch -c feature/d1/<phase>-<task>
```

Do not start a new branch from another developer's feature branch unless both developers explicitly agree that temporary dependency is necessary.

## Before a new phase

`main` must be tested and synchronized before the new phase begins.

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
```

Then create the next feature branch.

---

# 3. Push Rules

Push when:

- a logical feature is complete
- a safe checkpoint has been committed
- integration is ready
- the work session ends with a usable checkpoint

Before pushing:

```bash
git status
git diff
git diff --cached
```

Run appropriate tests.

Then:

```bash
git add <specific-files>
git commit -m "feat: <description>"
git push -u origin feature/d1/<phase>-<task>
```

Never:

- push directly to `main`
- push known broken code into a branch intended for immediate integration
- force-push shared branches
- rewrite Developer 2's commits
- include unrelated refactoring in the feature commit

---

# 4. When Developer 1 Can Work Simultaneously

Examples:

```text
Developer 1: FastAPI health-record endpoint
Developer 2: Mother health-entry page using agreed request contract
→ WORK SIMULTANEOUSLY
```

```text
Developer 1: ML training/evaluation
Developer 2: ASHA dashboard layout
→ WORK SIMULTANEOUSLY
```

```text
Developer 1: Safety service internals without API changes
Developer 2: Mother dashboard styling
→ WORK SIMULTANEOUSLY
```

```text
Developer 1: Prediction API
Developer 2: Risk-result UI based on frozen response contract
→ WORK SIMULTANEOUSLY
```

## Developer 1 must coordinate first when

- changing a database column used by Developer 2
- changing an API response/request
- changing authentication behavior used by the frontend
- changing shared types
- changing frontend routing indirectly
- changing environment/config files
- changing a shared root configuration
- changing ML input/output consumed by the frontend
- changing the semantics of a safety alert shown in the UI

---

# 5. When Developer 1 Must Wait

Developer 1 waits when Developer 2 is making a coordinated change to a shared contract that Developer 1 depends on.

Examples:

```text
Developer 2: Changes frontend auth flow
Developer 1: About to modify the same auth contract
→ COORDINATE FIRST
```

```text
Developer 2: Changes a shared TypeScript/API contract
Developer 1: Needs to regenerate or adjust related backend contract
→ WAIT FOR CONTRACT TO BE FROZEN
```

Developer 1 must also pause dependent work when:

- `main` is broken
- integration conflict has not been understood
- the schema migration is changing underneath an active backend implementation
- a required API contract is not finalized
- the other developer is actively editing the same shared file

### Communication

Use:

```text
DEPENDENCY NOTICE

I am changing:
<schema/API/auth/ML contract>

Affected feature:
<feature>

Expected impact:
<impact>

Please do not build against the old behavior until this is merged.
```

---

# 6. Phase-by-Phase Responsibilities

| Phase | Developer 1 | Developer 2 | Simultaneous? | Integration Gate |
|---|---|---|---|---|
| 1. Repository/setup | Backend structure, Python setup, environment conventions | React structure, frontend setup | YES | Root config agreed |
| 2. Database/schema | Supabase schema, migrations, RLS design | Review schema from consumer perspective | LIMITED | Migration + access rules tested |
| 3. Authentication/RLS | Backend auth checks, role logic, RLS | Auth UI, protected routes, session handling | YES after contract | Real Mother/ASHA access tests |
| 4. Backend/API | Health, symptoms, predictions, alerts, visits, follow-ups | Build API consumer services and mock contract tests | YES | API contract verified |
| 5. ML pipeline | Dataset, features, models, evaluation, versioning | Risk UI using frozen prediction contract | YES | Prediction API + model tests |
| 6. Safety/AI | Safety engine, decision layer, LLM/agent backend | AI chat/agent UI integration | YES after contracts | Safety tests + authorized tool tests |
| 7. Voice | AI4Bharat backend pipeline/interface | Voice UI, recording, confirmation, playback | YES after voice contract | End-to-end voice test |
| 8. Full integration | Backend/frontend compatibility support | Frontend/backend integration | NO for contract-breaking changes | Full smoke test |
| 9. E2E testing | API, RLS, ML, safety, backend tests | UI, E2E, accessibility and frontend tests | YES | Full regression passes |
| 10. Bug fixing | Backend/data/ML/security fixes | Frontend/integration fixes | YES if isolated | Main remains green |
| 11. Stabilization/deployment | Backend deployment, database verification, observability | Frontend deployment and final UX verification | YES | Release checklist complete |

---

# 7. Integration Protocol

For Developer 1:

```text
Complete backend/data/AI work
        ↓
Run tests
        ↓
Commit
        ↓
Push feature/d1/...
        ↓
Open PR into main
        ↓
Developer 2 reviews compatibility
        ↓
Resolve comments/conflicts
        ↓
CI/tests pass
        ↓
Both confirm readiness
        ↓
Merge
        ↓
Smoke-test main
        ↓
Both pull main
```

After merge:

```bash
git checkout main
git pull --ff-only origin main
```

If starting another feature:

```bash
git switch -c feature/d1/<next-phase>-<task>
```

Do not continue a stale feature branch for the next phase when the previous integration changed its base significantly.

---

# 8. Conflict Prevention

Developer 1 reduces conflicts by:

### File ownership

Keep backend/data/ML/safety changes inside owned directories.

### Contract freeze

Write down API/database/ML contracts before the dependent developer builds against them.

### Pull/rebase timing

Before opening a PR:

```bash
git fetch origin
git rebase origin/main
```

Only do this on your own feature branch.

### Small commits

Use focused commits so a conflict can be isolated.

### No unrelated cleanup

Do not rename, format, or reorganize files unrelated to the task.

### Migration discipline

Never silently change a database migration that is already integrated. Create a new migration when changing an existing production/integration state.

### API discipline

If a response field changes, treat it as a contract change, not a private backend refactor.

---

# 9. Conflict Resolution

When Git reports a conflict:

```bash
git status
git diff
```

Inspect each conflict marker:

```text
<<<<<<<
current content
=======
incoming content
>>>>>>>
```

Do not automatically choose:

```text
ours
```

or:

```text
theirs
```

Instead determine:

1. What each version is trying to accomplish.
2. Whether one version contains newer contract/schema behavior.
3. Whether both changes are required.
4. Whether the merge changes authentication, RLS, API, ML, or safety behavior.

After resolving:

```bash
git add <resolved-files>
git rebase --continue
```

or, if merging:

```bash
git commit
```

Then run:

```bash
git status
pytest
```

plus the relevant frontend/build/integration tests.

Only push after testing.

If you cannot explain the correct merged behavior, stop and coordinate with Developer 2 before completing the merge.

---

# 10. Developer 1 Phase-Completion ChatGPT Prompt

Use this at every phase:

```text
I am Developer 1 working on MaternAI.

Phase:
<phase>

My role:
Backend / Database / ML / Safety / AI

Completed work:
<details>

Files changed:
<files>

Git branch:
<branch>

Git commits:
<commits>

Database/schema changes:
<details or none>

API changes:
<details or none>

Authentication/RLS changes:
<details or none>

ML input/output changes:
<details or none>

Safety-rule changes:
<details or none>

LLM/agent/voice backend changes:
<details or none>

Tests performed and results:
<tests>

Known issues:
<issues>

Other developer dependencies:
<dependencies>

Review this phase against the MaternAI master project documentation.

Check:
1. Implementation completeness
2. Architecture correctness
3. Database/schema compatibility
4. API contract compatibility
5. Authentication and RLS
6. ML input/output compatibility
7. Safety-layer behavior
8. LLM/agent boundaries
9. Voice architecture compatibility
10. Frontend/backend integration risks
11. Test coverage
12. Security gaps
13. Performance or reliability risks
14. Exact fixes required
15. Main-branch readiness
16. Next-phase readiness

Do not invent missing facts. Mark uncertain items as needing verification.
```

---

# 11. Developer 1 Antigravity Fix Prompt

```text
I am Developer 1 fixing a MaternAI issue found during a ChatGPT phase review.

Issue:
<issue>

Phase:
<phase>

Relevant files:
<files>

Expected behavior:
<expected>

Observed behavior:
<observed>

Required fix:
<fix>

Before editing:
- Inspect the current repository.
- Read the existing implementation.
- Verify the reported issue against the actual code.
- Check related PostgreSQL/Supabase schema and RLS.
- Check FastAPI request/response contracts.
- Check ML input/output contracts.
- Check safety-rule behavior.
- Check authentication and authorization.

Then make the smallest safe change.

Rules:
- Preserve working functionality.
- No unrelated refactoring.
- No whole-project rewrites.
- Never expose secrets.
- Never bypass RLS or backend authorization.
- Do not change a contract unless the fix requires it.
- Do not modify Developer 2's owned area unless integration requires it and you explain why.

After editing:
1. Run relevant tests.
2. Check Python errors/imports.
3. Check API compatibility.
4. Check database compatibility.
5. Check auth/RLS if relevant.
6. Run regression tests for the affected feature.
7. List exact changed files.
8. List tests and results.
9. List remaining issues.

Do not begin by changing code. Inspect first.
```

---

# 12. Developer 1 Daily Checklist

```text
[ ] I am on a feature/d1 branch, not main.
[ ] I pulled the latest main before starting independent work.
[ ] My task belongs to my ownership area.
[ ] No unfrozen API/schema/ML contract blocks me.
[ ] I avoided unrelated files.
[ ] I committed a logical change.
[ ] I ran relevant tests.
[ ] I pushed my branch.
[ ] I informed Developer 2 about shared contract changes.
[ ] I did not force-push.
```

---

# 13. Backend/Data/AI Integration Gate

Before requesting merge, Developer 1 must confirm:

```text
[ ] Database migration reviewed
[ ] RLS policy tested
[ ] API request/response documented
[ ] Authentication checked
[ ] ML model contract stable
[ ] Safety behavior tested
[ ] Audit logging checked where applicable
[ ] Relevant tests passing
[ ] No secrets committed
[ ] No unrelated files changed
```

Then open the PR.


## Shared Team Workflow — MUST MATCH IN BOTH DEVELOPER FILES

### Branch model

Use `main` as the only stable branch.

Do **not** maintain permanent `developer-1` or `developer-2` branches. Each developer creates a short-lived feature branch from the latest `main`:

```text
main
├── feature/d1/<phase>-<task>
├── feature/d2/<phase>-<task>
└── ...
```

Examples:

```text
feature/d1/database-schema
feature/d1/risk-api
feature/d1/ml-pipeline

feature/d2/mother-dashboard
feature/d2/asha-dashboard
feature/d2/voice-ui
```

Rules:

- Never develop directly on `main`.
- Never push unfinished work to `main`.
- Never force-push `main`.
- Never force-push another developer's branch.
- A feature branch should represent one logical task.
- Delete merged feature branches after integration.
- Start every new feature branch from the latest tested `main`.

### Ownership matrix

| Area | Developer 1 | Developer 2 | Coordination |
|---|---|---|---|
| Backend/FastAPI | Primary owner | Consumer/reviewer | API changes announced |
| PostgreSQL/Supabase schema | Primary owner | Review/read-only | Schema changes announced before implementation |
| RLS policies | Primary owner | Review/test | Auth/data-access changes coordinated |
| ML pipeline | Primary owner | Review/integration | Input/output contract frozen before frontend integration |
| Safety engine | Primary owner | Review | Safety behavior changes require coordination |
| Mother frontend | Review/API consumer | Primary owner | Contract-driven |
| ASHA frontend | Review/API consumer | Primary owner | Contract-driven |
| Frontend routing/layout | Review | Primary owner | Coordinate shared app files |
| Voice backend integration | Primary owner | UI integration | Contract-driven |
| Voice UI | API consumer | Primary owner | Coordinate interface |
| Local LLM backend | Primary owner | UI consumer | Prompt/API changes announced |
| AI Agent backend/tools | Primary owner | UI consumer | Tool contracts coordinated |
| Agent UI | Review | Primary owner | Contract-driven |
| Tests | Backend/unit/security owner | Frontend/E2E owner | Both run full regression before merge |
| README/root config | Coordinate | Coordinate | One owner per change |
| `.env.example` | Coordinate | Coordinate | Never commit secrets |
| Shared types/contracts | Primary owner by contract | Consumer | Change requires announcement |
| Deployment | Primary owner | Review/verify | Final integration together |

### Shared file categories

#### Primarily owned by Developer 1

```text
backend/
ml/
supabase/migrations/
backend safety logic
backend LLM/agent services
backend tests
database/RLS definitions
```

#### Primarily owned by Developer 2

```text
frontend/src/components/
frontend/src/pages/
frontend/src/layouts/
frontend/src/hooks/
frontend/src frontend services
frontend UI tests
```

#### Shared — coordinate BEFORE editing

```text
frontend/src/App.*
frontend/src/main.*
frontend routing configuration
package.json / lockfiles
backend/app/main.py
API contract documentation
shared schema/type definitions
.env.example
README.md
deployment configuration
CI configuration
```

If a shared file must be edited, post a short message first:

```text
SHARED FILE NOTICE
File:
Reason:
Expected change:
Branch:
Does this alter an API/schema/route?
```

The second developer waits until the first finishes the shared-file edit, pulls it through an integration merge, or agrees on a single coordinated edit.

### Main branch rules

`main` must always be treated as stable and integration-ready.

Never merge:

- unfinished features
- known failing tests
- unresolved merge conflicts
- unreviewed database migrations
- undocumented API-breaking changes
- secrets
- code that bypasses authentication/RLS
- changes that break the ML input/output contract

Integration happens through a pull request.

The default rule is:

```text
Feature branch
    ↓
Local tests
    ↓
Push branch
    ↓
PR into main
    ↓
Other developer reviews
    ↓
CI/tests
    ↓
Merge
    ↓
Both developers synchronize
```

### Synchronization rules

Before starting new work:

```bash
git status
git fetch origin
git checkout main
git pull --ff-only origin main
git switch -c feature/<developer>/<phase>-<task>
```

Never use `git reset --hard`, `git clean -fd`, or force-push merely to make your branch match remote unless the team has explicitly decided to discard local work.

If local work exists:

```bash
git status
git add <specific-files>
git commit -m "wip: save safe checkpoint"
```

or stash it when committing is inappropriate:

```bash
git stash push -u -m "temporary checkpoint"
```

A safer sync pattern for an existing feature branch is:

```bash
git fetch origin
git rebase origin/main
```

Only rebase a branch that belongs solely to you and has not been rewritten by someone else.

### Integration checkpoints

At the end of every major phase:

1. Developer finishes the phase work.
2. Run relevant local tests.
3. Commit logical changes.
4. Push feature branch.
5. Open a PR into `main`.
6. Other developer reviews compatibility.
7. Resolve review comments/conflicts.
8. CI and required tests pass.
9. Merge the PR.
10. Run a smoke test on updated `main`.
11. Both developers pull the new `main`.
12. Only then start the next phase.

### Who merges?

The developer who owns the feature creates the PR.

The other developer performs the compatibility review.

Either developer may click Merge **only after both have explicitly confirmed readiness**, unless the team has previously delegated merge authority for that phase.

No one merges a PR while the other developer is actively changing the same contract, schema, authentication behavior, or shared files.

### Contract-first rule

Before dependent implementation begins, freeze the contract.

For example:

```text
Database schema
    ↓
API request/response contract
    ↓
Frontend implementation
```

or:

```text
ML input/output contract
    ↓
Backend prediction API
    ↓
Frontend risk UI
```

If the producer changes a contract:

1. Announce the change.
2. Update the contract documentation.
3. Tell the consumer exactly what changed.
4. Consumer updates their branch from latest `main`.
5. Consumer adapts before continuing dependent work.

### Wait vs. work decision rule

Both developers can work simultaneously when they are changing separate owned areas and consuming an agreed contract.

```text
D1: FastAPI prediction endpoint
D2: Mother risk-result UI using frozen response contract
→ WORK SIMULTANEOUSLY
```

A developer must wait when the other developer is changing the contract they currently depend on:

```text
D1: Changes prediction response shape
D2: Building UI against that response
→ D2 WAITS
```

Similarly:

```text
D1: Changes database columns used by D2
D2: Depends on those columns
→ D2 WAITS
```

But:

```text
D1: Improves ML model internals without changing API output
D2: Builds dashboard UI
→ BOTH CONTINUE
```

### Daily workflow

```text
1. Check team status / current phase.
2. git fetch origin
3. Synchronize with latest main if starting new work.
4. Confirm task is inside your ownership area.
5. Check whether the task depends on an unfrozen schema/API/ML contract.
6. If independent, work in parallel.
7. If dependent on a changing contract, wait or coordinate.
8. Commit logical changes.
9. Run tests.
10. Push feature branch.
11. Tell the other developer about shared-file, schema, API, auth, or ML-contract changes.
12. Open/update PR when the feature is integration-ready.
```

### Commit convention

Use:

```text
feat:
fix:
refactor:
docs:
test:
chore:
```

Examples:

```text
feat: add maternal health record API
feat: add mother risk assessment page
fix: enforce ASHA assignment authorization
test: add prediction API validation tests
docs: define risk response contract
chore: update FastAPI dependencies
```

A good commit:

- has one logical purpose
- is reasonably small
- contains tests where relevant
- does not mix unrelated formatting/refactoring

Avoid:

```text
feat: backend + frontend + database + random cleanup
```

### PR template

```text
## Phase
<phase number/name>

## Feature
<what changed>

## Owner
Developer 1 / Developer 2

## Files changed
<list>

## Dependency on other developer
<none / details>

## Database changes
<none / migration details>

## API changes
<none / endpoints and contracts>

## Authentication / RLS changes
<none / details>

## ML changes
<none / input-output contract details>

## Safety changes
<none / rule or decision-layer details>

## Tests
<tests and results>

## Integration notes
<special steps>

## Known issues
<none / details>

## Ready to merge?
YES / NO
```

### Phase completion reporting

At the end of every phase, both developers use the following ChatGPT review prompt, adapted to their developer number:

```text
I am Developer <1 or 2> working on MaternAI.

Phase:
<phase>

My role:
<role>

Completed work:
<details>

Files changed:
<files>

Git branch:
<branch>

Git commits:
<commits>

Database/schema changes:
<details or none>

API changes:
<details or none>

Authentication/RLS changes:
<details or none>

ML input/output changes:
<details or none>

Safety-rule changes:
<details or none>

Frontend changes:
<details or none>

Voice/LLM/agent changes:
<details or none>

Tests performed and results:
<tests>

Known issues:
<issues>

Other developer dependencies:
<dependencies>

Review this phase against the MaternAI master plan and generate:

1. Implementation summary
2. Completed work
3. Incomplete work
4. Architecture deviations
5. Integration risks
6. Database/schema compatibility issues
7. API contract compatibility issues
8. Authentication/RLS/security concerns
9. ML input/output compatibility concerns
10. Safety-layer concerns
11. Frontend/backend integration concerns
12. Voice/LLM/agent concerns
13. Testing gaps
14. Bugs or likely bugs
15. Exact required fixes
16. Whether the phase is ready to integrate into main
17. What the other developer must know before continuing
18. Next-phase readiness

Do not invent missing facts. Distinguish confirmed issues from risks or recommendations.
```

### Antigravity fix prompt

Use this only after the phase review identifies actual fixes:

```text
I am fixing a MaternAI issue identified during the phase review.

Reported issue:
<exact issue>

Affected phase:
<phase>

Relevant files:
<files>

Expected behavior:
<expected behavior>

Current observed behavior:
<observed behavior>

Required fix:
<fix>

Before changing code:

1. Inspect the existing repository and current implementation.
2. Identify how the relevant code fits into the MaternAI architecture.
3. Verify the issue against the actual code.
4. Check related API, database, authentication/RLS, ML, safety, voice, LLM, or frontend contracts.
5. Identify the smallest safe change.

Then:

- Make only the necessary changes.
- Preserve existing working functionality.
- Do not perform unrelated refactoring.
- Do not rewrite whole files unless necessary.
- Do not bypass PostgreSQL RLS or backend authorization.
- Do not expose service-role or other secrets.
- Do not change API contracts, database schema, authentication behavior, ML contracts, or shared types unless the fix requires it.
- Do not modify the other developer's owned area unless integration genuinely requires it and the reason is stated.

After changing code:

1. Run relevant unit/API/frontend tests.
2. Check TypeScript/Python errors.
3. Check imports and build output.
4. Check API compatibility.
5. Check database/migration compatibility.
6. Check authentication/RLS behavior where relevant.
7. Run the smallest useful regression test set.
8. Report exactly which files changed.
9. Report tests performed and results.
10. Report any remaining issue or uncertainty.

Do not start by changing code before inspecting it.
```

### Emergency fix workflow

If `main` breaks after integration:

```text
STOP NEW FEATURE WORK
        ↓
Identify breaking PR/commit
        ↓
Reproduce issue
        ↓
Determine fix vs revert
        ↓
Create controlled hotfix branch
        ↓
Fix / revert
        ↓
Run regression tests
        ↓
Merge controlled fix
        ↓
Smoke-test main
        ↓
Both developers synchronize
        ↓
Resume feature work
```

Ownership rule:

- Backend/database/auth/RLS/ML/safety break → Developer 1 leads the fix.
- Frontend/routing/UI break → Developer 2 leads the fix.
- Cross-layer integration break → both developers work together.
- Unknown cause → pause feature work until root cause is isolated.

Do not immediately revert if the problem can be diagnosed safely. Do not keep adding features while `main` is broken.

### Final integration

```text
Feature freeze
    ↓
Final schema/migration verification
    ↓
Final API contract verification
    ↓
Authentication + RLS verification
    ↓
ML pipeline verification
    ↓
Safety-rule verification
    ↓
Frontend/backend E2E verification
    ↓
Voice verification
    ↓
Security checks
    ↓
Full test suite
    ↓
Final synchronization
    ↓
Final main branch verification
    ↓
Release/tag if appropriate
```


