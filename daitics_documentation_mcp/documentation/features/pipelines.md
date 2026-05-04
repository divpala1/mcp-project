---
id: features/pipelines
title: Pipelines in Daitics DTX Portal
category: features
summary: Pipelines are visual data flows you build by dragging operators onto a canvas, then compile and deploy to run continuously or as a batch job.
tags: [pipelines, streaming, batch, designer, canvas, operators]
aliases:
  - what is a pipeline
  - pipeline designer
  - data pipeline
  - flink job
  - streaming pipeline
  - batch pipeline
  - dtx pipeline
last_updated: 2026-05-02
version: 1
---

# Pipelines in Daitics DTX Portal

## What pipelines are in Daitics DTX Portal {#what-pipelines-are-in-daitics-dtx-portal}

A pipeline in Daitics DTX Portal is a visual data flow that reads from one or more sources, processes the data, and writes it to one or more destinations. You build a pipeline by dragging operator boxes onto a canvas and connecting them with lines. The portal then compiles your visual pipeline into a job and deploys it.

Pipelines run in two modes:

- **Streaming** — the pipeline runs continuously, processing new records as they arrive.
- **Batch** — the pipeline runs once over a finite set of records, then stops.

You do not write code to build a pipeline. All configuration happens through forms and the visual canvas.

## When you would use pipelines in Daitics DTX Portal {#when-you-would-use-pipelines-in-daitics-dtx-portal}

You would use pipelines in Daitics DTX Portal whenever you need to move or transform data between systems. Common situations:

- Move records from a Kafka topic to a database.
- Filter or enrich records on their way between two systems.
- Run a one-off transformation across a fixed set of input data.
- Combine data from multiple sources into a single output stream.

If you only need to copy data from one place to another with no transformation, a pipeline still works. The canvas just has a source operator connected to a sink operator.

## Where to find pipelines in Daitics DTX Portal {#where-to-find-pipelines-in-daitics-dtx-portal}

Pipelines in Daitics DTX Portal live under the **Pipelines** section of the sidebar. Click **Pipelines** in the sidebar to open the list of all pipelines. Click any row to open that pipeline in the designer. Click **New Pipeline** in the top-right of the list to start a new one.

The designer opens full-screen so the canvas has as much space as possible. To leave the designer, click the back arrow or the breadcrumb at the top.

## What you can do on the Pipelines list page {#what-you-can-do-on-the-pipelines-list-page}

The Pipelines list page in Daitics DTX Portal shows every pipeline you have access to, with these columns and actions:

- **Columns** — Name, Type (Processing, Source, Sink), Mode (Streaming or Batch), Status, Created By, Last Modified.
- **Search** — type into the search box to filter by name or description. Search waits a moment after you stop typing.
- **Sort** — click any column header to sort by that column.
- **Pagination** — 20 pipelines per page.
- **Pause / Resume** — appears directly on each row for pipelines that are deployed or paused.
- **Row menu (⋯)** — Edit (open in designer), Duplicate (creates a draft copy named "Copy of …"), Delete (soft archive, requires confirmation).

## What you can do in the pipeline designer {#what-you-can-do-in-the-pipeline-designer}

In the Daitics DTX Portal pipeline designer you build, save, compile, and deploy pipelines on a single canvas:

- **Add operators** — click the floating **+** button to open the Adaptor Palette. Search or filter operators by category (Source, Process, Sink), then drag one onto the canvas.
- **Configure operators** — click any operator on the canvas to open the side configuration panel. Set input and output field mappings and any operator-specific settings.
- **Connect operators** — drag from an output handle on one operator to an input handle on another. If the connection is not valid, the canvas shows a banner explaining why.
- **Save** — saves the pipeline as a draft and runs local validation.
- **Compile** — translates your visual pipeline into a runnable job. A modal shows progress phase by phase.
- **Deploy** — submits the compiled pipeline to the runtime. The portal polls until the pipeline reaches the *deployed* status.
- **Pause, Resume, Cancel** — appear on the canvas while a pipeline is running. See [Pause, resume, or cancel a pipeline](../how-to/pause-resume-or-cancel-a-pipeline.md).
- **View Logs** — opens the Observability panel for this pipeline.

While a pipeline is running, the canvas also shows live metrics: records in, records out, and records filtered per operator, plus throughput on each connection.

## Pipeline statuses in Daitics DTX Portal {#pipeline-statuses-in-daitics-dtx-portal}

Each pipeline in Daitics DTX Portal has a status badge that tells you where it is in its lifecycle:

- **Draft** — saved but not yet compiled. You can edit freely.
- **Compiled** — translated into a runnable job, ready to deploy.
- **Deployed** — running on the runtime.
- **Paused** — stopped at a savepoint. Resume picks up from where it stopped.
- **Cancelled** — stopped without a savepoint. Cannot be resumed.
- **Failed** — the deploy or run attempt did not succeed. Open the pipeline to see why.

## Limits and things to know about pipelines {#limits-and-things-to-know-about-pipelines}

A few things to keep in mind when working with pipelines in Daitics DTX Portal:

- You must save a pipeline before you can compile it, and compile it before you can deploy it.
- Deleting a pipeline is a soft archive. The pipeline disappears from the list but can be restored by an administrator if needed.
- Cancelling a running pipeline is a hard stop with no savepoint. The portal asks you to confirm before doing it.
- A pipeline that fails to compile keeps your most recent draft. Fix the issue and compile again.
- The Adaptor Palette only lists operators your environment has installed. If you cannot find an operator you expect, ask your administrator.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common pipeline tasks in Daitics DTX Portal:

- [Create a pipeline](../how-to/create-a-pipeline.md)
- [Compile and deploy a pipeline](../how-to/compile-and-deploy-a-pipeline.md)
- [Pause, resume, or cancel a pipeline](../how-to/pause-resume-or-cancel-a-pipeline.md)
- [Duplicate or delete a pipeline](../how-to/duplicate-or-delete-a-pipeline.md)
