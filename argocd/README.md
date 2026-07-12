# ArgoCD GitOps Manifests

This directory prepares Recipe Rescue for ArgoCD-based continuous delivery.

## Structure

- `bootstrap/recipe-rescue-project.yaml`: creates the ArgoCD project and limits where this application is allowed to deploy.
- `bootstrap/recipe-rescue-root-app.yaml`: root app-of-apps that syncs the child ArgoCD Applications from `argocd/applications`.
- `applications/recipe-rescue-staging.yaml`: syncs `k8s/overlays/staging` from `staging`.
- `applications/recipe-rescue-production-data.yaml`: syncs the shared production PostgreSQL database from `release`.
- `applications/recipe-rescue-production.yaml`: syncs `k8s/overlays/production` from `release`.

## Bootstrap Flow

After ArgoCD is installed in the cluster:

```bash
kubectl apply -f argocd/bootstrap/recipe-rescue-project.yaml
kubectl apply -f argocd/bootstrap/recipe-rescue-root-app.yaml
```

In the AWS/EKS environment, ArgoCD itself is installed by Terraform using Helm. Terraform also installs External Secrets Operator and creates the ArgoCD repository credential from AWS Secrets Manager.

The root app then creates the staging, production-data, and production ArgoCD Applications from Git.

Production uses one shared database namespace plus one rollout-managed application namespace:

- `recipe-rescue-production-data`: shared production PostgreSQL.
- `recipe-rescue-production`: frontend/backend Rollout resources, active services, preview services, Nginx edge router, and smoke-test AnalysisTemplates.

Blue and green are managed inside the production namespace by Argo Rollouts. The production Nginx edge router is the stable external entry point. It proxies traffic to active services, and those active services route to the stable ReplicaSet. Preview services expose the next ReplicaSet for smoke tests before traffic is switched.

The child applications are configured for automated sync, prune, and self-heal. Staging is updated automatically through the `Deploy Staging` workflow after Docker images are published from `main`; ArgoCD watches the `staging` branch for that environment. Production approval happens through a protected PR from `main` into the single `release` branch. After the PR is approved, the `Complete Release Promotion` workflow moves `release` to the approved application commit, pins the production image tag, and ArgoCD reconciles production from `release`.

Argo Rollouts then performs the production blue-green flow automatically:

1. Create the new preview ReplicaSet.
2. Run pre-promotion smoke tests against preview services.
3. Switch active services to the new ReplicaSet if smoke tests pass; the Nginx router automatically reaches the new version through those active services.
4. Run 10 minutes of post-promotion health checks.
5. Abort and roll back to the previous ReplicaSet if post-promotion checks fail.

Create the `release` branch once from `main` after the workflow files are merged. Then protect it and require release PR checks plus human approval before merge.
