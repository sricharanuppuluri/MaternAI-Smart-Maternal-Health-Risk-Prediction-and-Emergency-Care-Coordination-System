# MATERN_AI_DEVELOPER_2_WORKFLOW.md

## Purpose

This is the operating manual for **Developer 2** in the two-person MaternAI team.

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

# 1. Developer 2 Role

## Primary ownership

Developer 2 is the primary owner of MaternAI's:

### Frontend and UX layer

- React application UI
- TypeScript frontend
- mother portal
- ASHA portal
- dashboard layouts
- forms
- risk-result presentation
- alert queue UI
- follow-up UI
- longitudinal risk timeline
- frontend routing
- frontend API service layer
- client-side voice interaction
- agent/chat UI

### Frontend quality

- responsive behavior
- mobile-first mother experience
- accessibility
- frontend validation
- loading/error/empty states
- frontend tests
- end-to-end user flows

Developer 2 consumes backend contracts rather than redefining them independently.

## Primary directories

Prefer working primarily in:

```text
frontend/
```

and frontend-related tests/documentation.

## Developer 2 should avoid

Do not make casual changes in:

```text
backend/
ml/
supabase/migrations/
```

unless a frontend integration issue genuinely requires coordinated backend work.

Do not change database schema, RLS, ML contracts, or safety rules without Developer 1 coordination.

## Developer 2's rule

> Build against frozen, documented contracts. Do not silently create frontend assumptions about database fields, risk outputs, authentication roles, or backend behavior.

---

# 2. Branch Strategy

Use short-lived feature branches.

Examples:

```text
feature/d2/auth-ui
feature/d2/mother-dashboard
feature/d2/asha-dashboard
feature/d2/risk-timeline
feature/d2/voice-ui
feature/d2/agent-ui
```

Start from the latest `main`.

```bash
git status
git fetch origin
git checkout main
git pull --ff-only origin main
git switch -c feature/d2/<phase>-<task>
```

Do not start a new branch from Developer 1's feature branch unless both developers explicitly agree that temporary dependency is necessary.

---

# 3. Push Rules

Push when:

- a logical frontend feature is complete
- a safe checkpoint has been committed
- integration is ready
- the work session ends with a usable checkpoint

Before pushing:

```bash
git status
git diff
git diff --cached
```

Run appropriate tests/build checks.

Then:

```bash
git add <specific-files>
git commit -m "feat: <description>"
git push -u origin feature/d2/<phase>-<task>
```

Never:

- push directly to `main`
- push known broken code intended for immediate integration
- force-push shared branches
- rewrite Developer 1's commits
- include unrelated refactoring in the feature commit

---

# 4. When Developer 2 Can Work Simultaneously

Examples:

```text
Developer 1: FastAPI health endpoint
Developer 2: Mother health-entry page using frozen request contract
→ WORK SIMULTANEOUSLY
```

```text
Developer 1: ML model training
Developer 2: ASHA dashboard and alert layout
→ WORK SIMULTANEOUSLY
```

```text
Developer 1: Safety engine internals
Developer 2: Frontend navigation and responsive styling
→ WORK SIMULTANEOUSLY
```

```text
Developer 1: Prediction API with agreed response
Developer 2: Risk-result page consuming that response
→ WORK SIMULTANEOUSLY
```

## Developer 2 must coordinate first when

- changing frontend auth assumptions because backend auth behavior is changing
- needing a new database field
- expecting a changed API response/request
- changing route behavior that affects shared app entry points
- changing shared types
- changing environment/config files
- changing API service conventions shared with other features
- changing how safety alerts are represented
- changing ML output presentation based on a changed model contract

---

# 5. When Developer 2 Must Wait

Developer 2 waits when Developer 1 is changing a contract the frontend depends on.

Examples:

```text
Developer 1: Changes prediction response shape
Developer 2: Building risk-result UI
→ D2 WAITS
```

```text
Developer 1: Changes database schema fields consumed by frontend
Developer 2: Building forms using those fields
→ D2 WAITS
```

```text
Developer 1: Changes authentication/role semantics
Developer 2: Implementing protected routes
→ COORDINATE FIRST
```

Developer 2 must also pause dependent work when:

- `main` is broken
- a required API contract is not finalized
- a shared file is actively being changed
- the backend contract has materially changed but the consumer update is not yet merged

### Communication

Use:

```text
DEPENDENCY NOTICE

I need this backend contract:
<endpoint/field/auth behavior>

Current expected behavior:
<details>

I will continue once the contract is frozen.
```

---

# 6. Phase-by-Phase Responsibilities

| Phase | Developer 1 | Developer 2 | Simultaneous? | Integration Gate |
|---|---|---|---|---|
| 1. Repository/setup | Backend structure, Python setup, environment conventions | React structure, frontend setup | YES | Root config agreed |
| 2. Database/schema | Supabase schema, migrations, RLS design | Review schema from consumer perspective | LIMITED | Migration + access rules tested |
| 3. Authentication/RLS | Backend auth checks, role logic, RLS | Auth UI, protected routes, session handling | YES after contract | Real Mother/ASHA access tests |
| 4. Backend/API | Health, symptoms, predictions, alerts, visits, follow-ups | API consumer service layer, loading/error states, mock contract tests | YES | API contract verified |
| 5. ML pipeline | Dataset, features, models, evaluation, versioning | Risk UI using frozen prediction contract | YES | Prediction API + model tests |
| 6. Safety/AI | Safety engine, decision layer, LLM/agent backend | Chat/agent UI integration | YES after contracts | Safety tests + authorized tool tests |
| 7. Voice | AI4Bharat backend pipeline/interface | Recording, confirmation, language controls, playback UI | YES after voice contract | End-to-end voice test |
| 8. Full integration | Backend/frontend compatibility support | Frontend/backend integration | NO for contract-breaking changes | Full smoke test |
| 9. E2E testing | API, RLS, ML, safety, backend tests | UI, E2E, accessibility and frontend tests | YES | Full regression passes |
| 10. Bug fixing | Backend/data/ML/security fixes | Frontend/integration fixes | YES if isolated | Main remains green |
| 11. Stabilization/deployment | Backend deployment, database verification, observability | Frontend deployment and final UX verification | YES | Release checklist complete |

---

# 7. Integration Protocol

For Developer 2:

```text
Complete frontend/UX work
        ↓
Run frontend tests/build
        ↓
Commit
        ↓
Push feature/d2/...
        ↓
Open PR into main
        ↓
Developer 1 reviews compatibility
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
git switch -c feature/d2/<next-phase>-<task>
```

Do not continue a stale feature branch for the next phase when the previous integration changed its base significantly.

---

# 8. Conflict Prevention

Developer 2 reduces conflicts by:

### File ownership

Keep UI work inside owned frontend directories.

### Contract-first development

Do not guess backend request/response formats.

### Pull/rebase timing

Before opening a PR:

```bash
git fetch origin
git rebase origin/main
```

Only do this on your own feature branch.

### Small commits

Use focused commits.

### No unrelated cleanup

Do not reformat or reorganize backend/shared files while implementing UI work.

### Shared routing discipline

`App.*`, route registration, and root entry files are high-conflict. Coordinate before editing them.

### Dependency discipline

If Developer 1 changes an endpoint:

1. Wait for the new contract to be documented.
2. Pull the integrated change.
3. Update the frontend consumer.
4. Run integration tests.

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

Do not blindly choose:

```text
ours
```

or:

```text
theirs
```

Determine:

1. What each version changes.
2. Whether the backend contract is newer.
3. Whether UI behavior must preserve both changes.
4. Whether authentication/routing behavior is affected.
5. Whether the conflict changes API or shared type assumptions.

After resolving:

```bash
git add <resolved-files>
git rebase --continue
```

or:

```bash
git commit
```

Then run:

```bash
git status
npm run build
npm test
```

plus the relevant backend/integration tests.

Only push after testing.

If you cannot determine the correct behavior, stop and coordinate with Developer 1.

---

# 10. Developer 2 Phase-Completion ChatGPT Prompt

Use this at every phase:

```text
I am Developer 2 working on MaternAI.

Phase:
<phase>

My role:
Frontend / UX / Voice UI / Agent UI

Completed work:
<details>

Files changed:
<files>

Git branch:
<branch>

Git commits:
<commits>

Database/schema dependencies:
<details or none>

API dependencies:
<details or none>

Authentication/RLS dependencies:
<details or none>

ML input/output dependencies:
<details or none>

Safety-rule UI behavior:
<details or none>

Frontend changes:
<details>

Voice/LLM/agent UI changes:
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
2. UI/UX correctness
3. API contract compatibility
4. Database/schema assumptions
5. Authentication/session/role behavior
6. RLS-related frontend assumptions
7. ML result compatibility
8. Safety-message correctness
9. Voice architecture compatibility
10. LLM/agent UI boundaries
11. Frontend/backend integration risks
12. Responsive/accessibility concerns
13. Test coverage
14. Security gaps
15. Exact fixes required
16. Main-branch readiness
17. What Developer 1 must know before continuing
18. Next-phase readiness

Do not invent missing facts. Mark uncertain items as needing verification.
```

---

# 11. Developer 2 Antigravity Fix Prompt

```text
I am Developer 2 fixing a MaternAI issue found during a ChatGPT phase review.

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
- Read the existing frontend implementation.
- Verify the issue against the actual code.
- Read the current API contract before changing consumers.
- Check authentication/session behavior.
- Check assumptions about PostgreSQL/Supabase data.
- Check ML prediction response structure.
- Check safety-alert semantics.
- Check voice/LLM/agent interfaces if relevant.

Then make the smallest safe change.

Rules:
- Preserve existing working functionality.
- No unrelated refactoring.
- No whole-project rewrites.
- Do not invent API fields.
- Do not bypass backend authorization or RLS.
- Do not expose secrets.
- Do not change backend contracts unless coordinated with Developer 1.
- Do not modify Developer 1's owned area unless integration requires it and you explain why.

After editing:
1. Run frontend tests.
2. Run build/type checks.
3. Check imports.
4. Check API compatibility.
5. Check authentication behavior.
6. Check affected user flows.
7. Run regression tests for the affected feature.
8. List exact changed files.
9. List tests and results.
10. List remaining issues.

Do not begin by changing code. Inspect first.
```

---

# 12. Developer 2 Daily Checklist

```text
[ ] I am on a feature/d2 branch, not main.
[ ] I pulled the latest main before starting independent work.
[ ] My task belongs to my ownership area.
[ ] I know the current API/schema/ML contracts.
[ ] No unfrozen backend dependency blocks me.
[ ] I avoided unrelated shared files.
[ ] I committed a logical change.
[ ] I ran build/tests.
[ ] I pushed my branch.
[ ] I informed Developer 1 about contract/shared-file concerns.
[ ] I did not force-push.
```

---

# 13. Frontend/Backend Integration Gate

Before requesting merge, Developer 2 must confirm:

```text
[ ] API request/response assumptions match the current contract
[ ] Authentication/session behavior tested
[ ] Role-based routes tested
[ ] Mother cannot see ASHA-only UI
[ ] ASHA UI only requests authorized assigned-mother data
[ ] Loading/error/empty states handled
[ ] Risk categories displayed correctly
[ ] Safety alerts are not downgraded in UI
[ ] Responsive behavior checked
[ ] Relevant tests/build passing
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


