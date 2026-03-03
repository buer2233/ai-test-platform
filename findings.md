# Findings & Decisions

## Requirements
- Compare traffic replay vs. AI doc/RAG for API test generation (pros/cons, feasibility)
- Provide detailed implementation process for both approaches
- Brainstorm and confirm requirements with user
- Both approaches must generate cases and be implemented
- Traffic capture via proxy (Python third-party library)
- Data desensitization not required now, but must reserve hook
- Documents are unified Markdown
- Flow is auto-generate + manual confirmation + execution/report analysis
- Need backend/frontend design and persist design doc in develop_document
- Need vector DB selection (deployment-friendly)

## Research Findings
- planning-with-files templates used to initialize task_plan.md, findings.md, progress.md
- Existing system supports API test cases, assertions, data extraction, variable pools, batch execution, and report views (see 09-test-case-feature-optimization.md)
- There is a separate "scenario" concept for chaining multiple API test cases with variable passing and execution records (see 09-test-scenario-feature.md)
- Scenario design includes step-level overrides, variable namespaces (env/global/scenario/step), retry/stop-on-failure, and execution records
- Read task_plan.md to confirm current phase and goals

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Start from develop_document materials | User request and likely contains domain context |
| Choose Qdrant for vector DB | Single-container deployment, easy ops, RESTful + Python SDK |
| Unified output to ApiTestCase + ApiTestScenario | Reuse existing execution/report pipeline |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
|       |            |

## Resources
- develop_document/09-test-case-feature-optimization.md
- develop_document/09-test-scenario-feature.md
- develop_document/12-api-testcase-auto-generation.md

## Visual/Browser Findings
-
