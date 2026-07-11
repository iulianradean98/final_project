# Secret Strategy

Real secret values must not be committed to Git.

Recipe Rescue uses AWS Secrets Manager as the source of truth for cloud secrets. Kubernetes Secrets are created from those AWS secrets by External Secrets Operator.

The intended AWS Secrets Manager entries are:

- `recipe-rescue/argocd/github-repo`: read-only GitHub token for ArgoCD.
- `recipe-rescue/staging/app`: staging database and backend secret values.
- `recipe-rescue/production/app`: shared production database and backend secret values.

Production uses one shared database secret for both blue and green. Blue and green are application colors, not separate production databases.

Expected Kubernetes Secrets:

- `recipe-rescue-staging/recipe-rescue-postgres-secret`
- `recipe-rescue-staging/recipe-rescue-api-secret`
- `recipe-rescue-production-data/recipe-rescue-postgres-secret`
- `recipe-rescue-blue/recipe-rescue-api-secret`
- `recipe-rescue-green/recipe-rescue-api-secret`
- `argocd/recipe-rescue-repo`

How the flow works:

1. Terraform installs External Secrets Operator.
2. Terraform gives the operator AWS access using EKS Pod Identity and a least-privilege IAM role.
3. Terraform creates a `ClusterSecretStore` named `recipe-rescue-aws-secrets`.
4. Kustomize overlays define `ExternalSecret` resources.
5. External Secrets Operator reads AWS Secrets Manager and creates normal Kubernetes Secrets for the pods.
