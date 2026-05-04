---
id: how-to/pause-resume-or-cancel-a-pipeline
title: Pause, resume, or cancel a pipeline in Daitics DTX Portal
category: how-to
summary: Pause stops a pipeline at a savepoint so you can resume it later. Resume restarts from that savepoint. Cancel is a hard stop with no savepoint.
tags: [pipeline, pause, resume, cancel, stop, savepoint]
aliases:
  - stop a pipeline
  - kill a pipeline
  - shut down pipeline
  - savepoint
  - turn off pipeline
last_updated: 2026-05-02
version: 1
---

# Pause, resume, or cancel a pipeline in Daitics DTX Portal

## What this does {#what-this-does}

Pause, resume, and cancel are the three ways to stop or restart a running pipeline in Daitics DTX Portal:

- **Pause** — creates a savepoint (a snapshot of the pipeline's progress) and then stops the pipeline. You can resume later from exactly where it left off.
- **Resume** — restarts a paused pipeline from its savepoint. No records are reprocessed.
- **Cancel** — a hard stop. The pipeline ends immediately without a savepoint and cannot be resumed.

## When you would pause, resume, or cancel a pipeline {#when-you-would-pause-resume-or-cancel-a-pipeline}

You would pause, resume, or cancel a pipeline in Daitics DTX Portal in different situations:

- **Pause** when you need to temporarily stop processing — for example, during a planned maintenance window — and want to pick up cleanly afterwards.
- **Resume** to restart a paused pipeline once the reason for pausing is over.
- **Cancel** when the pipeline has a problem that requires redeploying from scratch, or when you no longer want this pipeline to run at all.

If you are not sure which to use, prefer **Pause**. It is reversible.

## Steps to pause a pipeline {#steps-to-pause-a-pipeline}

Follow these steps to pause a running pipeline in Daitics DTX Portal:

1. Open the pipeline in the designer, or find its row on the Pipelines list.
2. Click **Pause** (in the designer's top bar, or on the pipeline's row in the list).
3. Wait for the savepoint to be created. The status changes from **Deployed** to **Paused**.

## Steps to resume a paused pipeline {#steps-to-resume-a-paused-pipeline}

Follow these steps to resume a paused pipeline in Daitics DTX Portal:

1. Open the pipeline in the designer, or find its row on the Pipelines list.
2. Confirm the status reads **Paused**.
3. Click **Resume** (in the designer's top bar, or on the pipeline's row).
4. The status changes from **Paused** to **Deployed** and processing resumes from the savepoint.

## Steps to cancel a running pipeline {#steps-to-cancel-a-running-pipeline}

Follow these steps to cancel a running pipeline in Daitics DTX Portal:

1. Open the pipeline in the designer.
2. Click **Cancel** in the top bar.
3. Read the confirmation dialog carefully — cancel is not reversible.
4. Click **Confirm cancel**. The status changes to **Cancelled**.

## What to expect after pausing, resuming, or cancelling {#what-to-expect-after-pausing-resuming-or-cancelling}

After pausing, resuming, or cancelling a pipeline in Daitics DTX Portal, you should see:

- The status badge updates: **Paused**, **Deployed**, or **Cancelled**.
- A green toast confirms the action.
- Live metrics on the canvas freeze (after pause), restart (after resume), or stop entirely (after cancel).

A cancelled pipeline cannot be resumed. To run it again, you must redeploy it from scratch — open it in the designer, then **Compile** and **Deploy**.

## If something goes wrong pausing, resuming, or cancelling {#if-something-goes-wrong-pausing-resuming-or-cancelling}

If something goes wrong while pausing, resuming, or cancelling a pipeline in Daitics DTX Portal, check the most likely causes:

- **"No pipeline to pause"** — the pipeline is not currently deployed. Confirm the status badge.
- **"Pipeline must be deployed to pause"** — the action is only valid in the **Deployed** state.
- **"Pipeline must be paused to resume"** — the action is only valid in the **Paused** state.
- **"Failed to cancel pipeline"** — the runtime did not respond. Refresh and try again. If it keeps failing, ask your administrator.
- **The pipeline status stays "Pausing" forever** — savepoints can take time on large pipelines. Wait a few minutes. If it still does not change, refresh the page.

For more help, see [Troubleshooting](../troubleshooting.md).
