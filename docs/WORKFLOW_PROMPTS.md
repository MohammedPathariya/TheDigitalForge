# Digital Forge Prompt Playbook

Use a new Codex task for each phase. Start with Terra Medium unless the phase is explicitly marked as Sol work below. Keep prompts scoped to one outcome and ask for verification before committing.

## Start a phase

Use this for Days 1, 2, 5, 6, and 7 with Terra Medium. Use Sol Medium for Days 3 and 4.

```text
Continue The Digital Forge revamp on the current branch.

Read AGENTS.md, docs/WEEK_PLAN.md, docs/ARCHITECTURE.md, docs/DECISIONS.md, and docs/STATUS.md. Inspect the current Git status and relevant code before editing.

Implement Day [N]: [phase name] only. Keep the diff focused, preserve unrelated work, and follow existing project conventions. Run the relevant tests, linting, and type checks. Update docs/STATUS.md with completed work, verification, risks, and the exact next task. Do not commit, push, or deploy unless I explicitly ask.
```

## Sol end-of-phase review

Use Sol Medium after a phase is implemented and locally verified. Skip or defer it if the five-hour allowance is low.

```text
Perform a focused end-of-phase review of The Digital Forge current branch.

Read docs/WEEK_PLAN.md, docs/ARCHITECTURE.md, docs/DECISIONS.md, docs/STATUS.md, and the current Git diff. Verify that Day [N]: [phase name] is complete and consistent with the documented architecture.

Find only blocking correctness, security, benchmark-integrity, deployment, or integration issues. Run the relevant checks. Fix confirmed issues with the smallest possible diff, rerun verification, and update docs/STATUS.md. Do not commit, push, or deploy unless I explicitly ask.
```

## Resume after a break

```text
Resume The Digital Forge revamp from the current repository state.

Read docs/STATUS.md first, then inspect Git status, recent commits, and the relevant source files. Summarize the exact current state in five bullets or fewer, identify the next documented task, and implement only that task. Verify the result and update docs/STATUS.md. Do not commit, push, or deploy unless I explicitly ask.
```

## Diagnose a failure

Use Terra Medium first. Escalate to Sol Medium only if the failure remains unclear after the initial investigation.

```text
Diagnose this Digital Forge failure without making unrelated changes.

Read docs/STATUS.md, the relevant implementation, test output, and Git diff. Identify the root cause, explain whether it is code, test, configuration, dependency, or infrastructure behavior, and propose the smallest correct fix. Implement the fix, run the relevant checks, and update docs/STATUS.md with the result. Do not commit, push, or deploy unless I explicitly ask.

Failure output:
[paste output]
```

## Commit a verified phase

```text
Review the current Digital Forge changes for Day [N]. Confirm Git status, inspect the diff, and run the relevant checks. If verification passes, update docs/STATUS.md if needed, stage only files belonging to this phase, and create a concise imperative commit. Do not push or open a pull request.
```

## Prepare a pull request

```text
Prepare the current Digital Forge branch for a pull request into main. Inspect the commits and diff against main, run the relevant checks, identify unresolved risks, and draft a concise pull request title and description. Do not push, open, merge, or delete branches unless I explicitly ask.
```

## Low-usage planning

Use Luna or Terra Low.

```text
Read docs/STATUS.md and docs/WEEK_PLAN.md. Do not edit files. Give a concise plan for the next phase, including the files likely to change, verification commands, and the main risks.
```
