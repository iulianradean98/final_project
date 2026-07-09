# ArgoCD GitOps Manifests

This directory prepares Recipe Rescue for ArgoCD-based continuous delivery.

## Structure

- `bootstrap/recipe-rescue-project.yaml`: creates the ArgoCD project and limits where this application is allowed to deploy.
- `bootstrap/recipe-rescue-root-app.yaml`: root app-of-apps that syncs the child ArgoCD Applications from `argocd/applications`.
- `applications/recipe-rescue-dev.yaml`: syncs `k8s/overlays/dev` from `release/dev`.
- `applications/recipe-rescue-production-blue.yaml`: syncs `k8s/overlays/production-blue` from `release/production-blue`.
- `applications/recipe-rescue-production-green.yaml`: syncs `k8s/overlays/production-green` from `release/production-green`.

## Bootstrap Flow

After ArgoCD is installed in the cluster:

```bash
kubectl apply -f argocd/bootstrap/recipe-rescue-project.yaml
kubectl apply -f argocd/bootstrap/recipe-rescue-root-app.yaml
```

The root app then creates the dev, production-blue, and production-green ArgoCD Applications from Git.

The child applications are configured for automated sync, prune, and self-heal. Manual approval happens before deployment in GitHub Actions through the `Promote Release` workflow. After approval, that workflow updates the correct release branch with an immutable image tag, and ArgoCD automatically reconciles the matching environment.
