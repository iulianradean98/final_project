# ArgoCD GitOps Manifests

This directory prepares Recipe Rescue for ArgoCD-based continuous delivery.

## Structure

- `bootstrap/recipe-rescue-project.yaml`: creates the ArgoCD project and limits where this application is allowed to deploy.
- `bootstrap/recipe-rescue-root-app.yaml`: root app-of-apps that syncs the child ArgoCD Applications from `argocd/applications`.
- `applications/recipe-rescue-dev.yaml`: syncs `k8s/overlays/dev`.
- `applications/recipe-rescue-production-blue.yaml`: syncs `k8s/overlays/production-blue`.
- `applications/recipe-rescue-production-green.yaml`: syncs `k8s/overlays/production-green`.

## Bootstrap Flow

After ArgoCD is installed in the cluster:

```bash
kubectl apply -f argocd/bootstrap/recipe-rescue-project.yaml
kubectl apply -f argocd/bootstrap/recipe-rescue-root-app.yaml
```

The root app then creates the dev, production-blue, and production-green ArgoCD Applications from Git.

The dev application is configured for automated sync, prune, and self-heal. Production blue and green are intentionally manual for now, so a new production color can be synced and tested before traffic is switched in a later blue-green routing step.
