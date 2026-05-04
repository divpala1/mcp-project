---
id: features/observability
title: Observability dashboard in Daitics DTX Portal
category: features
summary: The Observability dashboard shows cluster health, request rates, latency, error rates, alerts, and recent activity for every service in Daitics DTX Portal.
tags: [observability, dashboard, metrics, alerts, health-checks, monitoring]
aliases:
  - dashboard
  - metrics
  - system health
  - service status
  - alerts
  - monitoring
  - health checks
last_updated: 2026-05-02
version: 1
---

# Observability dashboard in Daitics DTX Portal

## What the Observability dashboard shows in Daitics DTX Portal {#what-the-observability-dashboard-shows-in-daitics-dtx-portal}

The Observability dashboard in Daitics DTX Portal shows whether the platform is healthy right now. You see one cluster health badge, summary metrics for all services together, and panels that break the picture down by service, alert level, and log volume. The dashboard is read-only — you cannot change settings here, only see the current state.

The dashboard is for everyone, but it is most useful to data engineers running pipelines and to administrators investigating an issue.

## When you would use the Observability dashboard {#when-you-would-use-the-observability-dashboard}

You would use the Observability dashboard in Daitics DTX Portal when you need to:

- Check at a glance whether the platform is healthy before starting work.
- Investigate why a pipeline is slow or failing.
- See whether a recent deployment broke anything.
- Confirm that alerts have cleared after a fix.

## Where to find the Observability dashboard {#where-to-find-the-observability-dashboard}

The Observability dashboard in Daitics DTX Portal is the **Dashboard** entry in the sidebar. Click it to open the page directly. Press the **Refresh** button at the top to reload the data on demand; otherwise the page does not refresh automatically.

## What each panel on the Observability dashboard shows {#what-each-panel-on-the-observability-dashboard-shows}

The Observability dashboard in Daitics DTX Portal has seven panels, each focused on one aspect of the platform's health:

- **System Overview** — one cluster health badge plus the count of services that are up vs. down.
- **Metrics summary cards** — request rate, average latency, error rate, and uptime across all services.
- **Health Checks panel** — per-component status for Kafka, the database, the cache, and the API gateway.
- **Alerts panel** — current alerts grouped by severity (critical, warning, info).
- **Log Level Distribution** — a chart showing how many logs the platform produced at each level (error, warn, info, debug).
- **Service Status table** — every service with its current health and the time of its last health check.
- **Recent Activity feed** — the latest deployments, restarts, and failures.

## What the cluster health badge means {#what-the-cluster-health-badge-means}

The cluster health badge in Daitics DTX Portal sits at the top of the Observability dashboard and summarises the platform's state in one word:

- **Healthy** — every monitored service is up and recent metrics are within expected ranges.
- **Degraded** — at least one service is reporting issues but the platform is still operating.
- **Unhealthy** — one or more critical services are down.

The badge gives you a single answer to the question "is anything broken right now?" — but always check the panels below for details before acting.

## What an alert means in the Alerts panel {#what-an-alert-means-in-the-alerts-panel}

An alert in the Daitics DTX Portal Observability dashboard is a notification that something crossed a threshold. Alerts are grouped by severity:

- **Critical** — needs attention now. Often a service is down or unreachable.
- **Warning** — abnormal but not breaking. For example, slow response times.
- **Info** — informational. For example, a service was restarted.

Alerts clear automatically when the underlying condition is resolved. The dashboard shows the current set, not a history.

## Limits and things to know about the Observability dashboard {#limits-and-things-to-know-about-the-observability-dashboard}

A few things to keep in mind when using the Observability dashboard in Daitics DTX Portal:

- The dashboard shows the **current** state. It is not a long-term metrics tool — for trends over hours or days, use your team's monitoring system.
- Data does not refresh automatically. Press **Refresh** to update.
- The dashboard can only show services it knows about. New services your team adds may take time to appear.
- A "Service down" status here means the portal could not reach a service. The service may actually be healthy and the network path may be the problem.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common Observability tasks in Daitics DTX Portal:

- [Check system health](../how-to/check-system-health.md)
