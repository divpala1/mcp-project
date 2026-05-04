---
id: how-to/create-a-pipeline
title: Create a pipeline in Daitics DTX Portal
category: how-to
summary: To create a pipeline, open the Pipelines list, click New Pipeline, fill in the settings modal, then drag operators onto the canvas and connect them.
tags: [pipeline, create, new, designer, canvas]
aliases:
  - new pipeline
  - build a pipeline
  - design a pipeline
  - start a pipeline
  - add a pipeline
last_updated: 2026-05-02
version: 1
---

# Create a pipeline in Daitics DTX Portal

## What this does {#what-this-does}

Creating a pipeline in Daitics DTX Portal opens an empty visual canvas where you drag operator boxes (sources, processors, sinks) and connect them with lines to define how data should flow. When you save, the pipeline is stored as a draft. You compile and deploy it as separate steps later.

## When you would create a pipeline {#when-you-would-create-a-pipeline}

You would create a pipeline in Daitics DTX Portal when you need to:

- Move records between two systems, for example from a Kafka topic to a database.
- Filter, enrich, or reshape records on their way through.
- Run a one-off transformation across a fixed batch of records.

If you only want to test how a pipeline behaves with sample data, you can build the pipeline first and use a [data generator](create-a-data-generator.md) to feed it.

## Steps to create a pipeline {#steps-to-create-a-pipeline}

Follow these steps to create a pipeline in Daitics DTX Portal:

1. In the sidebar, click **Pipelines**.
2. On the Pipelines list page, click **New Pipeline** in the top-right.
3. The **Settings** modal opens. Fill in:
   - **Name** — required. Use letters, numbers, spaces, and the punctuation `- _ . : , ( )`.
   - **Description** — optional, but helpful for teammates.
   - **Mode** — pick **Streaming** for continuous processing or **Batch** for a one-off run.
4. Click **Save** in the modal. The designer opens with an empty canvas.
5. Click the floating **+** button on the canvas. The Adaptor Palette opens.
6. Search or filter for an operator by category (Source, Process, Sink). Drag the operator onto the canvas. It appears as a node with input and output handles.
7. Click the operator to open the side configuration panel. Set its input and output field mappings and any operator-specific settings.
8. Repeat steps 5–7 to add more operators.
9. Connect operators by dragging from an output handle on one to an input handle on the next. If a connection is not valid, the canvas shows a banner explaining why.
10. Click **Save** in the top bar of the designer. The pipeline is saved as a **draft**.

![Pipeline designer with Adaptor Palette open](TODO/screenshots/pipeline-adaptor-palette.png)

## What to expect after creating a pipeline {#what-to-expect-after-creating-a-pipeline}

After you create a pipeline in Daitics DTX Portal, you should see:

- The pipeline appears on the **Pipelines** list with the status **Draft**.
- Local validation has run — if anything is wrong, the canvas highlights it.
- A green toast message confirms "Pipeline saved" in the corner of the screen.

A draft pipeline does not run. To run it, you compile and then deploy. See [Compile and deploy a pipeline](compile-and-deploy-a-pipeline.md).

## If something goes wrong creating a pipeline {#if-something-goes-wrong-creating-a-pipeline}

If something goes wrong while creating a pipeline in Daitics DTX Portal, check the most likely causes:

- **"Failed to save pipeline"** — usually a validation error. Open the designer's validation banner to see which operator or connection is the problem.
- **The Adaptor Palette is empty or missing operators you expect** — your environment may not have those operators installed. Ask your administrator.
- **You cannot connect two operators** — the canvas tells you why. Common causes are mismatched field types or trying to connect a sink to another sink.
- **You do not see "New Pipeline" button** — your account may not have the role needed to create pipelines. Ask your administrator.

For more help, see [Troubleshooting](../troubleshooting.md).
