---
id: how-to/check-system-health
title: Check system health in Daitics DTX Portal
category: how-to
summary: To check system health, open the Dashboard from the sidebar. The page shows a cluster health badge, summary metrics, alerts, and per-service status.
tags: [observability, dashboard, health, monitoring, status]
aliases:
  - check status
  - system status
  - is daitics up
  - daitics health
  - check observability
  - service status
last_updated: 2026-05-02
version: 1
---

# Check system health in Daitics DTX Portal

## What this does {#what-this-does}

Checking system health in Daitics DTX Portal means opening the Observability dashboard and reading the cluster health badge, alerts, and service status table. The dashboard answers "is the platform healthy right now?" and points you to the area that needs attention if it is not.

## When you would check system health {#when-you-would-check-system-health}

You would check system health in Daitics DTX Portal when you need to:

- Confirm the platform is healthy before starting an important task.
- Diagnose why a pipeline is slow or failing.
- Verify a fix has cleared an alert.
- Know whether a planned change can go ahead during a maintenance window.

## Steps to check system health {#steps-to-check-system-health}

Follow these steps to check system health in Daitics DTX Portal:

1. In the sidebar, click **Dashboard**.
2. Read the **System Overview** section at the top. The cluster health badge shows **Healthy**, **Degraded**, or **Unhealthy**.
3. Read the **Metrics summary cards** for request rate, average latency, error rate, and uptime.
4. If the badge is not Healthy, scroll to the **Alerts panel** and read alerts grouped by severity (critical, warning, info).
5. Cross-check the **Health Checks panel** for Kafka, the database, the cache, and the API gateway.
6. Open the **Service Status table** to see every service's current health and last check time.
7. To refresh the data, click **Refresh** at the top of the page.

The dashboard does not refresh on its own — always click **Refresh** for the latest state.

## What to expect when checking system health {#what-to-expect-when-checking-system-health}

When you check system health in Daitics DTX Portal, you should see:

- A single cluster health badge: **Healthy**, **Degraded**, or **Unhealthy**.
- Summary metric cards with current values.
- A list of any open alerts (or "No alerts" if everything is clear).
- A row for each service with its health status.
- A chart showing log volume by severity for the recent past.

If a service shows as down, it does not always mean the service is broken — it may mean the portal cannot reach it. Read the alert details before acting.

## If the dashboard looks wrong or empty {#if-the-dashboard-looks-wrong-or-empty}

If the Daitics DTX Portal Observability dashboard looks wrong or empty, check the most likely causes:

- **All panels show "No data"** — the observability backend may be unreachable. Click **Refresh**. If still empty, ask your administrator.
- **Cluster health badge is Unhealthy but no alerts show** — the dashboard may not have caught up yet. Click **Refresh**.
- **You see services you do not recognize** — the dashboard shows every service the portal knows about, including internal ones.
- **The Refresh button does nothing** — your network may have dropped. Reload the page.
- **Service Status shows a service as down that you can use normally** — the health check path between the portal and the service may be broken. Ask your administrator.

For more help, see [Troubleshooting](../troubleshooting.md).
