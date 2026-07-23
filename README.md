# The Digital Forge

The Digital Forge is a multi-agent software generation system for turning a natural-language request into a tested Python implementation. It coordinates four specialized agents, executes generated code in an isolated sandbox, records repair attempts, and exposes both live run traces and precomputed benchmark evidence through a Next.js dashboard.

The current revamp branch is `mjp/revamp-digital-forge`.

## What It Does

- Accepts a user request for a small Python feature or service.
- Builds a technical brief and development plan.
- Generates application code and tests.
- Runs the generated artifacts in a network-isolated sandbox.
- Classifies failures as application, test, infrastructure, or contract issues.
- Repairs failed candidates within a bounded attempt budget.
- Records generated artifacts, execution output, retrieval evidence, and the final report.
- Displays immutable benchmark reports without spending model tokens in the public dashboard.

## Architecture

```text
Next.js frontend
        |
        v
FastAPI backend
        |
        v
CrewAI orchestration
Janus -> Athena -> Hephaestus -> Argus
             |                    |
             v                    v
      ChromaDB retrieval     SandboxRunner
                             |           |
                             v           v
                          Docker       Modal
                        local/CI    hosted demo
        |
        v
Structured run and benchmark artifacts
```

Agent roles:

- `Janus`: turns the request into a technical brief and final report.
- `Athena`: creates the typed development and testing plan.
- `Hephaestus`: writes and repairs application code.
- `Argus`: writes and repairs the generated test suite.

The benchmark evaluator is independent from the agents. Agent-generated tests support development, but hidden benchmark tests determine correctness.

## Current Benchmark Evidence

The active benchmark suite is version `1.1.0` with 20 tasks: 10 easy and 10 medium. It measures the algorithmic and workflow-code path, not the separate RAG evaluation suite.

| Run | Model | Result | Easy | Medium | Report |
| --- | --- | ---: | ---: | ---: | --- |
| Digital Forge | `digital-forge:gpt-4o-mini` | `16/20` | `9/10` | `7/10` | `benchmark-results/46e08fb1861141cf82fad76ef676ce5b/report.json` |
| Zero-shot baseline | `gpt-4o-mini` | `14/20` | `7/10` | `7/10` | `benchmark-results/3da7bfb192c84a47aedc04a1d20be0f7/report.json` |

The dashboard loads these tracked report artifacts through `GET /benchmarks`. Full benchmark execution happens locally or in CI, not in the public demo.

See `docs/BENCHMARK_GUARDED_RUN_2026_07_23.md` for the guarded run details.

## Repository Layout

```text
backend/             FastAPI app, run manager, pipeline integration
benchmark/           Benchmark catalog, runners, evaluator, hidden cases
benchmark-results/   Tracked benchmark report JSON files used by the dashboard
frontend/            Next.js App Router frontend
rag/                 Versioned ChromaDB documentation index
tests/               Backend, pipeline, sandbox, benchmark, and API tests
docs/                Architecture, decisions, status, and benchmark notes
```

## Requirements

- Python 3.10 or newer
- Node.js compatible with the pinned frontend dependencies
- Docker for local sandbox execution and benchmark reproduction
- OpenAI API key for live agent runs and benchmark generation

Create a local `.env` file when running model-backed paths:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL_NAME=gpt-4o-mini
```

The `.env` file is ignored by Git.

## Local Setup

Backend:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m backend.main
```

The backend defaults to `http://localhost:8000`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:3000` and calls the backend at `http://localhost:8000`. Override that with `NEXT_PUBLIC_BACKEND_URL` if needed.

## Running Benchmarks

Zero-shot baseline:

```bash
.venv/bin/python -m benchmark.baseline \
  --model gpt-4o-mini \
  --sandbox docker \
  --max-consecutive-failures 3 \
  --finish-remaining-threshold 3
```

Digital Forge:

```bash
.venv/bin/python -m benchmark.digital_forge \
  --model gpt-4o-mini \
  --sandbox docker \
  --max-consecutive-failures 3 \
  --finish-remaining-threshold 3
```

Each completed task writes a checkpoint before the aggregate report is finalized. A full successful run writes `benchmark-results/<run_id>/report.json`. Guarded interrupted runs write `interrupted.json`.

## Verification

Python checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend benchmark rag tests
.venv/bin/python -m ruff format --check backend benchmark rag tests
.venv/bin/python -m mypy backend benchmark rag tests
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Targeted benchmark/frontend checks used during the latest revamp:

```bash
.venv/bin/python -m pytest tests/test_benchmarks.py tests/test_baseline.py tests/test_digital_forge_benchmark.py -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Current Limits

- Run snapshots are process-local and disappear when the backend restarts.
- Cancellation is cooperative and stops at workflow boundaries.
- Public deployment rate limits, spend controls, durable run storage, and one-run concurrency enforcement remain deployment work.
- Per-agent token and cost telemetry is not yet captured by the benchmark runner.
- The RAG layer is evaluated separately from the active 20-task algorithm benchmark.

## Project Docs

- `docs/STATUS.md`: current implementation status, verification, risks, and handoff notes.
- `docs/ARCHITECTURE.md`: system architecture and deployment model.
- `docs/DECISIONS.md`: accepted design decisions.
- `docs/WEEK_PLAN.md`: phased revamp plan.
- `docs/BENCHMARK_GUARDED_RUN_2026_07_23.md`: latest guarded benchmark evidence.
# 🛠️ The Digital Forge: An Autonomous AI Software Development Crew 

**The Digital Forge** is a fully autonomous software development pipeline powered by a crew of specialized AI agents. Give it a natural language request, and the crew will work together to understand the requirements, write the code, create tests, and even debug their own work to deliver a final, validated solution.

**Live Demo:** [**https://thedigitalforge.onrender.com/**](https://thedigitalforge.onrender.com/)

---

### A Note on Project Status (MVP)

This project is currently a Minimum Viable Product (MVP). It's a functional proof-of-concept demonstrating the power of a specialized AI agent crew. While I've worked hard to make the agents as robust as possible, the underlying nature of Large Language Models and the CrewAI framework means that occasional bugs or AI "hallucinations" can still occur, especially with complex or ambiguous requests. I am continuously working to improve the system's reliability.

---

## Core Concept & Philosophy

This project is built on my philosophy of **agent specialization**, mirroring a real-world agile development team. Instead of a single, monolithic AI trying to handle all tasks, The Digital Forge employs a crew of four distinct agents I designed, each with a unique role, personality, and set of instructions. This separation of duties creates a more robust and intelligent system capable of complex problem-solving and self-correction.

The entire process is designed to be **autonomous and iterative**. The crew operates in sprints, with a built-in debugging loop that allows them to analyze their own failures and attempt fixes, learning and adapting with each cycle.

---

## The AI Crew: Unit 734

The crew of AI agents, "Unit 734," is the heart of the operation. I modeled each agent after a figure from Greek mythology to reflect their specific role in the development pipeline.

| Agent       | Role                                    | Responsibilities                                                                                                                              |
| :---------- | :-------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| **Janus** | 👤 **Client Liaison** | Interprets the initial user request to create a formal technical brief. At the end of the process, compiles the final, client-facing report.    |
| **Athena** | 📝 **Strategic Team Lead** | Deconstructs the technical brief into a precise, actionable development plan. When tests fail, performs a root cause analysis to diagnose the bug. |
| **Hephaestus**| ⌨️ **Principal Software Developer** | Writes clean, efficient, and correct Python application code based strictly on the instructions from Athena.                                    |
| **Argus** | 🔎 **Quality Assurance Tester** | Writes and executes a `pytest` test suite to validate the code written by Hephaestus. Its tests must be a faithful reflection of the original task. |

---

## System Architecture & Design Decisions

I built The Digital Forge with a modern, decoupled architecture designed for scalability and robust error handling.

#### **Frontend: Streamlit**
* **Why Streamlit?** I chose Streamlit for its ability to create a beautiful, interactive user interface with pure Python. It allowed for rapid prototyping and provided a seamless way to display real-time progress and final reports without the complexity of traditional web frameworks.

#### **Backend: Flask & CrewAI**
* **Flask:** A lightweight Flask server acts as the API endpoint. It receives requests from the Streamlit front end and initiates the AI agent pipeline.
* **CrewAI:** This is the core framework that orchestrates the agents. It manages the flow of information, the assignment of tasks, and the execution of the overall workflow.

#### **Critical Design Decision: The In-Memory Workspace**
* **The Challenge:** Deploying an application that needs to write and read files to a platform with an ephemeral or read-only filesystem (like Render's free tier) is a major challenge. The agents need a "workspace" to save their code and tests, but can't rely on a persistent disk.
* **The Solution:** I implemented a **virtual, in-memory workspace** using a simple Python dictionary. All file operations (`save_file`, `read_file`) interact with this dictionary instead of the disk. The `run_tests` tool is engineered to use temporary files that are created just for the test run and are immediately deleted—a safe and standard practice for server environments. This makes the entire application stateless, scalable, and perfectly suited for modern cloud deployment.

#### **The Robust Debugging Loop**
* **The Goal:** A truly autonomous system must be able to fix its own mistakes.
* **The Implementation:** The pipeline operates in a loop for up to three "sprints." If tests fail, the log is passed back to **Athena**, my analyst agent. Athena performs a **differential diagnosis** to determine the root cause:
    1.  **Is the code buggy?** (A Hephaestus error)
    2.  **Is the test buggy?** (An Argus error)
* The main orchestration script then routes Athena's new, targeted task to the correct agent, allowing the crew to fix bugs in both the application code and their own test suites.

---

## Setbacks and Evolution: The Journey to Robustness

The development of The Digital Forge was an iterative process of identifying and fixing critical failures in the agents' logic.

1.  **The Contradiction Failure:**
    * **The Problem:** In early tests, the developer (Hephaestus) would correctly write code, but the tester (Argus) would write a faulty test expecting a different outcome. The team lead (Athena) would then incorrectly side with the bad test and instruct the developer to break the working code.
    * **The Solution:** I re-engineered Athena's `analyze_test_failure` task to perform the "differential diagnosis," forcing it to compare the test failure against the *original* developer task to determine the true source of the error.

2.  **The Hallucination Failure:**
    * **The Problem:** When faced with a confusing bug-fix task or an error reading a file, the agents would sometimes "hallucinate"—inventing completely new, unrelated code instead of using the context they were given. This led to the pipeline completely derailing.
    * **The Solution:** I added **CRITICAL, explicit instructions** to the agents' goals and task descriptions. Hephaestus was forbidden from writing test code, and Janus was commanded to *only* use the verbatim content provided for the final report.

3.  **The Orchestration Failure:**
    * **The Problem:** Even after Athena correctly diagnosed a bug in the test suite, the main script was still incorrectly routing the fix to the developer instead of the tester.
    * **The Solution:** I rewrote the debugging loop in `main_deployment.py` to correctly parse the JSON output from Athena and dynamically assign the next task to the agent specified in the `file_to_fix` key.

---

## How to Run Locally

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/MohammedPathariya/TheDigitalForge.git](https://github.com/MohammedPathariya/TheDigitalForge.git)
    cd TheDigitalForge
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Your Environment Variables:**
    * Create a file named `.env` in the project's root directory.
    * Add your OpenAI API key to this file:
        ```
        OPENAI_API_KEY="your_api_key_here"
        ```

5.  **Run the Application:**
    * The backend server and the front-end Streamlit app are now integrated. Simply run the Streamlit app:
        ```bash
        streamlit run streamlit_app.py
        ```
    * Open your browser to the local URL provided by Streamlit.

---

## Future Improvements

* **Multi-File Projects:** Extend the agents' capabilities to handle more complex requests that require generating multiple, interacting Python files.
* **Enhanced Context Memory:** Improve the agents' ability to remember the full history of a debugging session to prevent them from re-introducing old bugs.
* **Front-End Workspace Viewer:** Add a feature to the Streamlit UI that allows the user to view the contents of the in-memory workspace in real-time.
