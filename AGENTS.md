# AGENTS.md

## Project execution baseline

- Prefer minimal, explicit changes.
- Never guess project structure, contracts, or naming.
- Preserve existing architecture boundaries.
- Do not mix page entry, workflow logic, provider logic, and persistence logic in one file.
- Before changing code, identify the files to be created or modified.

## React app / feature-page conventions

### 1. Feature semantics first

- Organize React page code by feature directory, not by repeating the same feature prefix in every filename.
- Shared naming must move up to the directory layer.
- File names should only describe the local responsibility inside that feature.

Preferred example:

```text
src/pages/chat-page/
  index.tsx
  index.test.tsx
  contracts.ts
  components/
    Shell.tsx
  hooks/
    useBranding.ts
    useRuntimeStream.ts
  config/
    constants.ts
    normalizers.ts
```

Avoid patterns like:

- `ChatPageShell.tsx`
- `useChatPageBranding.ts`
- `useChatPageRuntimeStream.ts`
- `chatPageConfig.ts`

when the enclosing directory already expresses `chat-page`.

### 2. Page entry responsibility

- `index.tsx` is the page entry only.
- Page entry should do wiring/composition only.
- Do not bury workflow logic, stream bridging, normalization, or heavy assembly directly inside the page entry.
- Render output should stay declarative.

### 3. Required subdirectory semantics

- `components/`: page-local presentation pieces only
- `hooks/`: page-local composition, wiring, runtime bridge hooks
- `config/`: constants, defaults, normalizers
- `contracts.ts`: feature-local types/contracts export surface

### 4. JSX hygiene rules

Do not inline unstable values in the main render body when they are passed to children.

Always extract these first:

- handlers/callbacks → `useCallback`
- object props → `useMemo`
- array props → `useMemo`
- runtime bridge values / assembled props → explicit local variables or hooks outside JSX

Examples of values that must not be directly inlined into JSX:

- `onModeChange={(...) => ...}`
- `identityContext={{ ... }}`
- array literals passed as props
- ad-hoc runtime assembly expressions passed directly to child components

### 5. Stability and robustness rules

- Any prop that may participate in child memoization, shallow comparison, or effect dependencies must be kept as a stable reference.
- Do not assume inline object/function literals are harmless.
- If a child component receives a structured prop, prefer a named memoized value.

### 6. Helper/doc comment rules

When extracting a stable helper value, callback, or bridge in page entry code:

- add short helper-style doc comments when the reason is not obvious
- explain why the value exists and why it must not be inlined
- prefer maintenance-oriented comments over trivial line-by-line narration

Good comment intent:

- explain boundary
- explain stability requirement
- explain synchronization reason

Bad comment intent:

- restate obvious syntax
- narrate what a single line literally does

### 7. Tests

- Feature page tests should live beside the feature entry as `index.test.tsx` when the feature entry is `index.tsx`.
- Keep test import paths aligned with the feature directory entry, e.g. `@/pages/chat-page`.

### 8. Default expectation for future changes

For this repository, all future React/page work should follow this standard by default unless the user explicitly asks for a different structure.

## Backend app / feature conventions

### 1. Feature semantics first

- Organize backend code by feature/domain directory before repeating the same business prefix in every filename.
- Shared business naming must move up to the directory layer.
- File names should only describe the local responsibility inside that feature.

Preferred example:

```text
backend/app/chat_session/
  api.py
  contracts.py
  assembler.py
  repository.py
  usecases/
    create.py
    run.py
    retry.py
  workflows/
    requirement_collection.py
    sourcing.py
  domain/
    readiness.py
    policies.py
    next_actions.py
  adapters/
    llm.py
    search.py
```

Avoid patterns like:

- `chat_session_service.py`
- `chat_session_repository.py`
- `chat_session_controller.py`
- `chat_session_utils.py`

when the enclosing directory already expresses `chat_session`.

### 2. Backend entry responsibility

- `api.py` / route / controller / resolver is the backend entry only.
- Entry files must stay thin: input parsing, basic validation, calling application layer, returning response.
- Do not bury workflow logic, business decisions, provider details, persistence details, or large mapping logic directly inside backend entry files.

### 3. Required layer semantics

- `api.py`: transport boundary only
- `contracts.py`: request/response/event/schema single source of truth
- `assembler.py`: structure assembly only, no business decision logic
- `usecases/`: application orchestration entry points
- `workflows/`: explicit multi-step flow progression
- `domain/`: pure business rules, policies, readiness, eligibility, next-actions
- `repository.py` / `repositories/`: persistence only
- `adapters/` / `providers/`: external systems only

### 4. Thin-entry rule

Backend entry files must not inline:

- business if/else trees
- multi-step workflow progression
- provider SDK payload composition
- persistence orchestration
- large ad-hoc mapping blocks
- nested dict payload assembly for downstream business logic

If a route/controller starts assembling large command payloads or making business decisions, extract a contract/usecase/helper with a clear ownership boundary.

### 5. Explicit orchestration rule

- Multi-step application logic must have an explicit owner in `usecases/` or `workflows/`.
- Do not scatter orchestration across route files, repositories, adapters, or generic helpers.
- Do not hide workflow progression inside provider callbacks or persistence methods.

### 6. Domain purity rule

- Domain rules must live in `domain/`, `policies.py`, or similarly explicit domain modules.
- Domain logic must not depend directly on transport layer, framework request objects, ORM session objects, or provider SDK payloads.
- Repositories must not own business-state progression.
- Providers must not decide product/domain truth.

### 7. Contracts-first rule

- Use explicit DTO/schema/contracts before implementation details.
- Prefer typed contracts over loose dict passing.
- Request/response/event/patch payloads must have an explicit schema owner.
- Avoid `dict[str, Any]` drift between layers unless the user explicitly asks for a temporary spike.

### 8. Provider normalization rule

- External provider output must be normalized before entering domain logic or application truth.
- Never let raw provider payload become authoritative state directly.
- Required flow:

```text
provider output -> normalize -> contract/dto -> usecase/domain
```

### 9. Persistence boundary rule

- Repository layer handles data access only.
- Repository layer must not silently apply business policy, workflow transitions, or presentation projection logic.
- Do not mix SQL/ORM decisions with domain decisions in one file.

### 10. Backend helper/doc comment rule

When extracting an application helper, workflow bridge, normalization function, or state-sync helper:

- add short helper-style doc comments when the reason is not obvious
- explain why the helper exists and what boundary it protects
- explain why the logic should not be inlined into route/usecase/provider code
- prefer maintenance-oriented comments over obvious line narration

### 11. File and naming discipline

- Avoid god services, god utils, and catch-all helpers.
- Avoid generic names like `utils.py`, `helpers.py`, `common.py`, `manager.py`, `service.py` unless the file has a single, self-evident role.
- If many files repeat the same business prefix, move that prefix to a feature directory.
- Keep one file focused on one role: route, orchestration, policy, repository, adapter, contract, or assembler.

### 12. Default expectation for future backend changes

For this repository, all future backend work should follow this standard by default unless the user explicitly asks for a different structure.
