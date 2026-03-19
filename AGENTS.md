# MultiMultiAgent-ArchiLLM Repository Knowledge

## Project Overview
This repo evaluates LLM agents on MERODE-based software engineering tasks.
Each project under `projects/` has a backend (Spring Boot) and test artifacts.

## EasyBank Project

### Backend (`projects/easybank/backend`)
- Spring Boot 3.2, Java 21, Maven, H2 in-memory database
- Entities: `Accountholder` (EXISTS → ENDED), `Account` (FROZEN → OPEN ↔ FROZEN → CLOSED → ENDED)
- REST API at `/api/accountholders` and `/api/accounts`
- Business rule: open account cannot be ended directly (must be frozen first, then closed)
- **Known issue**: Lombok `@Data` on `Account`/`Accountholder` entities creates circular `hashCode()`/`toString()` between bidirectional JPA relationships. This causes 500 errors when calling endpoints with no `Content-Type` header (Spring fails to resolve the request body properly). The backend works correctly when requests carry `Content-Type: application/json`.

### Test Application (`run/easybank/test`)
- Standalone Maven Spring Boot test project (NOT inside the backend project)
- Embeds the backend source via `build-helper-maven-plugin` (adds `../backend/src/main/java` as a compile source)
- Run with: `mvn test` from `run/easybank/test/`
- Generates `report.json` and `report.html` in `run/easybank/test/` (via `reports.output.dir` system property set in Surefire config)
- 57 test cases covering 11 MERODE FSM coverage criteria (CO, EO, AT, ALFP, AOLP, AS, AEM, GEN, TP, AL, AM)
- All 57 tests pass using MockMvc against an embedded H2-backed Spring context

### Key Technical Decisions
1. **Backend source integration**: Use `build-helper-maven-plugin`'s `add-source` goal to include `../backend/src/main/java` in the test project's compilation. This avoids needing a JAR or multi-module setup.
2. **Resources**: Use `build-helper-maven-plugin`'s `add-resource` goal to pull in backend `application.properties`; test-specific properties in `src/test/resources/application.properties` override it (H2 console disabled, separate DB name).
3. **Surefire includes**: Added `**/*Suite.java` pattern so `EasybankTestSuite` is picked up by Maven Surefire (default patterns only match `*Test`, `*Tests`, `*TestCase`).
4. **Custom reporting**: `ReportingExtension` (implements `TestWatcher` + `BeforeTestExecutionCallback` + `AfterAllCallback`) records per-test results annotated with `@TestCase` and calls `ReportGenerator.generate()` after the full class completes.
5. **@DirtiesContext**: Each test gets a fresh H2 database (`BEFORE_EACH_TEST_METHOD`), ensuring complete test isolation.
6. **Content-Type**: `@RequestBody(required = false)` endpoints (block, unblock) work with `mvc.perform(post(...))` without a body in MockMvc.

## EasyBank Backend (run/easybank/backend) — MERODE-adapted Spring Boot

### Summary
Generated from `projects/easybank/merode_application/src/dao/` DAO files.
Fully functional Spring Boot 3.2 / Java 21 / Maven / H2 application.

### Account FSM (key business logic)
```
ALLOCATED --mecraccount--> FROZEN
FROZEN    --medeposit-->   FROZEN   (deposit allowed while frozen)
FROZEN    --meopen-->      OPEN
FROZEN    --meclose-->     CLOSED
OPEN      --medeposit-->   OPEN
OPEN      --mewithdraw-->  OPEN     (withdraw only when open)
OPEN      --mefreeze-->    FROZEN
OPEN      --meclose-->     CLOSED
CLOSED    --meendaccount-> ENDED    (terminal)
```

### Accountholder FSM
```
ALLOCATED --mecraccountholder--> EXISTS
EXISTS    --meblock-->           EXISTS
EXISTS    --meunblock-->         EXISTS
EXISTS    --meendaccountholder (no living accounts)--> ENDED
```

### REST Endpoints (port 8080)
- POST /accountholders — create
- GET  /accountholders, GET /accountholders/{id}
- POST /accountholders/{id}/block, /unblock, /end
- POST /accountholders/{holderId}/accounts — create account
- GET  /accounts, GET /accounts/{id}
- POST /accounts/{id}/open, /deposit, /withdraw, /freeze, /close, /end

### Technical Notes
- **JPA bidirectional relationship**: Do NOT call `holder.getAccounts().add(account)`
  AND `accountRepo.save(account)` in the same transaction — causes
  `NonUniqueObjectException`. Only save via `accountRepo.save(account)`; the FK
  on Account manages the relationship.
- **BigDecimal JSON serialization**: H2 DECIMAL(19,2) columns read back with scale 2
  (e.g. `100.00`). Jackson serializes as `100.0` in JSON. Test assertions must use
  `.value(100.0)` or `is(100.0)`, not `is(100)` (Integer).
- **Tests**: 23 integration tests covering all FSM paths and constraint violations.
  Run with `mvn test` in `run/easybank/backend/`.
- **openapi.yaml**: Located at `run/easybank/backend/openapi.yaml`.

## EasyBank Frontend (`run/easybank/frontend`)

### Tech Stack
- React 18 + Vite 5 + plain CSS (no framework)
- Port: 3000 (dev)
- API proxy: `/api/*` → `http://localhost:8080/*` (via `vite.config.js`)

### Key Files
```
src/
  main.jsx              - React entry point
  App.jsx               - Root component; fetches holders, manages selection & toast state
  App.css               - All styles (CSS custom properties, responsive grid)
  api/
    accountholders.js   - Fetch wrappers for all accountholder endpoints
    accounts.js         - Fetch wrappers for all account endpoints
  components/
    AccountholderPanel.jsx  - Left sidebar: list, create, block/unblock/end actions
    AccountPanel.jsx        - Main area: account cards with FSM action buttons
    StateBadge.jsx          - Color-coded pill badge for FSM states
    Modal.jsx               - Reusable modal with overlay, keyboard close, form slots
    Toast.jsx               - Auto-dismissing bottom-right toast notifications
```

### Running the Frontend
```bash
cd run/easybank/frontend
npm install
npm run dev        # starts at http://localhost:3000
npm run build      # production build → dist/
```

### UI Design
- Two-column layout: sidebar (accountholders) + main (accounts grid)
- State-aware action buttons shown per FSM state (only valid transitions offered)
- Responsive: stacks vertically on screens < 640px
- Graceful error screen when backend is unreachable

## Alpha Insurance Test Application (`run/alphainsurance/test`)

### Architecture
- Spring Boot 3.2.0 test project using `build-helper-maven-plugin` to include backend sources
- **Backend path**: `run/alphainsurance/backend/` (compiled JAR also available)
- **Test source**: `run/alphainsurance/test/src/test/java/com/alphainsurance/test/`
- Run with: `mvn test` from `run/alphainsurance/test/`
- Generates `report.json` and `report.html` in `run/alphainsurance/test/`

### Test Coverage
**230 test cases** covering 7 MERODE FSM coverage criteria:
- **CO** (13): Create one instance of each object type
- **EO** (13): End one instance of each object type
- **AT** (62): All state machine transitions for each entity
- **ALFP** (21): All loop-free paths from initial to ending state
- **AOLP** (33): All one-loop paths (exactly one state visited twice)
- **AL** (20): All loops in each FSM
- **AM** (68): All allowed/disallowed methods per state

**Results**: 228/230 pass. 2 failures are legitimate backend deficiencies:
- `AM-CUST-B-D02`: Backend allows `assessClient` on blacklisted customers (should fail per FSM)
- `AM-CUST-A-D01`: Backend allows `assessClient` on already-assessed customers (should fail per FSM)

### Key Technical Decisions
1. **Jackson circular reference fix**: Backend entities have bidirectional JPA relationships
   (e.g., Customer↔Contract↔InsurancePolicy) without `@JsonIgnore`. Without fix, the backend
   returns malformed JSON (truncated due to `SerializationException: Infinite recursion`).
   Fix: `TestJacksonConfig.java` uses `Jackson2ObjectMapperBuilderCustomizer` with Jackson Mix-ins
   (`@JsonIgnoreProperties`) to break circular refs during test serialization.
   Import with `@Import(TestJacksonConfig.class)` on the test class.

2. **HTTP helper design**: Two layers of POST methods:
   - `postJson(url, body)` / `postJson(url)`: parses response as JsonNode (entity creation)
   - `post(url, body)` / `post(url)`: status check only, no parsing (state-change actions)
   - `get(url)`: returns raw String for field extraction
   This avoids parsing large/complex entity responses for actions that don't need the result.

3. **Fallback ID extraction**: `parse()` has try-catch with fallback `extractIdFromBody()`
   that uses string search to extract `id` from potentially-malformed JSON.
   `extractFieldFromBody()` extracts string field values (e.g., `lifecycleStatus`) for GET checks.

4. **Test isolation**: All tests run in a single Spring context with shared H2 in-memory DB.
   Static fields store entity IDs across test methods. `@TestMethodOrder(OrderAnnotation.class)`
   ensures proper execution order. No `@DirtiesContext` needed.

5. **Backend constraints enforced** (tests pass):
   - `MEcrClaim` disallowed for suspended/unsigned contracts
   - `MEcrClaim` disallowed for blacklisted customers
   - `SignContract` disallowed when not in OFFERED state
   - `MEUnsuspend` disallowed when not in SUSPENDED state
   - `ApproveClaim`/`RejectClaim`/`RejectAsFraud` disallowed when ClaimCase not in SENT state
   - `DisproveFraud` disallowed when ClaimCase not in REJECTED_AS_FRAUD state
   - `RetractAsIncomplete` disallowed when ClaimCase not in SENT state
   - `MEcrContract` disallowed for blacklisted customers

### Backend API Endpoints (alpha-insurance-backend)
- Port: 8080 (configured in `application.properties`)
- Base URL: `/api`
- Main endpoints: `/api/insurance-policies`, `/api/employees`, `/api/customers`,
  `/api/assignments`, `/api/contracts`, `/api/invoices/contract/{id}`,
  `/api/claims`, `/api/accounts/customer/{id}`, `/api/claim-cases`,
  `/api/estimators`, `/api/reports`, `/api/compensation-decisions`,
  `/api/compensation-payments`
- State-change endpoints: `/api/contracts/{id}/sign`, `/api/contracts/{id}/unsuspend`,
  `/api/customers/{id}/assess`, `/api/customers/{id}/blacklist`, `/api/customers/{id}/whitelist`,
  `/api/claim-cases/{id}/add-documents`, `/api/claim-cases/{id}/send-for-evaluation`,
  `/api/claim-cases/{id}/retract-as-incomplete`, `/api/claim-cases/{id}/approve`,
  `/api/claim-cases/{id}/reject`, `/api/claim-cases/{id}/reject-as-fraud`,
  `/api/claim-cases/{id}/disprove-fraud`
- Error responses: `BusinessException` → 400, `EntityNotFoundException` → 404

### Fraud Scenario (complex state chain)
To get a Contract into SUSPENDED state and ClaimCase into REJECTED_AS_FRAUD:
1. Create customer, contract, sign contract
2. Create claim for signed contract
3. Create claim case for claim
4. POST `/api/claim-cases/{id}/send-for-evaluation` (EXISTS → SENT)
5. POST `/api/claim-cases/{id}/reject-as-fraud` (SENT → REJECTED_AS_FRAUD)
   → Also: contract becomes SUSPENDED, customer becomes blacklisted
To undo: POST `/api/claim-cases/{id}/disprove-fraud` (REJECTED_AS_FRAUD → SENT)
   → Also: contract becomes SIGNED, customer becomes whitelisted

## Gas Station Test Application (`run/gasstation/test`)

### Architecture
- Standalone Spring Boot application (non-web: `spring.main.web-application-type=none`)
- Uses raw `HttpURLConnection` (not RestTemplate) to handle partial/malformed JSON responses
- Run from repo root: `java -jar run/gasstation/test/target/gasstation-test-1.0.0.jar`
- Requires backend running at `http://localhost:8080/api` (start with: `java -jar run/gasstation/backend/target/gasstation-backend-1.0.0.jar`)
- Generates `report.json` and `report.html` in `run/gasstation/test/`
- Uses `ApplicationRunner` (CommandLineRunner) pattern – NOT a web server

### Test Coverage
**169 test cases** covering 6 MERODE Tescav criteria:
- **CO** (7): Create one instance of each object type
- **EO** (7): End one instance of each object type  
- **AT** (68): All state machine transitions (GasStation×16, Pump×16, CashTurn×11, RefuelTurn×7, Invoice×9, InvoiceLine×2, CardHolder×7)
- **ALFP** (21): All loop-free paths from initial to ending state
- **AOLP** (18): All one-loop paths (exactly one state visited twice)
- **MAD** (48): Methods Allowed/Disallowed per state (Pump×12, CashTurn×12, RefuelTurn×9, Invoice×8, CardHolder×7)

**Results**: 141/169 pass. 28 failures are legitimate backend deficiencies:
- All Invoice-related tests (17): Backend's `INVOICES` table creation fails because `month` is an H2 reserved SQL keyword. The Invoice entity uses a column named `month` that conflicts with H2's built-in `MONTH()` function.
- CardHolder GET/suspend/unsuspend (7): When Jackson tries to serialize a CardHolder, it lazy-loads the invoices collection, which fails with the same SQL error.
- `MAD-CT-10`: Backend incorrectly allows `driveAwayWithoutPaying` from `FILLING_ENDED_CREDIT` state (should be disallowed per FSM).
- Invoice MAD tests (3): Depend on Invoice creation which fails.

### Key Technical Decisions
1. **Partial JSON extraction**: The backend has circular reference issues (Pump → GasStation → pumps → Pump → ...). The HTTP 200 response is valid at the start but becomes malformed JSON. Solution: read only first 8KB of response, try full JSON parse, fall back to regex extraction of `id` and `state` fields.
2. **HttpURLConnection over RestTemplate**: RestTemplate throws `HttpMessageNotReadableException` for malformed JSON before we can access the raw bytes. `HttpURLConnection` lets us read raw bytes directly.
3. **MAX_BODY_BYTES = 8192**: The `state` and `id` fields always appear in the first 200 bytes of valid responses. 8KB is sufficient to capture them while avoiding memory pressure from multi-MB recursive JSON.
4. **Scaffold helpers**: `scaffoldStationAndPump()` creates a GasStation + Pump needed by most tests. `scaffoldCardHolder()` creates a CardHolder. `scaffoldRefuelTurnFillingEnded()` drives a RefuelTurn to FILLING_ENDED state.
5. **AtomicInteger seq**: Unique name generation using `uid(prefix)` prevents H2 unique constraint violations across test runs.

### Backend Known Bugs (detected by test suite)
1. **Circular JSON**: `Pump`, `CashTurn`, `RefuelTurn` entities serialize with infinite recursion (Pump↔GasStation, CashTurn↔Pump, etc.). Backend sends partial valid JSON then fails with StackOverflowError.
2. **H2 reserved keyword**: `Invoice` entity uses column name `month` which conflicts with H2 SQL reserved word `MONTH`. Causes `Table "INVOICES" not found` on first INSERT (table created with `month` column name fails in DDL).
3. **driveAwayWithoutPaying allowed in FILLING_ENDED_CREDIT**: FSM says it should be disallowed, but backend accepts it.

## Project Structure
```
projects/
  easybank/
    backend/         - Spring Boot REST API (older version)
    merode_application/
      easybank_testcases.html  - Source test cases (HTML)
      src/dao/                 - MERODE-generated DAO files (source of truth)
run/
  easybank/
    backend/         - NEW Spring Boot REST API (adapted from DAO files)
      pom.xml
      openapi.yaml
      src/main/java/com/easybank/
        EasybankApplication.java
        domain/      - Account, Accountholder, AccountState, AccountholderState
        repository/  - AccountRepository, AccountholderRepository
        service/     - AccountService, AccountholderService (FSM logic here)
        controller/  - AccountController, AccountholderController
        dto/         - Request/Response DTOs
        exception/   - MerodeException, GlobalExceptionHandler
      src/test/java/com/easybank/
        AccountFsmTest.java        - 13 tests for Account FSM
        AccountholderFsmTest.java  - 10 tests for Accountholder FSM
    frontend/        - React + Vite SPA (see above)
    test/            - Spring Boot test application (older)
```
