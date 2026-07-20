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
- production Nginx edge router Deployment and LoadBalancer Service
- PostgreSQL StatefulSet and Service
- PostgreSQL persistent volume claim template
- application ConfigMap
- liveness and readiness probes
- staging, production-data, and production overlays

The Kubernetes manifests are rendered in CI with:

```bash
kubectl kustomize k8s/base
kubectl kustomize k8s/overlays/staging
kubectl kustomize k8s/overlays/production-data
kubectl kustomize k8s/overlays/production
kubeconform -strict -summary -ignore-missing-schemas rendered-manifests/*.yaml
kube-linter lint rendered-manifests/*.yaml
python scripts/check_k8s_policies.py rendered-manifests/*.yaml
```

The CI policy checks verify practical cluster-free rules: rendered manifests must not contain real Secrets, workload containers must define liveness/readiness probes and CPU/memory requests and limits, and Services must select an existing workload. kube-linter currently defers immutable image tag and full container runtime hardening checks until the GitOps image promotion phase.

The production blue-green structure separates application traffic from production data:

- `recipe-rescue-production-data`: the single shared production PostgreSQL database.
- `recipe-rescue-production`: the production frontend/backend namespace managed by Argo Rollouts.

Argo Rollouts manages the blue and green application states as ReplicaSets behind active and preview Services. A dedicated production Nginx edge router is exposed through the AWS LoadBalancer and proxies traffic to the active frontend/backend Services. During a deployment, preview Services expose the new ReplicaSet for smoke tests; after those tests pass, Argo Rollouts switches the active Services that Nginx routes to. Both colors use the same production database service in `recipe-rescue-production-data`.

Before the production backend Rollout promotes the preview ReplicaSet to active traffic, Argo Rollouts runs a pre-promotion PostgreSQL backup job. That job writes a deployment safety backup to `s3://<backup-bucket>/recipe-rescue/production/prepromotion/`. If the backup fails, the backend traffic switch does not happen.

The frontend Rollout also runs a pre-promotion backend rollout-state check. It waits until the backend Rollout is healthy and its current ReplicaSet is the stable ReplicaSet. This prevents a frontend traffic switch when the matching backend deployment failed or is still progressing.

Real secret values live in AWS Secrets Manager. External Secrets Operator reads those values and creates Kubernetes Secrets in the correct namespaces. This keeps passwords and GitHub tokens out of Git and out of ArgoCD manifests.

The `k8s/secrets` directory documents the expected secret flow and contains placeholder examples only. Those examples are not used by the AWS/EKS deployment.

## ArgoCD GitOps

ArgoCD bootstrap manifests live in `argocd/bootstrap`, and child application manifests live in `argocd/applications`.

The ArgoCD structure follows an app-of-apps pattern:

- `recipe-rescue-root` watches `argocd/applications`.
- `recipe-rescue-staging` syncs `k8s/overlays/staging` from `staging`.
- `recipe-rescue-production-data` syncs `k8s/overlays/production-data` from `release`.
- `recipe-rescue-production` syncs `k8s/overlays/production` from `release`.

The `staging` branch stores the automatically deployed staging state after Docker images are published from `main`. The single `release` branch stores the approved production deployment state. The `Promote Release` workflow opens a PR from `main` into `release` for validation and human approval. After the PR is approved and release checks pass, the `Complete Release Promotion` workflow moves `release` to the approved application commit, pins `k8s/overlays/production` to the matching `sha-<commit>` Docker image tag, comments on the PR, closes it when GitHub allows that cleanup, and lets ArgoCD reconcile production from `release`.

ArgoCD manifests are checked in CI with:

```bash
python scripts/check_argocd_manifests.py argocd/bootstrap/*.yaml argocd/applications/*.yaml
```

## AWS Infrastructure

Terraform infrastructure code lives in `infra/terraform/aws`. The first AWS layer creates a project VPC and an Amazon EKS cluster where ArgoCD and the Kubernetes application environments will run.

Terraform also installs the cluster platform services used by the deployment flow:

- ArgoCD through Helm
- Argo Rollouts through Helm for automated blue-green production deployments
- External Secrets Operator through Helm
- EKS Pod Identity permissions for reading AWS Secrets Manager
- EKS Pod Identity permissions for PostgreSQL backup/restore jobs that use the external S3 backup bucket

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
6. `Staging Live Tests` waits for the live staging workloads, resolves the staging LoadBalancer URL, tests the frontend, health/readiness endpoints, signup/auth flow, and recipes API.

The `staging` branch is an automated deployment-state branch. It should not require manual PR approval, because it is updated by the `Deploy Staging` workflow after `main` has passed PR checks and Docker image publishing. If branch protection is enabled for `staging`, allow GitHub Actions to push to it.

Production promotion is approval-gated and deployment is automated:

1. Run the `Promote Release` workflow.
2. The workflow opens a normal PR from `main` into `release`.
3. Wait for release branch checks and human approval.
4. The `Complete Release Promotion` workflow starts automatically after the missing condition arrives: either approval after checks, or checks after approval.
5. The workflow verifies the PR, approvals, and checks, then updates `release` to the approved `main` application SHA.
6. The workflow pins production images on `release` to the matching `sha-<12-character-commit-sha>` Docker tag.
7. The workflow comments on and closes the PR when GitHub allows it.
8. ArgoCD syncs production from `release`.
9. Argo Rollouts creates the preview ReplicaSet, runs smoke tests, switches active Services behind the production Nginx router, keeps the old ReplicaSet for 10 minutes, and rolls back automatically if post-promotion health checks fail.

The `Complete Release Promotion` workflow can also be run manually with the release PR number if an automatic trigger needs to be retried.

Protect the `release` branch with required PR review, required release checks, and restricted direct pushes. The `Complete Release Promotion` workflow must be allowed to bypass the release branch update restriction, or it must use a fine-grained token stored as `RELEASE_PROMOTION_TOKEN`. This is required because the workflow intentionally moves the release branch pointer to the approved `main` commit and then writes the production deployment-state commit.

Create the `release` branch once from `main` after the CI/CD workflow files are merged, then protect it. GitHub uses workflow files from the target branch for PR checks, so the release branch must contain `release-checks.yml` before promotion PRs can be validated.

Pull requests into `release` run deployment-readiness checks:

- Kubernetes render
- Kubernetes schema validation
- Kubernetes lint
- Kubernetes project policy
- ArgoCD manifest policy

## Database Backups And Disaster Recovery

PostgreSQL data is protected in two layers:

- normal runtime persistence through Kubernetes PVCs backed by AWS EBS volumes
- disaster-recovery backups through scheduled PostgreSQL dumps uploaded to S3

The S3 backup bucket is intentionally created outside the destroyable EKS Terraform stack, similar to the Terraform state bucket. The cluster can be destroyed and recreated while the database backups remain available.

ArgoCD deploys database backup CronJobs:

- staging writes to `s3://<backup-bucket>/recipe-rescue/staging/`
- production writes to `s3://<backup-bucket>/recipe-rescue/production/`
- production pre-promotion backups write to `s3://<backup-bucket>/recipe-rescue/production/prepromotion/`

The infrastructure recovery workflow can optionally restore `latest.sql.gz` after rebuilding the platform. This gives the capstone a complete recovery story: Terraform recreates AWS/EKS, ArgoCD redeploys the app, and the recovery workflow can restore PostgreSQL data from S3.

## Monitoring

The AWS/EKS platform includes a minimal monitoring stack installed by Terraform:

- `kube-prometheus-stack`: Prometheus, Grafana, Prometheus Operator, kube-state-metrics, and node-exporter.
- `prometheus-blackbox-exporter`: HTTP probes for live application endpoints.
- `Recipe Rescue Overview` Grafana dashboard: endpoint health, running pods, restarts, database readiness, and ArgoCD/Rollouts controller visibility.
- Optional Alertmanager email notifications through AWS SES SMTP.

Grafana and Prometheus are internal `ClusterIP` services. They are not exposed publicly through AWS LoadBalancers. For demo access, use port-forwarding:

```powershell
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/monitoring-prometheus -n monitoring 9090:9090
```

Open Grafana at:

```text
http://localhost:3000
```

Default demo login:

- User: `admin`
- Password: `recipe-rescue-admin`

Prometheus probes the staging and production frontend/backend readiness endpoints every 30 seconds. If an endpoint stays down for more than 2 minutes, the `RecipeRescueEndpointDown` alert becomes active. When `ENABLE_EMAIL_ALERTS=true` and SES SMTP credentials are configured in GitHub secrets, Alertmanager also sends the notification by email. This monitoring layer complements the existing self-healing mechanisms: Kubernetes probes restart unhealthy containers, Argo Rollouts blocks or aborts unsafe releases, ArgoCD restores Git drift, and Terraform recovery can recreate infrastructure.

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

## Completed DevOps Scope

- GitHub repository with branch strategy and protected PR-based promotion.
- GitHub Actions CI for linting, tests, Docker builds, Kubernetes validation, and ArgoCD policy checks.
- Docker image publishing to DockerHub with `latest`, `sha-...`, and `build-...` tags.
- Kubernetes manifests for frontend, backend, PostgreSQL, backups, and production Rollouts.
- ArgoCD GitOps-based continuous deployment for staging and production.
- Argo Rollouts blue-green production deployment with smoke tests, pre-promotion database backup, post-promotion checks, and rollback protection.
- AWS infrastructure using Terraform.
- AWS Secrets Manager and External Secrets Operator for cloud secret delivery.
- S3 PostgreSQL backups and infrastructure recovery workflows.
- Prometheus and Grafana monitoring with blackbox endpoint probes.
