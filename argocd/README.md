# ArgoCD GitOps Manifests

This directory prepares Recipe Rescue for ArgoCD-based continuous delivery.

## Structure

- `bootstrap/recipe-rescue-project.yaml`: creates the ArgoCD project and limits where this application is allowed to deploy.
- `bootstrap/recipe-rescue-root-app.yaml`: root app-of-apps that syncs the child ArgoCD Applications from `argocd/applications`.
- `applications/recipe-rescue-staging.yaml`: syncs `k8s/overlays/staging` from `staging`.
- `applications/recipe-rescue-production-blue.yaml`: syncs `k8s/overlays/production-blue` from `release`.
- `applications/recipe-rescue-production-green.yaml`: syncs `k8s/overlays/production-green` from `release`.

## Bootstrap Flow

After ArgoCD is installed in the cluster:

```bash
kubectl apply -f argocd/bootstrap/recipe-rescue-project.yaml
kubectl apply -f argocd/bootstrap/recipe-rescue-root-app.yaml
```

The root app then creates the staging, production-blue, and production-green ArgoCD Applications from Git.

The child applications are configured for automated sync, prune, and self-heal. Staging is updated automatically through the `Deploy Staging` workflow after Docker images are published from `main`; ArgoCD watches the `staging` branch for that environment. Manual production approval happens through a protected PR from `main` into the single `release` branch. After the PR is approved and merged, ArgoCD automatically reconciles production from `release`.

Create the `release` branch once from `main` after the workflow files are merged. Then protect it and require release PR checks plus human approval before merge.
