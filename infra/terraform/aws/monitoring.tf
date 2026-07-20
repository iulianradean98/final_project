resource "kubernetes_namespace_v1" "monitoring" {
  metadata {
    name = "monitoring"

    labels = {
      "app.kubernetes.io/name"       = "monitoring"
      "app.kubernetes.io/part-of"    = var.project_name
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

locals {
  recipe_rescue_blackbox_targets = [
    {
      name        = "staging-frontend"
      environment = "staging"
      component   = "frontend"
      url         = "http://recipe-rescue-web.recipe-rescue-staging.svc.cluster.local/"
    },
    {
      name        = "staging-backend-ready"
      environment = "staging"
      component   = "backend"
      url         = "http://recipe-rescue-web.recipe-rescue-staging.svc.cluster.local/api/ready"
    },
    {
      name        = "production-frontend"
      environment = "production"
      component   = "frontend"
      url         = "http://recipe-rescue-router.recipe-rescue-production.svc.cluster.local/"
    },
    {
      name        = "production-backend-ready"
      environment = "production"
      component   = "backend"
      url         = "http://recipe-rescue-router.recipe-rescue-production.svc.cluster.local/api/ready"
    },
  ]

  recipe_rescue_dashboard = {
    uid                  = "recipe-rescue-overview"
    title                = "Recipe Rescue Overview"
    tags                 = ["recipe-rescue", "devops", "monitoring"]
    timezone             = "browser"
    schemaVersion        = 39
    version              = 1
    refresh              = "30s"
    editable             = true
    graphTooltip         = 0
    fiscalYearStartMonth = 0
    time = {
      from = "now-1h"
      to   = "now"
    }
    templating = {
      list = []
    }
    annotations = {
      list = [
        {
          builtIn    = 1
          datasource = { type = "grafana", uid = "-- Grafana --" }
          enable     = true
          hide       = true
          iconColor  = "rgba(0, 211, 255, 1)"
          name       = "Annotations & Alerts"
          type       = "dashboard"
        }
      ]
    }
    panels = [
      {
        id         = 1
        title      = "HTTP probes up"
        type       = "stat"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 5, w = 6, x = 0, y = 0 }
        fieldConfig = {
          defaults = {
            unit     = "short"
            decimals = 0
            thresholds = {
              mode = "absolute"
              steps = [
                { color = "red", value = null },
                { color = "green", value = 1 }
              ]
            }
            mappings = [
              {
                type = "value"
                options = {
                  "0" = { text = "DOWN" }
                  "1" = { text = "UP" }
                }
              }
            ]
          }
          overrides = []
        }
        options = {
          colorMode   = "background"
          graphMode   = "area"
          justifyMode = "auto"
          orientation = "auto"
          reduceOptions = {
            calcs  = ["lastNotNull"]
            fields = ""
            values = false
          }
          textMode = "auto"
        }
        targets = [
          {
            refId        = "A"
            expr         = "min(probe_success{job=\"recipe-rescue-http-probes\"})"
            legendFormat = "all endpoints"
          }
        ]
      },
      {
        id         = 2
        title      = "Recipe Rescue running pods"
        type       = "stat"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 5, w = 6, x = 6, y = 0 }
        fieldConfig = {
          defaults = {
            color = { mode = "palette-classic" }
            unit  = "short"
          }
          overrides = []
        }
        options = {
          colorMode = "value"
          graphMode = "area"
          reduceOptions = {
            calcs  = ["lastNotNull"]
            fields = ""
            values = false
          }
          textMode = "auto"
        }
        targets = [
          {
            refId        = "A"
            expr         = "sum(kube_pod_status_phase{namespace=~\"recipe-rescue-.*\",phase=\"Running\"})"
            legendFormat = "running pods"
          }
        ]
      },
      {
        id         = 3
        title      = "Endpoint probe status"
        type       = "timeseries"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 8, w = 12, x = 12, y = 0 }
        fieldConfig = {
          defaults = {
            custom = {
              drawStyle         = "line"
              lineInterpolation = "stepAfter"
              lineWidth         = 2
              fillOpacity       = 10
              showPoints        = "never"
            }
            min  = 0
            max  = 1
            unit = "short"
          }
          overrides = []
        }
        options = {
          legend  = { displayMode = "table", placement = "bottom", showLegend = true }
          tooltip = { mode = "multi", sort = "none" }
        }
        targets = [
          {
            refId        = "A"
            expr         = "probe_success{job=\"recipe-rescue-http-probes\"}"
            legendFormat = "{{environment}} {{component}}"
          }
        ]
      },
      {
        id         = 4
        title      = "Running pods by namespace"
        type       = "timeseries"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 8, w = 12, x = 0, y = 5 }
        fieldConfig = {
          defaults = {
            custom = {
              drawStyle   = "line"
              lineWidth   = 2
              fillOpacity = 10
              showPoints  = "never"
            }
            unit = "short"
          }
          overrides = []
        }
        options = {
          legend  = { displayMode = "table", placement = "bottom", showLegend = true }
          tooltip = { mode = "multi", sort = "none" }
        }
        targets = [
          {
            refId        = "A"
            expr         = "sum(kube_pod_status_phase{namespace=~\"recipe-rescue-.*|argocd|argo-rollouts|monitoring\",phase=\"Running\"}) by (namespace)"
            legendFormat = "{{namespace}}"
          }
        ]
      },
      {
        id         = 5
        title      = "Container restarts in last 15 minutes"
        type       = "timeseries"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 8, w = 12, x = 12, y = 8 }
        fieldConfig = {
          defaults = {
            custom = {
              drawStyle   = "bars"
              lineWidth   = 1
              fillOpacity = 40
              showPoints  = "never"
            }
            unit = "short"
          }
          overrides = []
        }
        options = {
          legend  = { displayMode = "table", placement = "bottom", showLegend = true }
          tooltip = { mode = "multi", sort = "none" }
        }
        targets = [
          {
            refId        = "A"
            expr         = "sum(increase(kube_pod_container_status_restarts_total{namespace=~\"recipe-rescue-.*|argocd|argo-rollouts|monitoring\"}[15m])) by (namespace)"
            legendFormat = "{{namespace}}"
          }
        ]
      },
      {
        id         = 6
        title      = "Production database pod ready"
        type       = "stat"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 5, w = 6, x = 0, y = 13 }
        fieldConfig = {
          defaults = {
            unit     = "short"
            decimals = 0
            thresholds = {
              mode = "absolute"
              steps = [
                { color = "red", value = null },
                { color = "green", value = 1 }
              ]
            }
          }
          overrides = []
        }
        options = {
          colorMode = "background"
          graphMode = "area"
          reduceOptions = {
            calcs  = ["lastNotNull"]
            fields = ""
            values = false
          }
          textMode = "auto"
        }
        targets = [
          {
            refId        = "A"
            expr         = "sum(kube_pod_status_ready{namespace=\"recipe-rescue-production-data\",pod=~\"recipe-rescue-postgres-.*\",condition=\"true\"})"
            legendFormat = "postgres ready"
          }
        ]
      },
      {
        id         = 7
        title      = "ArgoCD and Rollouts controllers running"
        type       = "stat"
        datasource = { type = "prometheus", uid = "prometheus" }
        gridPos    = { h = 5, w = 6, x = 6, y = 13 }
        fieldConfig = {
          defaults = {
            unit     = "short"
            decimals = 0
            color    = { mode = "palette-classic" }
          }
          overrides = []
        }
        options = {
          colorMode = "value"
          graphMode = "area"
          reduceOptions = {
            calcs  = ["lastNotNull"]
            fields = ""
            values = false
          }
          textMode = "auto"
        }
        targets = [
          {
            refId        = "A"
            expr         = "sum(kube_pod_status_phase{namespace=~\"argocd|argo-rollouts\",phase=\"Running\"}) by (namespace)"
            legendFormat = "{{namespace}}"
          }
        ]
      }
    ]
  }

  recipe_rescue_alertmanager_email_values = yamlencode({
    alertmanager = {
      enabled = true

      service = {
        type = "ClusterIP"
      }

      alertmanagerSpec = {
        replicas = 1
        resources = {
          requests = {
            cpu    = "25m"
            memory = "64Mi"
          }
          limits = {
            cpu    = "100m"
            memory = "128Mi"
          }
        }
      }

      config = {
        global = {
          smtp_smarthost     = var.alert_smtp_smarthost
          smtp_from          = var.alert_email_from
          smtp_require_tls   = true
          smtp_auth_username = ""
          smtp_auth_password = ""
        }

        route = {
          receiver        = "recipe-rescue-email"
          group_by        = ["alertname", "environment", "component"]
          group_wait      = "30s"
          group_interval  = "5m"
          repeat_interval = "1h"
        }

        receivers = [
          {
            name = "null"
          },
          {
            name = "recipe-rescue-email"
            email_configs = [
              {
                to            = var.alert_email_to
                from          = var.alert_email_from
                send_resolved = true
              }
            ]
          }
        ]
      }
    }
  })
}

check "email_alerts_require_smtp_config" {
  assert {
    condition = !var.enable_email_alerts || (
      length(trimspace(var.alert_email_from)) > 0 &&
      length(trimspace(var.alert_email_to)) > 0 &&
      length(trimspace(var.alert_smtp_smarthost)) > 0 &&
      length(trimspace(var.alert_smtp_username)) > 0 &&
      length(trimspace(var.alert_smtp_password)) > 0
    )
    error_message = "When enable_email_alerts=true, set alert_email_from, alert_email_to, alert_smtp_smarthost, alert_smtp_username, and alert_smtp_password."
  }
}

resource "kubernetes_config_map_v1" "recipe_rescue_grafana_dashboard" {
  metadata {
    name      = "recipe-rescue-grafana-dashboard"
    namespace = kubernetes_namespace_v1.monitoring.metadata[0].name

    labels = {
      grafana_dashboard             = "1"
      "app.kubernetes.io/name"      = "recipe-rescue-dashboard"
      "app.kubernetes.io/part-of"   = var.project_name
      "app.kubernetes.io/component" = "monitoring"
    }
  }

  data = {
    "recipe-rescue-overview.json" = jsonencode(local.recipe_rescue_dashboard)
  }
}

resource "helm_release" "blackbox_exporter" {
  name       = "blackbox-exporter"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus-blackbox-exporter"
  version    = var.prometheus_blackbox_exporter_chart_version
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name

  wait    = true
  timeout = 300

  values = [
    yamlencode({
      fullnameOverride = "blackbox-exporter"

      service = {
        port = 9115
      }

      config = {
        modules = {
          http_2xx = {
            prober  = "http"
            timeout = "5s"
            http = {
              method                = "GET"
              preferred_ip_protocol = "ip4"
              valid_http_versions   = ["HTTP/1.1", "HTTP/2.0"]
            }
          }
        }
      }

      resources = {
        requests = {
          cpu    = "25m"
          memory = "64Mi"
        }
        limits = {
          cpu    = "100m"
          memory = "128Mi"
        }
      }
    }),
  ]
}

resource "helm_release" "kube_prometheus_stack" {
  name       = "monitoring"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = var.kube_prometheus_stack_chart_version
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name

  wait    = true
  timeout = 900

  values = concat([
    yamlencode({
      fullnameOverride = "monitoring"

      crds = {
        enabled = true
      }

      defaultRules = {
        create = false
      }

      alertmanager = {
        enabled = false
      }

      kubeControllerManager = {
        enabled = false
      }

      kubeScheduler = {
        enabled = false
      }

      kubeEtcd = {
        enabled = false
      }

      grafana = {
        adminUser     = "admin"
        adminPassword = var.grafana_admin_password

        service = {
          type = "ClusterIP"
        }

        defaultDashboardsEnabled = true

        sidecar = {
          dashboards = {
            enabled          = true
            label            = "grafana_dashboard"
            labelValue       = "1"
            searchNamespace  = "ALL"
            folderAnnotation = "grafana_folder"
          }
        }

        resources = {
          requests = {
            cpu    = "50m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "250m"
            memory = "256Mi"
          }
        }
      }

      prometheusOperator = {
        resources = {
          requests = {
            cpu    = "50m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "250m"
            memory = "256Mi"
          }
        }
      }

      prometheus = {
        service = {
          type = "ClusterIP"
        }

        prometheusSpec = {
          retention                               = "3d"
          scrapeInterval                          = "30s"
          evaluationInterval                      = "30s"
          serviceMonitorSelectorNilUsesHelmValues = false
          podMonitorSelectorNilUsesHelmValues     = false
          ruleSelectorNilUsesHelmValues           = false

          resources = {
            requests = {
              cpu    = "100m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }

          additionalScrapeConfigs = [
            {
              job_name        = "recipe-rescue-http-probes"
              metrics_path    = "/probe"
              scrape_interval = "30s"
              params = {
                module = ["http_2xx"]
              }
              static_configs = [
                for target in local.recipe_rescue_blackbox_targets : {
                  targets = [target.url]
                  labels = {
                    service     = target.name
                    environment = target.environment
                    component   = target.component
                  }
                }
              ]
              relabel_configs = [
                {
                  source_labels = ["__address__"]
                  target_label  = "__param_target"
                },
                {
                  source_labels = ["__param_target"]
                  target_label  = "instance"
                },
                {
                  target_label = "__address__"
                  replacement  = "blackbox-exporter.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:9115"
                }
              ]
            }
          ]
        }
      }

      additionalPrometheusRulesMap = {
        "recipe-rescue.rules" = {
          groups = [
            {
              name = "recipe-rescue.rules"
              rules = [
                {
                  alert = "RecipeRescueEndpointDown"
                  expr  = "probe_success{job=\"recipe-rescue-http-probes\"} == 0"
                  for   = "2m"
                  labels = {
                    severity = "warning"
                  }
                  annotations = {
                    summary     = "Recipe Rescue endpoint is down"
                    description = "The {{ $labels.environment }} {{ $labels.component }} endpoint {{ $labels.instance }} has failed blackbox checks for more than 2 minutes."
                  }
                },
                {
                  alert = "RecipeRescuePodRestarting"
                  expr  = "sum(increase(kube_pod_container_status_restarts_total{namespace=~\"recipe-rescue-.*\"}[10m])) by (namespace, pod) > 0"
                  for   = "1m"
                  labels = {
                    severity = "info"
                  }
                  annotations = {
                    summary     = "Recipe Rescue pod restarted"
                    description = "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} restarted recently. Kubernetes should recreate unhealthy containers automatically."
                  }
                }
              ]
            }
          ]
        }
      }
    }),
  ], var.enable_email_alerts ? [local.recipe_rescue_alertmanager_email_values] : [])

  depends_on = [
    helm_release.blackbox_exporter,
    kubernetes_config_map_v1.recipe_rescue_grafana_dashboard,
  ]

  dynamic "set_sensitive" {
    for_each = var.enable_email_alerts ? {
      "alertmanager.config.global.smtp_auth_username" = var.alert_smtp_username
      "alertmanager.config.global.smtp_auth_password" = var.alert_smtp_password
    } : {}

    content {
      name  = set_sensitive.key
      value = set_sensitive.value
    }
  }
}
