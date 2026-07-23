"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { BrandHeader } from "@/components/BrandHeader";
import { CodePanel } from "@/components/CodePanel";
import {
  cancelRun,
  checkHealth,
  getRun,
  RunAgent,
  RunSnapshot,
  RunStage,
  startRun,
} from "@/lib/api";

const RUN_STORAGE_KEY = "digital-forge-active-run";
const MAX_REQUEST_LENGTH = 20_000;

const EXAMPLES = [
  "Build a Python function that validates nested brackets and include a focused pytest suite.",
  "Build a Python function that groups orders by customer and summarizes completed totals, pending totals, and order counts.",
  "Implement a stable deduplication function that preserves input order and include a focused pytest suite.",
];

const PIPELINE: Array<{
  stage: RunStage;
  agent: string;
  role: string;
  description: string;
  activeAgent: RunAgent;
}> = [
  {
    stage: "briefing",
    agent: "Janus",
    role: "Client liaison",
    description: "Translates the request into a precise technical brief.",
    activeAgent: "janus",
  },
  {
    stage: "planning",
    agent: "Athena",
    role: "Strategic lead",
    description: "Builds the plan and routes repairs to the right specialist.",
    activeAgent: "athena",
  },
  {
    stage: "developing",
    agent: "Hephaestus",
    role: "Principal developer",
    description: "Writes and repairs the isolated Python implementation.",
    activeAgent: "hephaestus",
  },
  {
    stage: "testing",
    agent: "Argus",
    role: "Quality assurance",
    description: "Authors tests and validates the candidate in the sandbox.",
    activeAgent: "argus",
  },
  {
    stage: "reporting",
    agent: "Janus",
    role: "Final report",
    description: "Packages the verified artifacts and evidence for review.",
    activeAgent: "janus",
  },
];

type View = "overview" | "attempts" | "artifacts" | "evidence" | "report";
type Health = "checking" | "online" | "waking" | "offline";
type PlanInstruction =
  | string
  | number
  | boolean
  | null
  | PlanInstruction[]
  | { [key: string]: PlanInstruction };

function stageRank(stage: RunStage): number {
  if (stage === "queued") return -1;
  if (stage === "repairing") return 3;
  if (stage === "complete" || stage === "cancelled") return PIPELINE.length;
  return PIPELINE.findIndex((item) => item.stage === stage);
}

function activePipelineIndex(run: RunSnapshot): number {
  const reportedIndex = PIPELINE.findIndex(
    (item) =>
      item.activeAgent === run.active_agent &&
      (run.active_agent !== "janus" || item.stage === run.stage),
  );
  if (reportedIndex >= 0) return reportedIndex;

  const activity = run.events.at(-1)?.message.toLowerCase() ?? "";
  if (activity.includes("argus")) return 3;
  if (activity.includes("hephaestus")) return 2;
  if (activity.includes("athena")) return 1;
  if (activity.includes("janus")) return run.stage === "reporting" ? 4 : 0;
  if (run.stage === "repairing") return activity.includes("test") ? 3 : 2;
  return stageRank(run.stage);
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatStage(stage: RunStage): string {
  return stage.charAt(0).toUpperCase() + stage.slice(1);
}

function humanizeKey(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function parsePlanInstruction(value: string): PlanInstruction {
  const trimmed = value.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return value;
  try {
    return JSON.parse(trimmed) as PlanInstruction;
  } catch {
    return value;
  }
}

function splitInlineSteps(value: string): string[] {
  const normalized = value.trim();
  if (!normalized) return [];
  const numbered = normalized.split(/\s+(?=\d+\.\s+)/);
  if (numbered.length > 1 && numbered.every((item) => /^\d+\.\s+/.test(item))) {
    return numbered.map((item) => item.replace(/^\d+\.\s+/, "").trim());
  }
  const dashed = normalized.split(/\s+-\s+/);
  if (dashed.length > 1) {
    return dashed.map((item) => item.replace(/^-\s*/, "").trim()).filter(Boolean);
  }
  return [];
}

function candidateAttemptsUsed(run: RunSnapshot): number {
  return Math.max(
    run.attempts_used,
    ...run.attempts
      .map((attempt) => attempt.candidate_attempt ?? 0),
  );
}

function HealthIndicator({ health }: { health: Health }) {
  const labels: Record<Health, string> = {
    checking: "Checking backend",
    online: "Backend online",
    waking: "Backend waking",
    offline: "Backend unavailable",
  };
  return (
    <span className={`health health-${health}`}>
      <span className="health-dot" aria-hidden="true" />
      {labels[health]}
    </span>
  );
}

export default function ForgePage() {
  const [request, setRequest] = useState("");
  const [run, setRun] = useState<RunSnapshot | null>(null);
  const [runId, setRunId] = useState<string | null>(() =>
    typeof window === "undefined" ? null : window.localStorage.getItem(RUN_STORAGE_KEY),
  );
  const [health, setHealth] = useState<Health>("checking");
  const [view, setView] = useState<View>("overview");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [connectionIssue, setConnectionIssue] = useState(false);
  const [clock, setClock] = useState<number | null>(null);

  const terminal =
    run?.status === "completed" ||
    run?.status === "failed" ||
    run?.status === "cancelled";

  useEffect(() => {
    const controller = new AbortController();
    const wakingTimer = window.setTimeout(() => setHealth("waking"), 2500);
    checkHealth(controller.signal)
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"))
      .finally(() => window.clearTimeout(wakingTimer));
    return () => {
      controller.abort();
      window.clearTimeout(wakingTimer);
    };
  }, []);

  useEffect(() => {
    if (!runId) return;
    const activeRunId = runId;
    const controller = new AbortController();
    let timer: number | undefined;

    async function poll() {
      try {
        const snapshot = await getRun(activeRunId, controller.signal);
        setRun(snapshot);
        setConnectionIssue(false);
        if (!["completed", "failed", "cancelled"].includes(snapshot.status)) {
          timer = window.setTimeout(poll, 1800);
        }
      } catch (error) {
        if (controller.signal.aborted) return;
        setConnectionIssue(true);
        if (error instanceof Error && error.message === "Run not found.") {
          window.localStorage.removeItem(RUN_STORAGE_KEY);
        } else {
          timer = window.setTimeout(poll, 3500);
        }
      }
    }

    void poll();
    return () => {
      controller.abort();
      if (timer) window.clearTimeout(timer);
    };
  }, [runId]);

  useEffect(() => {
    if (!runId || terminal) return;
    const timer = window.setInterval(() => setClock(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, [runId, terminal]);

  const elapsed = useMemo(() => {
    if (!run) return null;
    const end = terminal
      ? new Date(run.updated_at).getTime()
      : (clock ?? new Date(run.updated_at).getTime());
    return Math.max(0, Math.floor((end - new Date(run.created_at).getTime()) / 1000));
  }, [clock, run, terminal]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const cleaned = request.trim();
    if (!cleaned) {
      setFormError("Describe what you want the crew to build.");
      return;
    }
    if (cleaned.length > MAX_REQUEST_LENGTH) {
      setFormError("The request exceeds the 20,000 character limit.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      const snapshot = await startRun(cleaned);
      setRun(snapshot);
      setRunId(snapshot.run_id);
      setView("overview");
      window.localStorage.setItem(RUN_STORAGE_KEY, snapshot.run_id);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "The run could not start.");
    } finally {
      setSubmitting(false);
    }
  }

  async function requestCancellation() {
    if (!run) return;
    try {
      setRun(await cancelRun(run.run_id));
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Cancellation failed.");
    }
  }

  function reset() {
    setRun(null);
    setRunId(null);
    setRequest("");
    setView("overview");
    setFormError(null);
    window.localStorage.removeItem(RUN_STORAGE_KEY);
  }

  return (
    <>
      <BrandHeader active="forge" />
      <main>
        {!run ? (
          <Landing
            request={request}
            setRequest={setRequest}
            submit={submit}
            submitting={submitting}
            error={formError}
            health={health}
          />
        ) : (
          <RunWorkspace
            run={run}
            view={view}
            setView={setView}
            elapsed={elapsed}
            connectionIssue={connectionIssue}
            cancel={requestCancellation}
            reset={reset}
          />
        )}
      </main>
      <footer>
        <span>The Digital Forge</span>
        <span>Next.js · FastAPI · CrewAI · isolated execution</span>
      </footer>
    </>
  );
}

function Landing({
  request,
  setRequest,
  submit,
  submitting,
  error,
  health,
}: {
  request: string;
  setRequest: (value: string) => void;
  submit: (event: FormEvent) => void;
  submitting: boolean;
  error: string | null;
  health: Health;
}) {
  return (
    <div className="landing">
      <section className="hero">
        <div className="eyebrow">Multi-agent software development</div>
        <h1>Turn a precise request into tested Python code.</h1>
        <p>
          Four specialized agents plan, implement, test, and repair each candidate inside
          an isolated sandbox. Every result includes the evidence behind it.
        </p>
        <div className="hero-meta">
          <HealthIndicator health={health} />
          <span className="meta-divider" />
          <span>Maximum 3 candidate attempts</span>
        </div>
      </section>

      <section className="submission-card" aria-labelledby="request-title">
        <div className="section-heading">
          <div>
            <span className="step-number">01</span>
            <h2 id="request-title">What should the forge build?</h2>
          </div>
          <span className="character-count">
            {request.length.toLocaleString()} / {MAX_REQUEST_LENGTH.toLocaleString()}
          </span>
        </div>
        <form onSubmit={submit}>
          <label className="sr-only" htmlFor="forge-request">
            Software request
          </label>
          <textarea
            id="forge-request"
            value={request}
            onChange={(event) => setRequest(event.target.value)}
            placeholder="Describe the function, inputs, expected behavior, constraints, and edge cases."
            rows={8}
            maxLength={MAX_REQUEST_LENGTH + 1}
          />
          {error && <p className="form-error">{error}</p>}
          <div className="form-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => setRequest("")}
              disabled={!request || submitting}
            >
              Clear
            </button>
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? "Starting forge" : "Start forging"}
            </button>
          </div>
        </form>
        <div className="examples">
          <span>Try an example</span>
          <div className="example-list">
            {EXAMPLES.map((example, index) => (
              <button key={example} type="button" onClick={() => setRequest(example)}>
                <span>0{index + 1}</span>
                {example}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="workflow-section" aria-labelledby="workflow-title">
        <div className="section-heading">
          <div>
            <span className="step-number">02</span>
            <h2 id="workflow-title">One request. Four accountable roles.</h2>
          </div>
        </div>
        <div className="agent-grid">
          {PIPELINE.slice(0, 4).map((item, index) => (
            <article className="agent-card" key={item.agent}>
              <div className="agent-index">0{index + 1}</div>
              <h3>{item.agent}</h3>
              <p className="agent-role">{item.role}</p>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function RunWorkspace({
  run,
  view,
  setView,
  elapsed,
  connectionIssue,
  cancel,
  reset,
}: {
  run: RunSnapshot;
  view: View;
  setView: (view: View) => void;
  elapsed: number | null;
  connectionIssue: boolean;
  cancel: () => void;
  reset: () => void;
}) {
  const terminal = ["completed", "failed", "cancelled"].includes(run.status);
  const currentRank = stageRank(run.stage);
  const reachedRanks = run.events
    .map((event) => stageRank(event.stage))
    .filter((rank) => rank >= 0 && rank < PIPELINE.length);
  const terminalRank = reachedRanks.length ? Math.max(...reachedRanks) : -1;
  const pipelineFailed = run.status === "failed" && Boolean(run.error);
  const finalAttempt = run.attempts[run.attempts.length - 1];
  const unresolvedTestFailure =
    finalAttempt !== undefined && finalAttempt.status !== "passed";
  const routedAttempt = [...run.attempts]
    .reverse()
    .find((attempt) => attempt.repair_target !== null);
  const outcomeFailureStage: RunStage | null =
    routedAttempt?.repair_target === "tests"
      ? "testing"
      : routedAttempt?.repair_target === "application"
        ? "developing"
        : finalAttempt?.failure_kind === "test"
          ? "testing"
          : finalAttempt &&
              ["candidate", "timeout", "resource"].includes(
                finalAttempt.failure_kind ?? "",
              )
            ? "developing"
            : null;
  const statusLabel =
    run.cancel_requested && !terminal ? "Cancellation requested" : run.status;
  const candidateAttempts = candidateAttemptsUsed(run);
  const activeIndex = activePipelineIndex(run);
  const pipelineTitle =
    run.status === "failed" && !run.error
      ? "Needs manual review"
      : run.status === "failed"
        ? "Pipeline failed"
        : run.status === "completed"
          ? "Complete"
          : run.status === "cancelled"
            ? "Stopped"
            : formatStage(run.stage);

  return (
    <div className="run-page">
      <section className="run-header-card">
        <div>
          <span className={`status-label status-${run.status}`}>{statusLabel}</span>
          <h1>{terminal ? "Forge result" : "The crew is working"}</h1>
          <p>{run.request}</p>
        </div>
        <div className="run-facts">
          <div>
            <span>Run ID</span>
            <strong>{run.run_id.slice(0, 8)}</strong>
          </div>
          <div>
            <span>Started</span>
            <strong>{formatTime(run.created_at)}</strong>
          </div>
          <div>
            <span>Elapsed</span>
            <strong>{elapsed ?? 0}s</strong>
          </div>
          <div>
            <span>Candidate attempts</span>
            <strong>
              {candidateAttempts} / {run.max_attempts}
            </strong>
          </div>
          <div>
            <span>Test runs</span>
            <strong>{run.attempts.length}</strong>
          </div>
        </div>
      </section>

      {connectionIssue && (
        <div className="warning-banner" role="status">
          <div>
            <strong>Connection interrupted</strong>
            <span>
              The run may still be processing. The forge is reconnecting without marking
              the run as failed.
            </span>
          </div>
        </div>
      )}

      {run.error && (
        <div className="error-banner" role="alert">
          <strong>Pipeline error</strong>
          <span>{run.error}</span>
        </div>
      )}

      <section className="pipeline-card" aria-labelledby="pipeline-title">
        <div className="pipeline-heading">
          <div>
            <span className="section-kicker">Live pipeline</span>
            <h2 id="pipeline-title">{pipelineTitle}</h2>
          </div>
          {!terminal ? (
            <button
              className="secondary-button danger-text"
              type="button"
              onClick={cancel}
              disabled={run.cancel_requested}
            >
              {run.cancel_requested ? "Stopping safely" : "Cancel run"}
            </button>
          ) : (
            <button className="primary-button" type="button" onClick={reset}>
              New run
            </button>
          )}
        </div>
        <div className="pipeline-grid">
          {PIPELINE.map((item, index) => {
            const isRunning = !terminal && activeIndex === index;
            const isFailed =
              (run.status === "failed" || unresolvedTestFailure) &&
              (pipelineFailed
                ? terminalRank === index
                : item.stage === outcomeFailureStage);
            const isCancelled = run.status === "cancelled" && terminalRank === index;
            const isComplete =
              run.status === "completed" ||
              (run.status === "failed" && !pipelineFailed) ||
              (terminal
                ? terminalRank > index
                : activeIndex >= 0
                  ? activeIndex > index
                  : currentRank > index);
            const stageClass = isRunning
              ? "stage-running"
              : isFailed
                ? "stage-failed"
                : isCancelled
                  ? "stage-cancelled"
                  : isComplete
                    ? "stage-complete"
                    : "stage-pending";
            const stageLabel = isRunning
              ? "Working"
              : isFailed
                ? "Failed"
                : isCancelled
                  ? "Stopped"
                  : isComplete
                    ? "Complete"
                    : "Waiting";
            return (
              <article
                className={`pipeline-stage ${stageClass}`}
                key={item.stage}
              >
                <div className="stage-state">
                  <span className="stage-dot" aria-hidden="true" />
                  {stageLabel}
                </div>
                <h3>{item.agent}</h3>
                <p>{item.role}</p>
              </article>
            );
          })}
        </div>
      </section>

      <nav className="run-tabs" aria-label="Run details">
        {(["overview", "attempts", "artifacts", "evidence", "report"] as View[]).map(
          (item) => (
            <button
              key={item}
              type="button"
              className={view === item ? "active" : ""}
              onClick={() => setView(item)}
            >
              {item}
              {item === "attempts" && <span>{run.attempts.length}</span>}
              {item === "evidence" && <span>{run.retrieval_events.length}</span>}
            </button>
          ),
        )}
      </nav>

      <section className="run-content">
        {view === "overview" && <Overview run={run} />}
        {view === "attempts" && <Attempts run={run} />}
        {view === "artifacts" && <Artifacts run={run} />}
        {view === "evidence" && <Evidence run={run} />}
        {view === "report" && <Report run={run} />}
      </section>
    </div>
  );
}

function Overview({ run }: { run: RunSnapshot }) {
  return (
    <div className="overview-grid">
      <article className="detail-card overview-panel">
        <span className="section-kicker">Current activity</span>
        <h3>{run.events.at(-1)?.message ?? "The run is queued."}</h3>
        <div className="event-list custom-scroll">
          {[...run.events].reverse().map((event, index) => (
            <div className="event-row" key={`${event.created_at}-${index}`}>
              <span className="event-marker" />
              <div>
                <strong>{formatStage(event.stage)}</strong>
                <p>{event.message}</p>
              </div>
              <time>{new Date(event.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
            </div>
          ))}
        </div>
      </article>
      <article className="detail-card overview-panel">
        <span className="section-kicker">Development plan</span>
        {run.plan ? (
          <div className="plan-scroll custom-scroll">
            <div className="plan-grid">
              <PlanSummary
                title="Application"
                fileName={run.plan.file_name}
                instruction={run.plan.developer_task}
              />
              <PlanSummary
                title="Test suite"
                fileName={run.plan.test_file_name}
                instruction={run.plan.tester_task}
              />
            </div>
          </div>
        ) : (
          <p className="empty-copy">Athena’s development plan will appear here.</p>
        )}
      </article>
    </div>
  );
}

function PlanSummary({
  title,
  fileName,
  instruction,
}: {
  title: string;
  fileName: string;
  instruction: string;
}) {
  return (
    <div className="plan-card">
      <span>{title}</span>
      <strong>{fileName}</strong>
      <InstructionView value={parsePlanInstruction(instruction)} />
    </div>
  );
}

function InstructionView({ value }: { value: PlanInstruction }) {
  if (Array.isArray(value)) {
    return (
      <ul className="instruction-list">
        {value.map((item, index) => (
          <li key={index}>
            <InstructionView value={item} />
          </li>
        ))}
      </ul>
    );
  }
  if (value && typeof value === "object") {
    return (
      <dl className="instruction-fields">
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <dt>{humanizeKey(key)}</dt>
            <dd>
              <InstructionView value={item} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }
  if (typeof value === "string") {
    const steps = splitInlineSteps(value);
    if (steps.length > 1) {
      return (
        <ul className="instruction-list">
          {steps.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ul>
      );
    }
  }
  return <p>{value === null ? "None" : String(value)}</p>;
}

function Attempts({ run }: { run: RunSnapshot }) {
  if (!run.attempts.length) {
    return <EmptyState title="No attempts yet" copy="Test execution records will appear here as Argus validates each candidate." />;
  }
  return (
    <div className="attempt-list">
      {run.attempts.map((attempt) => (
        <details className={`attempt-card attempt-${attempt.status}`} key={attempt.sequence}>
          <summary>
            <div>
              <span className="attempt-number">
                {attempt.candidate_attempt
                  ? `Attempt ${attempt.candidate_attempt}`
                  : `Infrastructure retry ${attempt.sequence}`}
              </span>
              <strong>{attempt.status}</strong>
            </div>
            <div className="attempt-meta">
              {attempt.failure_kind && <span>{attempt.failure_kind}</span>}
              {attempt.repair_target && <span>Repair: {attempt.repair_target}</span>}
            </div>
          </summary>
          <div className="attempt-body">
            <CodePanel title="Test results" content={attempt.test_results} />
            <CodePanel title="Application snapshot" content={attempt.application_code} language="python" />
            <CodePanel title="Test snapshot" content={attempt.test_code} language="python" />
          </div>
        </details>
      ))}
    </div>
  );
}

function Artifacts({ run }: { run: RunSnapshot }) {
  if (!run.artifacts.length) {
    return <EmptyState title="No generated files yet" copy="Application code and tests will appear after the development stages complete." />;
  }
  return (
    <div className="artifact-list">
      {run.artifacts.map((artifact) => (
        <CodePanel
          key={artifact.path}
          title={artifact.path}
          content={artifact.content}
          language="python"
        />
      ))}
      {run.test_results && <CodePanel title="Latest test results" content={run.test_results} />}
    </div>
  );
}

function Evidence({ run }: { run: RunSnapshot }) {
  if (!run.retrieval_events.length) {
    return <EmptyState title="No documentation retrieved" copy="RAG evidence appears only when Athena or Hephaestus needs version-pinned official API documentation." />;
  }
  return (
    <div className="evidence-list">
      {run.retrieval_events.map((event, eventIndex) => (
        <article className="evidence-card" key={`${event.query}-${eventIndex}`}>
          <div className="evidence-heading">
            <span className="rag-badge">Documentation retrieval</span>
            <h3>{event.query}</h3>
          </div>
          <div className="source-list">
            {event.results.map((source) => (
              <a href={source.source_url} target="_blank" rel="noreferrer" key={source.chunk_id}>
                <div>
                  <strong>{source.title}</strong>
                  <span>{source.heading}</span>
                </div>
                <div className="source-meta">
                  <span>{source.library} {source.library_version}</span>
                  <span>Open source</span>
                </div>
              </a>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function Report({ run }: { run: RunSnapshot }) {
  if (!run.report) {
    return <EmptyState title="Report not ready" copy="Janus creates the final report after implementation and testing finish." />;
  }
  return <CodePanel title="Final report" content={run.report} language="markdown" />;
}

function EmptyState({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="empty-state">
      <span className="empty-mark" aria-hidden="true" />
      <h3>{title}</h3>
      <p>{copy}</p>
    </div>
  );
}
