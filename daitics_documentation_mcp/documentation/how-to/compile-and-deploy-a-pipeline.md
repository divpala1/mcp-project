---
id: how-to/compile-and-deploy-a-pipeline
title: Compile and deploy a pipeline in Daitics DTX Portal
category: how-to
summary: Compile turns your visual pipeline into a runnable job, and deploy submits it to the runtime so it starts processing data. Both run from the designer's top bar.
tags: [pipeline, compile, deploy, run, lifecycle]
aliases:
  - run a pipeline
  - start a pipeline
  - deploy a pipeline
  - compile pipeline
  - turn on pipeline
  - launch pipeline
last_updated: 2026-05-02
version: 1
---

# Compile and deploy a pipeline in Daitics DTX Portal

## What this does {#what-this-does}

Compiling a pipeline in Daitics DTX Portal translates your visual canvas into a runnable job. Deploying then submits that job to the runtime so it starts reading from sources and writing to sinks. Compile and deploy are two separate steps — you can compile a pipeline to check it works without actually starting it.

## When you would compile and deploy a pipeline {#when-you-would-compile-and-deploy-a-pipeline}

You would compile and deploy a pipeline in Daitics DTX Portal when you have:

- Finished building a draft pipeline and want to validate that it can run.
- Made edits to a deployed pipeline and want to push the new version live.
- Recovered a previously failed pipeline after fixing the issue.

If you only want to confirm the pipeline is structurally valid without running it, compile but do not deploy.

## Steps to compile and deploy a pipeline {#steps-to-compile-and-deploy-a-pipeline}

Follow these steps to compile and deploy a pipeline in Daitics DTX Portal:

1. Open the pipeline in the designer (click its name on the Pipelines list).
2. Make sure the pipeline is saved. If it is not, click **Save** first.
3. Click **Compile** in the top bar of the designer.
4. A modal opens showing compilation progress phase by phase. Wait for it to finish. The status changes to **Compiled**.
5. Click **Deploy** in the top bar.
6. The portal submits the job to the runtime and polls until the status reaches **Deployed**.
7. The canvas now shows live metrics on each operator (records in, out, filtered) and throughput on each connection.

![Pipeline designer top bar with Save, Compile, and Deploy buttons](TODO/screenshots/pipeline-top-bar.png)

## What to expect after deploying a pipeline {#what-to-expect-after-deploying-a-pipeline}

After deploying a pipeline in Daitics DTX Portal, you should see:

- The pipeline status badge reads **Deployed**.
- Live metrics appear on every operator on the canvas.
- A green toast confirms "Pipeline deployed".
- The Pipelines list shows **Pause** on this pipeline's row.

Streaming pipelines keep running until you pause or cancel them. Batch pipelines run to completion and then stop on their own.

## If something goes wrong compiling or deploying {#if-something-goes-wrong-compiling-or-deploying}

If something goes wrong while compiling or deploying a pipeline in Daitics DTX Portal, check the most likely causes:

- **"Pipeline must be saved first"** — click **Save** before **Compile**.
- **"Pipeline must be compiled first"** — click **Compile** before **Deploy**.
- **"Pipeline too large"** — the compiled job exceeds a runtime limit. Split the pipeline into smaller pieces.
- **"Deployment failed"** — open the toast's details to see the runtime error. Common causes are unreachable sources or sinks, or missing credentials. Ask your administrator if connection details look wrong.
- **The pipeline status stays at "Compiled" forever** — refresh the page. If the status still does not change, ask your administrator to check the runtime.
- **Status reads "Failed"** — open the pipeline and click **View Logs** to see the error.

For more help, see [Troubleshooting](../troubleshooting.md).
