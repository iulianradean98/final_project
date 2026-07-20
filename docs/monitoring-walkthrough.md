# Recipe Rescue Monitoring Walkthrough

This document explains the minimal monitoring layer added for the final DevOps project.

## What Was Added

Monitoring is installed by Terraform in the `monitoring` namespace.

Components:

- Prometheus: collects metrics.
- Grafana: visualizes metrics.
- Prometheus Operator: manages Prometheus custom resources.
- kube-state-metrics: exposes Kubernetes object state such as pods, deployments, jobs, and namespaces.
- node-exporter: exposes node-level metrics.
- Blackbox Exporter: checks live HTTP endpoints from inside the cluster.
- Recipe Rescue Overview dashboard: custom dashboard for application and platform health.

## Why This Is Enough For The Project

The project requirements mention optional monitoring and self-healing:

1. Poll frontend and backend endpoints.
2. Recover or reprovision unhealthy containers.

The project covers this in two layers:

- Monitoring visibility: Prometheus probes staging and production frontend/backend endpoints every 30 seconds.
- Runtime self-healing: Kubernetes liveness/readiness probes, ReplicaSets/Rollouts, and Argo Rollouts keep traffic on healthy versions and recreate unhealthy pods.

So the monitoring stack shows the health of the system, while Kubernetes and Argo Rollouts perform the recovery behavior.

## Monitored Endpoints

Prometheus uses Blackbox Exporter to check:

```text
http://recipe-rescue-web.recipe-rescue-staging.svc.cluster.local/
http://recipe-rescue-web.recipe-rescue-staging.svc.cluster.local/api/ready
http://recipe-rescue-router.recipe-rescue-production.svc.cluster.local/
http://recipe-rescue-router.recipe-rescue-production.svc.cluster.local/api/ready
```

These are internal Kubernetes DNS names. They are checked from inside the cluster, which is better than checking from your laptop because it validates service-to-service connectivity inside Kubernetes.

## Alerts

Two lightweight alert rules are installed:

- `RecipeRescueEndpointDown`: active when a staging or production frontend/backend probe fails for more than 2 minutes.
- `RecipeRescuePodRestarting`: active when a Recipe Rescue pod restarts in the last 10 minutes.

Alertmanager can send email through AWS SES SMTP when `enable_email_alerts=true`. If email alerting is disabled, alerts are still visible in Prometheus/Grafana but no email is sent.

## Optional Email Alerts Through AWS SES

SES manual setup:

1. In Amazon SES, region `eu-central-1`, verify the sender email address.
2. If SES is in sandbox mode, verify the receiver email address too.
3. In SES SMTP settings, create IAM SMTP credentials.
4. Keep the SMTP username/password secret.

GitHub repository variables:

```text
ENABLE_EMAIL_ALERTS=true
ALERT_EMAIL_FROM=iulian.radean@gmail.com
ALERT_EMAIL_TO=iulian.radean@gmail.com
ALERT_SMTP_SMARTHOST=email-smtp.eu-central-1.amazonaws.com:587
```

GitHub repository secrets:

```text
ALERT_SMTP_USERNAME=<SES SMTP username>
ALERT_SMTP_PASSWORD=<SES SMTP password>
```

After these values are configured, run the `Infrastructure Recovery` workflow in apply mode. Terraform enables Alertmanager and configures the email receiver.

Important security note:

> The SMTP username/password are never committed to Git. They are passed to Terraform through GitHub Actions secrets. Terraform state is stored in the encrypted S3 backend, so treat access to the Terraform state bucket as sensitive infrastructure access.

## Access Grafana

Grafana is not exposed publicly. Use port-forward:

```powershell
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open:

```text
http://localhost:3000
```

Login:

```text
user: admin
password: recipe-rescue-admin
```

Open the dashboard:

```text
Dashboards -> Recipe Rescue Overview
```

What to show:

- HTTP probes up.
- Endpoint probe status.
- Running pods by namespace.
- Container restarts.
- Production database pod readiness.
- ArgoCD and Argo Rollouts controller pods.

## Access Prometheus

Use port-forward:

```powershell
kubectl port-forward svc/monitoring-prometheus -n monitoring 9090:9090
```

Open:

```text
http://localhost:9090
```

Useful queries:

```promql
probe_success{job="recipe-rescue-http-probes"}
sum(kube_pod_status_phase{namespace=~"recipe-rescue-.*",phase="Running"}) by (namespace)
sum(increase(kube_pod_container_status_restarts_total{namespace=~"recipe-rescue-.*"}[15m])) by (namespace, pod)
sum(kube_pod_status_ready{namespace="recipe-rescue-production-data",pod=~"recipe-rescue-postgres-.*",condition="true"})
```

Check alerts:

```text
Status -> Rules
Alerts
```

To check that Alertmanager exists when email is enabled:

```powershell
kubectl get pods -n monitoring | Select-String alertmanager
kubectl port-forward svc/monitoring-alertmanager -n monitoring 9093:9093
```

Open:

```text
http://localhost:9093
```

## Quick Email Alert Test

The easiest safe demo test is to temporarily scale down the staging frontend so the blackbox probe fails:

```powershell
kubectl scale deployment recipe-rescue-web -n recipe-rescue-staging --replicas=0
```

Wait around 2-3 minutes. Then check:

- Prometheus `Alerts` page.
- Alertmanager UI.
- Email inbox.

Restore staging:

```powershell
kubectl scale deployment recipe-rescue-web -n recipe-rescue-staging --replicas=1
```

ArgoCD may also restore it automatically because staging is GitOps-managed. Once the endpoint is healthy again, Alertmanager should send a resolved notification if `send_resolved=true` is enabled.

## Kubernetes Commands

Check monitoring namespace:

```powershell
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Check Prometheus targets:

```powershell
kubectl port-forward svc/monitoring-prometheus -n monitoring 9090:9090
```

Then open:

```text
http://localhost:9090/targets
```

## Demo Explanation

Use this explanation:

> Monitoring is implemented with Prometheus and Grafana. Prometheus collects Kubernetes metrics through kube-state-metrics and node-exporter, and it checks Recipe Rescue frontend/backend endpoints using Blackbox Exporter. Grafana provides a dashboard for endpoint health, pod status, restarts, database readiness, and controller health. The monitoring layer gives visibility, while Kubernetes probes, ReplicaSets, ArgoCD self-healing, and Argo Rollouts provide the actual recovery mechanisms.

## Important Design Choice

Grafana and Prometheus are internal only:

```text
Service type: ClusterIP
Access method: kubectl port-forward
```

This is intentional because it avoids:

- extra AWS LoadBalancer cost
- public dashboard exposure
- DNS/TLS setup work during the final project deadline

For a professional production environment, the next step would be to expose Grafana behind authenticated ingress with HTTPS and SSO.
