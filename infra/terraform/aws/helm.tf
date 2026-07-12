resource "helm_release" "external_secrets" {
  name       = "external-secrets"
  repository = "https://charts.external-secrets.io"
  chart      = "external-secrets"
  version    = var.external_secrets_chart_version
  namespace  = kubernetes_namespace.external_secrets.metadata[0].name

  wait    = true
  timeout = 600

  values = [
    yamlencode({
      installCRDs = true
      serviceAccount = {
        create = false
        name   = kubernetes_service_account.external_secrets.metadata[0].name
      }
    }),
  ]

  depends_on = [
    aws_eks_pod_identity_association.external_secrets,
  ]
}

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.argocd_chart_version
  namespace        = "argocd"
  create_namespace = true

  wait    = true
  timeout = 900

  values = [
    yamlencode({
      crds = {
        install = true
      }
      server = {
        service = {
          type = "ClusterIP"
        }
      }
    }),
  ]
}

resource "helm_release" "argo_rollouts" {
  name             = "argo-rollouts"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-rollouts"
  version          = var.argo_rollouts_chart_version
  namespace        = "argo-rollouts"
  create_namespace = true

  wait    = true
  timeout = 600

  values = [
    yamlencode({
      installCRDs = true
      keepCRDs    = false
      dashboard = {
        enabled = true
      }
    }),
  ]
}

resource "helm_release" "recipe_rescue_platform" {
  name      = "recipe-rescue-platform"
  chart     = "${path.module}/charts/recipe-rescue-platform"
  namespace = "argocd"

  wait    = true
  timeout = 300

  values = [
    yamlencode({
      awsRegion              = var.aws_region
      argocdGithubRepoSecret = var.argocd_github_repo_secret_name
      repoUrl                = var.github_repo_url
      rootTargetRevision     = var.argocd_root_target_revision
    }),
  ]

  depends_on = [
    helm_release.argocd,
    helm_release.argo_rollouts,
    helm_release.external_secrets,
  ]
}
