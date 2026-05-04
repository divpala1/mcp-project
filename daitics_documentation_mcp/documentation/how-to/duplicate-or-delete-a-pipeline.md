---
id: how-to/duplicate-or-delete-a-pipeline
title: Duplicate or delete a pipeline in Daitics DTX Portal
category: how-to
summary: Duplicate copies a pipeline as a new draft so you can experiment without changing the original. Delete soft-archives a pipeline, hiding it from the list.
tags: [pipeline, duplicate, delete, copy, archive]
aliases:
  - copy a pipeline
  - clone a pipeline
  - remove a pipeline
  - archive pipeline
  - duplicate pipeline
last_updated: 2026-05-02
version: 1
---

# Duplicate or delete a pipeline in Daitics DTX Portal

## What this does {#what-this-does}

Duplicating a pipeline in Daitics DTX Portal makes an exact copy of an existing pipeline and saves it as a new draft. Deleting a pipeline removes it from the Pipelines list. Delete is a soft archive — the pipeline is hidden, not destroyed, and an administrator can restore it if needed.

Duplicate is useful when you want to try variations without disturbing the original. Delete is useful when a pipeline is finished or replaced.

## When you would duplicate or delete a pipeline {#when-you-would-duplicate-or-delete-a-pipeline}

You would duplicate or delete a pipeline in Daitics DTX Portal when you need to:

- **Duplicate** to keep a stable version running while you experiment on a copy.
- **Duplicate** to start a new pipeline from a similar one rather than from scratch.
- **Delete** to remove a pipeline you no longer need.
- **Delete** to clean up the Pipelines list when an experiment is over.

## Steps to duplicate a pipeline {#steps-to-duplicate-a-pipeline}

Follow these steps to duplicate a pipeline in Daitics DTX Portal:

1. In the sidebar, click **Pipelines**.
2. Find the pipeline you want to copy in the list.
3. Click the **⋯** menu at the right end of its row.
4. Click **Duplicate**.
5. The portal creates a new draft named **Copy of \<original name\>** and opens it in the designer.
6. Rename the copy and edit it as you like.

The copy is independent. Changes to the duplicate do not affect the original.

## Steps to delete a pipeline {#steps-to-delete-a-pipeline}

Follow these steps to delete a pipeline in Daitics DTX Portal:

1. In the sidebar, click **Pipelines**.
2. Find the pipeline you want to delete.
3. Click the **⋯** menu at the right end of its row.
4. Click **Delete**.
5. Read the confirmation dialog. It tells you the pipeline will be archived.
6. Click **Confirm delete**.

A deployed pipeline cannot be deleted directly. Pause it, then cancel it, before deleting.

## What to expect after duplicating or deleting {#what-to-expect-after-duplicating-or-deleting}

After duplicating or deleting a pipeline in Daitics DTX Portal, you should see:

- **After Duplicate** — the new draft opens in the designer. The original is unchanged on the list.
- **After Delete** — the pipeline disappears from the list. A green toast confirms "Pipeline deleted".

Deleted pipelines no longer count against any limits and do not run. They are recoverable through your administrator if you change your mind.

## If something goes wrong duplicating or deleting {#if-something-goes-wrong-duplicating-or-deleting}

If something goes wrong while duplicating or deleting a pipeline in Daitics DTX Portal, check the most likely causes:

- **You cannot find Duplicate or Delete in the row menu** — your account may not have the role needed for these actions. Ask your administrator.
- **"Cannot delete a deployed pipeline"** — pause and cancel the pipeline first, then try delete again.
- **"Failed to duplicate pipeline"** — the source pipeline may have an unsaved error. Open it, fix any validation issues, save, and try duplicating again.
- **The duplicate is missing operators** — confirm the original opens cleanly in the designer. If it does, refresh and duplicate again.

For more help, see [Troubleshooting](../troubleshooting.md).
