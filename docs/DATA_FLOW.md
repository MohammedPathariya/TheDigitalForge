# The Digital Forge data flow

This document follows a request from the browser through generation, execution, repair, and reporting.

## Live run lifecycle

```mermaid
sequenceDiagram
    actor User
    participant UI as Next.js dashboard
    participant API as FastAPI
    participant RM as RunManager
    participant Crew as DevelopmentCrew
    participant Model as OpenAI via CrewAI
    participant Sandbox as Docker or Modal

    User->>UI: Enter natural-language request
    UI->>API: POST /runs {request}
    API->>RM: Reserve run and create snapshot
    RM-->>UI: 202 RunSnapshot with run_id
    RM->>Crew: Start worker with run_id and cancellation event
    Crew->>Model: Janus creates technical brief
    Crew->>Model: Athena creates typed DevelopmentPlan
    Crew->>Model: Hephaestus saves application.py in workspace
    Crew->>Model: Argus saves test_application.py in workspace
    Crew->>Sandbox: Execute pytest with generated files and fixed limits
    Sandbox-->>Crew: stdout, stderr, exit status, timing, error class
    Crew->>RM: Publish event, artifacts, attempt, and retrieval metadata
    loop Up to three candidate attempts
        Crew->>Crew: Classify failure and select repair target
        Crew->>Model: Repair application or regenerate tests
        Crew->>Sandbox: Execute next candidate
    end
    Crew->>Model: Janus writes final report
    Crew->>RM: Publish terminal snapshot
    loop Until terminal status
        UI->>API: GET /runs/{run_id}
        API-->>UI: Current snapshot and evidence
    end
    UI-->>User: Report, code, tests, logs, attempts, and sources
```

## State and data ownership

```mermaid
flowchart TD
    REQ["RunRequest<br/>request text"] --> STATE["RunState<br/>per-run in memory"]
    STATE --> BRIEF[technical_brief]
    STATE --> PLAN["DevelopmentPlan<br/>file names and agent tasks"]
    PLAN --> WS["RunWorkspace<br/>application and test files"]
    STATE --> EVENTS[RunEvent history]
    STATE --> ATTEMPTS[RunAttempt history]
    STATE --> RETRIEVAL[RetrievalEvent history]
    WS --> ARTIFACTS[RunArtifact snapshots]
    WS --> EXEC[Sandbox execution]
    EXEC --> RESULTS[test_results]
    RESULTS --> ATTEMPTS
    BRIEF --> REPORT[final report]
    PLAN --> REPORT
    RESULTS --> REPORT
    STATE --> SNAPSHOT[RunSnapshot API response]
    EVENTS --> SNAPSHOT
    ATTEMPTS --> SNAPSHOT
    RETRIEVAL --> SNAPSHOT
    ARTIFACTS --> SNAPSHOT
    REPORT --> SNAPSHOT
```

`RunState` is the internal mutable workflow state. `RunSnapshot` is the read model returned to the frontend. The run manager copies state into snapshots under a lock, so polling never receives a live mutable workspace object.

## Repair decision flow

```mermaid
flowchart TD
    TEST[Sandbox test result] --> CLASSIFY{Failure classification}
    CLASSIFY -->|all tests passed| REPORT[Record passed candidate]
    CLASSIFY -->|infrastructure| INFRA{Retryable?}
    INFRA -->|no| STOP[Stop with configuration failure]
    INFRA -->|yes, budget remains| RETRY[Retry sandbox without consuming candidate attempt]
    INFRA -->|retry budget exhausted| STOP2[Stop with infrastructure exhaustion]
    CLASSIFY -->|generated test failure| TESTFIX[Discard stale suite and Argus writes fresh tests]
    CLASSIFY -->|timeout, resource, contract| CODEFIX[Hephaestus repairs application code]
    CLASSIFY -->|other application or test ambiguity| DIAG[Athena diagnoses target and next task]
    DIAG --> TARGET{Repair target}
    TARGET -->|application| CODEFIX
    TARGET -->|tests| TESTFIX
    TESTFIX --> BUDGET{Candidate attempts remain?}
    CODEFIX --> BUDGET
    RETRY --> TEST
    BUDGET -->|yes| TEST
    BUDGET -->|no| FAIL[Record failed candidate and report manual review]
    REPORT --> DONE[Terminal completed run]
```

Infrastructure retries are recorded as `infrastructure` attempts but do not increment the candidate-attempt counter. A generated test failure causes the old test suite to be discarded before Argus writes a fresh suite, preventing incorrect assertions from anchoring the repair.

## Benchmark data flow

```mermaid
flowchart LR
    CATALOG[Versioned task catalog] --> RUNNER[Benchmark runner]
    RUNNER -->|baseline| BASE[Single model response]
    RUNNER -->|Digital Forge| CREW[DevelopmentCrew]
    BASE --> CANDIDATE[Candidate Python file]
    CREW --> CANDIDATE
    CANDIDATE --> EVAL["Independent hidden evaluator<br/>in isolated sandbox"]
    EVAL --> TASK[TaskResult]
    TASK --> CHECKPOINT[Per-task checkpoint]
    TASK --> REPORT[Aggregate report.json]
    REPORT --> API[GET /benchmarks]
    API --> DASH[Benchmark dashboard]
```

The benchmark evaluator is independent from the agent-generated tests. The public dashboard reads existing report files and never runs the full benchmark or spends model tokens.
