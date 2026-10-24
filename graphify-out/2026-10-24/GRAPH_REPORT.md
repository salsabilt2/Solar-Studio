# Graph Report - Photovoltaic_project  (2026-10-21)

## Corpus Check
- 40 files · ~17,547 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 383 nodes · 975 edges · 11 communities (10 shown, 1 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 121 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Frontend Experience
- Reports and Weather
- Accounts and Access
- API and Database
- Tests and Evaluation
- Frontend Tooling
- AI Document Assistant
- Requirements and Deployment
- Database Migrations
- TypeScript Settings
- Project Identity

## God Nodes (most connected - your core abstractions)
1. `User` - 54 edges
2. `Setup` - 22 edges
3. `Panel` - 20 edges
4. `fetch_weather()` - 19 edges
5. `Solar Studio` - 16 edges
6. `Project` - 15 edges
7. `Base` - 15 edges
8. `Document` - 15 edges
9. `compilerOptions` - 15 edges
10. `ProjectPage()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `AI Evaluation Plan` --semantically_similar_to--> `AI Evaluation and Observability`  [INFERRED] [semantically similar]
  docs/ai-evaluation.md → Roadmap AI Engineering .pdf
- `Forty-Question RAG Benchmark` --semantically_similar_to--> `Document Retrieval Assistant`  [INFERRED] [semantically similar]
  docs/ai-evaluation.md → README.md
- `FastAPI` --semantically_similar_to--> `Python and FastAPI`  [INFERRED] [semantically similar]
  README.md → Roadmap AI Engineering .pdf
- `PostgreSQL and pgvector` --semantically_similar_to--> `RAG and Vector Databases`  [INFERRED] [semantically similar]
  README.md → Roadmap AI Engineering .pdf
- `Document Retrieval Assistant` --semantically_similar_to--> `RAG and Vector Databases`  [INFERRED] [semantically similar]
  README.md → Roadmap AI Engineering .pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Solar Studio Quality and Runtime Workflows** — github_workflows_ci_ci, github_workflows_nightly_nightly_solar_jobs, compose_local_stack, render_solar_studio_deployment [INFERRED 0.75]

## Communities (11 total, 1 thin omitted)

### Community 0 - "Frontend Experience"
Cohesion: 0.06
Nodes (45): api(), Daily, Estimate, json(), navigate(), Panel, Project, Report (+37 more)

### Community 1 - "Reports and Weather"
Cohesion: 0.11
Nodes (26): Base, demo(), run_due(), Report, Setup, utcnow(), WeatherCache, create_report() (+18 more)

### Community 2 - "Accounts and Access"
Cohesion: 0.15
Nodes (42): make_token(), public_user(), verify_password(), Panel, Project, User, admin_users(), company_panels() (+34 more)

### Community 3 - "API and Database"
Cohesion: 0.07
Nodes (10): current_user(), require_role(), Settings, get_db(), init_db(), check_browser_origin(), frontend(), health() (+2 more)

### Community 4 - "Tests and Evaluation"
Cohesion: 0.09
Nodes (19): fixture_pdf(), main(), client(), create_setup(), fixture_pdf(), register(), sample_weather(), test_account_project_limits_and_private_data() (+11 more)

### Community 5 - "Frontend Tooling"
Cohesion: 0.05
Nodes (36): dependencies, @fontsource/dm-sans, @fontsource/manrope, leaflet, lucide-react, motion, react, react-dom (+28 more)

### Community 6 - "AI Document Assistant"
Cohesion: 0.16
Nodes (20): ask(), client(), compare_setup(), CompareIn, cosine(), document_out(), download_document(), embed() (+12 more)

### Community 7 - "Requirements and Deployment"
Cohesion: 0.09
Nodes (22): Local PostgreSQL and Mailpit Stack, AI Evaluation Plan, Forty-Question RAG Benchmark, Solar Studio Engineering Case Study, Solar Studio Web Page, Continuous Integration Workflow, Nightly Solar Jobs Workflow, Backend, API, Frontend, and Database Architecture (+14 more)

### Community 8 - "Database Migrations"
Cohesion: 0.16
Nodes (4): upgrade(), upgrade(), upgrade(), upgrade()

### Community 9 - "TypeScript Settings"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+8 more)

## Knowledge Gaps
- **15 isolated node(s):** `@fontsource/dm-sans`, `@fontsource/manrope`, `prettier`, `@types/leaflet`, `@types/react` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 123 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Accounts and Access` to `Reports and Weather`, `API and Database`, `Tests and Evaluation`, `AI Document Assistant`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 45 inferred relationships involving `User` (e.g. with `ask()` and `compare_setup()`) actually correct?**
  _`User` has 45 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@fontsource/dm-sans`, `@fontsource/manrope`, `prettier` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Experience` be split into smaller, more focused modules?**
  _Cohesion score 0.05921325051759834 - nodes in this community are weakly interconnected._
- **Why does `react` connect `Frontend Experience` to `Frontend Tooling`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Setup` (e.g. with `demo()` and `list_reports()`) actually correct?**
  _`Setup` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `Reports and Weather` be split into smaller, more focused modules?**
  _Cohesion score 0.10901960784313726 - nodes in this community are weakly interconnected._