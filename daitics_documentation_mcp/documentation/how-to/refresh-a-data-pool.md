---
id: how-to/refresh-a-data-pool
title: Refresh a data pool in Daitics DTX Portal
category: how-to
summary: To refresh a data pool, open Synthetic Data → Pools, then click Refresh on the pool's card. To reload every pool at once, click Refresh All Pools at the top.
tags: [data-pool, refresh, synthetic-data, sdg, reference-data]
aliases:
  - reload data pool
  - refresh sdg pool
  - reload reference data
  - refresh all pools
  - update data pool
last_updated: 2026-05-02
version: 1
---

# Refresh a data pool in Daitics DTX Portal

## What this does {#what-this-does}

Refreshing a data pool in Daitics DTX Portal reloads its contents from the system source so generators using the pool see the latest reference data. Data pools hold shared reference values like country codes or product categories. They refresh on a schedule by default, but you can refresh on demand if the underlying source has changed and you do not want to wait.

## When you would refresh a data pool {#when-you-would-refresh-a-data-pool}

You would refresh a data pool in Daitics DTX Portal when you need to:

- Pull the latest values into the pool because the source updated.
- Recover a pool that shows the **Error** status.
- Confirm a pool is reachable and loadable as part of a check.

If a pool's last refresh time is recent and its status is **Loaded**, you usually do not need to refresh.

## Steps to refresh a single data pool {#steps-to-refresh-a-single-data-pool}

Follow these steps to refresh a single data pool in Daitics DTX Portal:

1. In the sidebar, click **Data Management → Synthetic Data → Pools**.
2. Find the pool's card in the grid.
3. Click **Refresh** on the card.
4. Wait for the status badge to change from **Loading** back to **Loaded**.

## Steps to refresh every data pool {#steps-to-refresh-every-data-pool}

Follow these steps to refresh every data pool in Daitics DTX Portal at once:

1. In the sidebar, click **Data Management → Synthetic Data → Pools**.
2. Click **Refresh All Pools** at the top of the page.
3. Wait for every pool's status badge to settle on **Loaded** (or **Error** if a pool fails).

## What to expect after refreshing a data pool {#what-to-expect-after-refreshing-a-data-pool}

After refreshing a data pool in Daitics DTX Portal, you should see:

- The pool's status changes briefly to **Loading**, then back to **Loaded**.
- The "last refresh" timestamp updates.
- Record count and memory usage may change if the underlying data has grown or shrunk.
- A green toast confirms the refresh succeeded.

Generators using the pool start seeing the new values as soon as the refresh completes.

## If something goes wrong refreshing a data pool {#if-something-goes-wrong-refreshing-a-data-pool}

If something goes wrong while refreshing a data pool in Daitics DTX Portal, check the most likely causes:

- **The pool stays in Loading status for a long time** — large pools can take a while. Wait a few minutes. If it does not recover, refresh the page.
- **The pool ends up in Error status** — the source could not be read. Hover over or click the pool card for details. Common causes are network issues or a missing source file.
- **"Failed to refresh pool"** — your network may have dropped. Try again. If it keeps failing, ask your administrator.
- **You expected to refresh, but Refresh is greyed out** — the pool may already be refreshing. Wait for the current refresh to finish.

For more help, see [Troubleshooting](../troubleshooting.md).
