# Recipe Rescue

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

The `Docker Publish` workflow publishes application images to Docker Hub after changes are pushed to `main`.

- Backend: `iulian98/recipe-rescue-backend`
- Frontend: `iulian98/recipe-rescue-frontend`

Images published from `main` are tagged with:

- `latest`
- `sha-<12-character-commit-sha>`
- `build-<github-run-number>`

## Kubernetes Manifests

Kubernetes manifests live in `k8s/base` and `k8s/overlays` and define the first cloud deployment shape:

- frontend Deployment and Service
- backend Deployment and Service
- PostgreSQL StatefulSet and Service
- PostgreSQL persistent volume claim template
- application ConfigMap
- liveness and readiness probes
- staging, production-data, production-blue, and production-green overlays

The Kubernetes manifests are rendered in CI with:

```bash
kubectl kustomize k8s/base
kubectl kustomize k8s/overlays/staging
kubectl kustomize k8s/overlays/production-data
kubectl kustomize k8s/overlays/production-blue
kubectl kustomize k8s/overlays/production-green
kubeconform -strict -summary -ignore-missing-schemas rendered-manifests/*.yaml
kube-linter lint rendered-manifests/*.yaml
python scripts/check_k8s_policies.py rendered-manifests/*.yaml
```

The CI policy checks verify practical cluster-free rules: rendered manifests must not contain real Secrets, workload containers must define liveness/readiness probes and CPU/memory requests and limits, and Services must select an existing workload. kube-linter currently defers immutable image tag and full container runtime hardening checks until the GitOps image promotion phase.

The production blue-green structure separates application traffic from production data:

- `recipe-rescue-production-data`: the single shared production PostgreSQL database.
- `recipe-rescue-blue`: the blue production frontend/backend application color.
- `recipe-rescue-green`: the green production frontend/backend application color.

This keeps both production application colors isolated while avoiding two separate production databases. Blue and green are expected to connect to the same production database service in `recipe-rescue-production-data`.

Secret examples live in `k8s/secrets`. Copy these examples and create real Kubernetes Secrets in the cluster, but do not commit real secret values to Git.

For AWS/EKS, real secret values live in AWS Secrets Manager. External Secrets Operator reads those values and creates Kubernetes Secrets in the correct namespaces. This keeps passwords and GitHub tokens out of Git and out of ArgoCD manifests.

## ArgoCD GitOps

ArgoCD bootstrap manifests live in `argocd/bootstrap`, and child application manifests live in `argocd/applications`.

The ArgoCD structure follows an app-of-apps pattern:

- `recipe-rescue-root` watches `argocd/applications`.
- `recipe-rescue-staging` syncs `k8s/overlays/staging` from `staging`.
- `recipe-rescue-production-data` syncs `k8s/overlays/production-data` from `release`.
- `recipe-rescue-production-blue` syncs `k8s/overlays/production-blue` from `release`.
- `recipe-rescue-production-green` syncs `k8s/overlays/production-green` from `release`.

The `staging` branch stores the automatically deployed staging state after Docker images are published from `main`. The single `release` branch stores the manually approved production deployment state. The `Promote Release` workflow opens a PR from `main` into `release` for validation and human approval. After the PR is approved, the `Complete Release Promotion` workflow moves `release` to the exact same commit SHA as `main`, comments on the PR, closes it, and lets ArgoCD reconcile the production applications from `release`.

ArgoCD manifests are checked in CI with:

```bash
python scripts/check_argocd_manifests.py argocd/bootstrap/*.yaml argocd/applications/*.yaml
```

## AWS Infrastructure

Terraform infrastructure code lives in `infra/terraform/aws`. The first AWS layer creates a project VPC and an Amazon EKS cluster where ArgoCD and the Kubernetes application environments will run.

Terraform also installs the cluster platform services used by the deployment flow:

- ArgoCD through Helm
- External Secrets Operator through Helm
- EKS Pod Identity permissions for reading AWS Secrets Manager

Start with:

```bash
cd infra/terraform/aws
copy terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
```

See `infra/terraform/aws/README.md` for the full explanation of the Terraform files, AWS resources, and next deployment steps.

## CI/CD Flow

Pull requests to `main` run one orchestrator workflow named `PR Checks`. That workflow calls separate reusable check workflows from the `.github/workflows/check-*.yml` files, so the GitHub UI stays organized while each validation still has its own focused YAML file.

The reusable PR checks are:

- backend dependency consistency
- backend lint
- backend tests
- frontend dependency audit
- frontend lint
- frontend build
- Kubernetes render
- Kubernetes schema validation
- Kubernetes lint
- Kubernetes project policy
- ArgoCD manifest policy
- backend Docker image build
- frontend Docker image build

Pushes to `main` start the deployment side of the lifecycle:

1. `Docker Publish` builds and pushes frontend/backend images to Docker Hub.
2. `Deploy Staging` runs after Docker publishing succeeds.
3. `Deploy Staging` pins `k8s/overlays/staging` to the new `sha-<12-character-commit-sha>` image tag.
4. It pushes a normal commit to the `staging` branch.
5. ArgoCD syncs the staging application from the `staging` branch.

The `staging` branch is an automated deployment-state branch. It should not require manual PR approval, because it is updated by the `Deploy Staging` workflow after `main` has passed PR checks and Docker image publishing. If branch protection is enabled for `staging`, allow GitHub Actions to push to it.

Production promotion is manual:

1. Run the `Promote Release` workflow.
2. The workflow opens a normal PR from `main` into `release`.
3. Wait for release branch checks and human approval.
4. Run the `Complete Release Promotion` workflow with the release PR number.
5. The workflow verifies the PR, approvals, and checks, then updates `release` to the exact same commit SHA as `main`.
6. The workflow comments on and closes the PR, then ArgoCD syncs production from `release`.

Protect the `release` branch with required PR review, required release checks, and restricted direct pushes. The `Complete Release Promotion` workflow must be allowed to bypass the release branch update restriction, or it must use a fine-grained token stored as `RELEASE_PROMOTION_TOKEN`. This is required because the workflow intentionally moves the release branch pointer to the approved `main` commit.

Create the `release` branch once from `main` after the CI/CD workflow files are merged, then protect it. GitHub uses workflow files from the target branch for PR checks, so the release branch must contain `release-checks.yml` before promotion PRs can be validated.

Pull requests into `release` run deployment-readiness checks:

- Kubernetes render
- Kubernetes schema validation
- Kubernetes lint
- Kubernetes project policy
- ArgoCD manifest policy

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
- PR checks validate backend dependency consistency/lint/tests, frontend dependency audit/lint/build, Kubernetes manifests, ArgoCD manifests, and Docker image builds.
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
