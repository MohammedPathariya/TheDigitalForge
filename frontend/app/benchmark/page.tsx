"use client";

import { useEffect, useMemo, useState } from "react";

import { BrandHeader } from "@/components/BrandHeader";
import { BenchmarkReport, getBenchmarks } from "@/lib/api";

type Difficulty = "all" | "easy" | "medium";
type Outcome = "all" | "passed" | "failed";

function percent(passed: number, total: number): string {
  return total ? `${Math.round((passed / total) * 100)}%` : "0%";
}

export default function BenchmarkPage() {
  const [reports, setReports] = useState<BenchmarkReport[]>([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [difficulty, setDifficulty] = useState<Difficulty>("all");
  const [outcome, setOutcome] = useState<Outcome>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getBenchmarks(controller.signal)
      .then((data) => {
        setReports(data);
        if (data[0]) setSelectedRun(data[0].run_id);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Benchmark data is unavailable.");
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const report = reports.find((item) => item.run_id === selectedRun) ?? reports[0];
  const results = useMemo(() => {
    if (!report) return [];
    return report.results.filter((result) => {
      const matchesDifficulty = difficulty === "all" || result.difficulty === difficulty;
      const matchesOutcome =
        outcome === "all" ||
        (outcome === "passed" ? result.passed : !result.passed);
      return matchesDifficulty && matchesOutcome;
    });
  }, [report, difficulty, outcome]);

  return (
    <>
      <BrandHeader active="benchmark" />
      <main className="benchmark-page">
        <section className="benchmark-intro">
          <span className="eyebrow">Precomputed evaluation</span>
          <div className="benchmark-heading">
            <div>
              <h1>Benchmark evidence, not live theater.</h1>
              <p>
                Full benchmark runs happen locally or in CI. This dashboard reads their
                immutable reports without spending model tokens in the public demo.
              </p>
            </div>
            {reports.length > 1 && (
              <label className="report-picker">
                Report
                <select value={selectedRun} onChange={(event) => setSelectedRun(event.target.value)}>
                  {reports.map((item) => (
                    <option value={item.run_id} key={item.run_id}>
                      {item.model} · {new Date(item.completed_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
        </section>

        {loading ? (
          <div className="benchmark-loading" aria-live="polite">
            <span />
            Loading benchmark reports
          </div>
        ) : error ? (
          <div className="warning-banner" role="status">
            <div>
              <strong>Benchmark service unavailable</strong>
              <span>{error}</span>
            </div>
          </div>
        ) : !report ? (
          <NoReports />
        ) : (
          <BenchmarkResults
            report={report}
            results={results}
            difficulty={difficulty}
            setDifficulty={setDifficulty}
            outcome={outcome}
            setOutcome={setOutcome}
          />
        )}
      </main>
      <footer>
        <span>The Digital Forge</span>
        <span>Results remain tied to model, prompt, evaluator, and benchmark versions</span>
      </footer>
    </>
  );
}

function NoReports() {
  return (
    <>
      <section className="no-reports">
        <span className="empty-mark" aria-hidden="true" />
        <div>
          <h2>No measured benchmark report is available yet.</h2>
          <p>
            The dashboard is ready to display reports from the existing benchmark runner.
            Results are intentionally blank until a real model configuration is measured.
          </p>
        </div>
      </section>
      <section className="method-grid" aria-label="Benchmark methodology">
        <article>
          <span>20</span>
          <h3>Independent tasks</h3>
          <p>Ten easy and ten medium algorithm tasks with immutable hidden evaluators.</p>
        </article>
        <article>
          <span>03</span>
          <h3>Bounded attempts</h3>
          <p>Self-healing is capped at three candidate executions for honest comparison.</p>
        </article>
        <article>
          <span>01</span>
          <h3>Isolated contract</h3>
          <p>Every candidate runs under fixed time, CPU, memory, process, and network limits.</p>
        </article>
      </section>
    </>
  );
}

function BenchmarkResults({
  report,
  results,
  difficulty,
  setDifficulty,
  outcome,
  setOutcome,
}: {
  report: BenchmarkReport;
  results: BenchmarkReport["results"];
  difficulty: Difficulty;
  setDifficulty: (value: Difficulty) => void;
  outcome: Outcome;
  setOutcome: (value: Outcome) => void;
}) {
  const easy = report.results.filter((result) => result.difficulty === "easy");
  const medium = report.results.filter((result) => result.difficulty === "medium");
  const averageDuration = report.results.length
    ? report.results.reduce((total, result) => total + result.duration_seconds, 0) /
      report.results.length
    : 0;

  return (
    <>
      <section className="benchmark-summary">
        <div className="benchmark-meta">
          <span>Model {report.model}</span>
          <span>Benchmark {report.benchmark_version}</span>
          <span>Sandbox {report.sandbox_backend}</span>
          <span>Run {report.run_id.slice(0, 8)}</span>
        </div>
        <div className="metric-grid">
          <article className="metric-card primary-metric">
            <span>Overall pass rate</span>
            <strong>{percent(report.tasks_passed, report.tasks_total)}</strong>
            <p>{report.tasks_passed} of {report.tasks_total} tasks</p>
          </article>
          <article className="metric-card">
            <span>Easy</span>
            <strong>{percent(easy.filter((item) => item.passed).length, easy.length)}</strong>
            <p>{easy.filter((item) => item.passed).length} of {easy.length} tasks</p>
          </article>
          <article className="metric-card">
            <span>Medium</span>
            <strong>{percent(medium.filter((item) => item.passed).length, medium.length)}</strong>
            <p>{medium.filter((item) => item.passed).length} of {medium.length} tasks</p>
          </article>
          <article className="metric-card">
            <span>Average execution</span>
            <strong>{averageDuration.toFixed(2)}s</strong>
            <p>Sandbox duration per task</p>
          </article>
        </div>
      </section>

      <section className="results-section">
        <div className="results-toolbar">
          <div>
            <span className="section-kicker">Task-level evidence</span>
            <h2>{results.length} results</h2>
          </div>
          <div className="filter-groups">
            <FilterGroup
              label="Difficulty"
              value={difficulty}
              values={["all", "easy", "medium"]}
              onChange={(value) => setDifficulty(value as Difficulty)}
            />
            <FilterGroup
              label="Outcome"
              value={outcome}
              values={["all", "passed", "failed"]}
              onChange={(value) => setOutcome(value as Outcome)}
            />
          </div>
        </div>
        <div className="table-card">
          <div className="result-table" role="table" aria-label="Benchmark task results">
            <div className="result-row result-header" role="row">
              <span role="columnheader">Task</span>
              <span role="columnheader">Difficulty</span>
              <span role="columnheader">Tests</span>
              <span role="columnheader">Duration</span>
              <span role="columnheader">Outcome</span>
            </div>
            {results.map((result) => (
              <details className="result-row-wrap" key={result.task_id}>
                <summary className="result-row" role="row">
                  <span role="cell" className="task-id">{result.task_id}</span>
                  <span role="cell" className="capitalize">{result.difficulty}</span>
                  <span role="cell">{result.tests_passed} / {result.tests_total}</span>
                  <span role="cell">{result.duration_seconds.toFixed(2)}s</span>
                  <span role="cell" className={result.passed ? "result-passed" : "result-failed"}>
                    {result.passed ? "Passed" : "Failed"}
                  </span>
                </summary>
                {result.error && <pre className="result-error">{result.error}</pre>}
              </details>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function FilterGroup({
  label,
  value,
  values,
  onChange,
}: {
  label: string;
  value: string;
  values: string[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="filter-group">
      <span>{label}</span>
      <div>
        {values.map((item) => (
          <button
            key={item}
            type="button"
            className={value === item ? "active" : ""}
            onClick={() => onChange(item)}
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}
