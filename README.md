# Recipe Rescue

[![CI](https://github.com/iulianradean98/final_project/actions/workflows/ci.yml/badge.svg)](https://github.com/iulianradean98/final_project/actions/workflows/ci.yml)

Recipe Rescue is a professional 3-tier web application for a DevOps capstone project. It helps users track pantry ingredients and discover recipes they can cook with what they already have.

## Current Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI REST API
- Database: PostgreSQL
- Local runtime: Docker Compose

## Architecture

```text
Browser
  -> React multipage frontend served by Nginx
  -> Nginx /api proxy
  -> FastAPI REST API
  -> PostgreSQL database
```

The frontend runs on `http://localhost:3001` when started through Docker Compose. The API runs on `http://localhost:8000`, and PostgreSQL is exposed on `localhost:5433` for local development because many machines already have a local PostgreSQL service on `5432`.

The frontend calls `/api` in the browser. Nginx proxies those requests to the backend service, which keeps the same frontend image usable in Docker Compose and Kubernetes.

## Run Locally With Docker

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3001
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health
- Readiness check: http://localhost:8000/api/ready

## Docker Images

The CI/CD pipeline publishes application images to Docker Hub after the `CI` workflow succeeds on `main`.

- Backend: `iulian98/recipe-rescue-backend`
- Frontend: `iulian98/recipe-rescue-frontend`

Each image is tagged with:

- `latest`
- `sha-<commit-sha>`

## Kubernetes Manifests

Kubernetes manifests live in `k8s/base` and define the first cloud deployment shape:

- frontend Deployment and Service
- backend Deployment and Service
- PostgreSQL StatefulSet and Service
- PostgreSQL persistent volume claim template
- application ConfigMap
- liveness and readiness probes

The Kubernetes base is rendered in CI with:

```bash
kubectl kustomize k8s/base
kubeconform -strict -summary -ignore-missing-schemas rendered-manifests.yaml
kube-linter lint rendered-manifests.yaml
python scripts/check_k8s_policies.py rendered-manifests.yaml
```

The CI policy checks verify practical cluster-free rules: the base must not render real Secrets, workload containers must define liveness/readiness probes and CPU/memory requests and limits, and Services must select an existing workload. kube-linter currently defers immutable image tag and full container runtime hardening checks until the GitOps image promotion phase.

Secret examples live in `k8s/secrets`. Copy these examples and create real Kubernetes Secrets in the cluster, but do not commit real secret values to Git.

## Application Pages

- Home: landing page with project summary and navigation.
- Login / Sign Up: account pages for user-specific pantry and custom recipe data.
- Recipes: public catalogue where users can inspect all recipes and exact required ingredients before stocking their pantry.
- Pantry: add and remove ingredients with quantity, measure unit, description, category, and expiry date.
- Find Recipes: search/filter pantry ingredients, build a cooking basket, choose a meal type, and compare selected-ingredient matches, ready pantry recommendations, and recipes that need extra ingredients. Recipe cards distinguish selected ingredients, available pantry ingredients, low-stock ingredients, and truly missing ingredients.
- Recipe Details: view exact recipe ingredient quantities, detailed preparation steps, and finish preparation.
- Add Recipe: create custom recipes with ingredient quantities and a meal type tag.

## Core Business Flow

1. The user signs up or logs in.
2. The user adds pantry ingredients to their own account.
3. The user selects product categories and friendly measure units while managing pantry stock.
4. The user selects ingredients and a meal type: `breakfast`, `lunch`, `dinner`, or `snack`.
5. The API compares selected pantry stock with recipe requirements.
6. The frontend displays three result sections: selected-ingredient matches, ready pantry recommendations, and recipes that need extra ingredients.
7. The user opens a recipe and clicks `Finish and update stock`.
8. The backend validates stock and deducts the exact required ingredient quantities from PostgreSQL.

The seeded database currently contains 20 recipes across all meal types, including recipes that intentionally use ingredients not present in the demo pantry so missing-ingredient behavior can be demonstrated.

## Demo Account

For a quick walkthrough, use:

- Email: `demo@reciperescue.local`
- Password: `demo123`

The demo user owns the seeded pantry inventory. Built-in recipes are public, while new ingredients and custom recipes are tied to the logged-in user.

## Useful API Endpoints

- `GET /api/health`
- `GET /api/ready`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/ingredients`
- `POST /api/ingredients`
- `DELETE /api/ingredients/{ingredient_id}`
- `GET /api/recipes`
- `GET /api/recipes/{recipe_id}`
- `POST /api/recipes`
- `POST /api/recipes/matches`
- `POST /api/recipes/{recipe_id}/finish`

## Why This Project Works Well For DevOps

- The application has three clear tiers, which makes containerization and deployment easy to explain.
- The REST API has testable endpoints plus separate health and readiness endpoints for CI/CD and Kubernetes probes.
- CI validates backend dependency consistency/tests, frontend dependency audit/lint/build, Kubernetes manifests, and Docker image builds.
- PostgreSQL gives the project real persistence.
- The UI has visible behavior changes, which is useful when demonstrating staging and Blue/Green production deployments.

## Planned DevOps Expansion

- GitHub repository with branch strategy.
- Jenkins CI pipeline for linting and tests.
- Docker image publishing to Docker Hub.
- Kubernetes manifests for frontend, backend, and PostgreSQL.
- ArgoCD for GitOps-based continuous deployment.
- AWS infrastructure using Terraform, with Ansible only if configuration automation becomes useful.
- Optional Prometheus and Grafana monitoring after the deployment flow is stable.
