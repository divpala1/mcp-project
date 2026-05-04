---
id: how-to/create-a-data-generator
title: Create a data generator in Daitics DTX Portal
category: how-to
summary: To create a data generator, open Synthetic Data → Generators, click New Generator, and complete the five-step wizard — Basic Info, Schema, Destination, Generation Config, Review.
tags: [generator, synthetic-data, sdg, create, test-data]
aliases:
  - new generator
  - new data generator
  - create generator
  - synthetic data generator
  - fake data generator
last_updated: 2026-05-02
version: 1
---

# Create a data generator in Daitics DTX Portal

## What this does {#what-this-does}

Creating a data generator in Daitics DTX Portal sets up a producer that writes records matching a schema to a destination of your choice. The five-step wizard collects everything the generator needs: a name, the schema it should follow, where the data should go, how fast or how many records to produce, and a final review. Once created, you can start, pause, resume, and stop the generator from its detail page.

## When you would create a data generator {#when-you-would-create-a-data-generator}

You would create a data generator in Daitics DTX Portal when you need to:

- Test a pipeline without using real production data.
- Load-test Kafka, a database, the cache, or files.
- Demo the platform without exposing customer data.
- Generate sample data that matches a known schema for development work.

## Steps to create a data generator {#steps-to-create-a-data-generator}

Follow these steps to create a data generator in Daitics DTX Portal:

1. In the sidebar, click **Data Management → Synthetic Data → Generators**.
2. Click **New Generator** in the top-right.
3. **Step 1: Basic Info**. Enter:
   - **Name** (required).
   - **Description** (optional).
4. Click **Next**.
5. **Step 2: Schema**. Pick where the schema comes from:
   - **Registry** — pick an existing schema from the dropdown.
   - **Custom** — paste a schema definition into the editor.
   Choose a format (JSON, AVRO, or PROTO).
6. Click **Next**.
7. **Step 3: Destination**. Pick where the generator should write:
   - **Kafka** — enter a topic name and an optional key field.
   - **PostgreSQL** — pick a connection and table.
   - **Dragonfly** — pick a key pattern.
   - **File** — set a path and pick a format (JSON Lines, Parquet, or CSV).
8. Click **Next**.
9. **Step 4: Generation Config**. Pick the generation mode:
   - **Batch** — set total record count and batch size.
   - **Real-Time** — set records per second and an optional maximum.
   The wizard auto-maps fields from the schema. Adjust the mappings if needed.
10. Click **Next**.
11. **Step 5: Review**. Read the full configuration. Click **Create Generator**.

![Synthetic Data generator wizard on the Destination step](TODO/screenshots/generator-wizard-destination.png)

## What to expect after creating a data generator {#what-to-expect-after-creating-a-data-generator}

After creating a data generator in Daitics DTX Portal, you should see:

- The generator appears on the Generators list with status **Stopped** (or your environment's equivalent for "ready but not running").
- The generator's detail page opens.
- A green toast confirms "Generator created".

A new generator does not start producing records on its own. Click **Start** on its detail page when you are ready.

## If something goes wrong creating a data generator {#if-something-goes-wrong-creating-a-data-generator}

If something goes wrong while creating a data generator in Daitics DTX Portal, check the most likely causes:

- **"Auto-mapping failed"** — the wizard could not work out a default mapping from the schema. Set the field mappings by hand on Step 4.
- **"Failed to create generator"** — the wizard could not save. Check your network and try again. If the error mentions permissions, ask your administrator.
- **The schema you want is not in the dropdown** — the schema may be deprecated or archived. Open it in Schema Registry to check; if it is archived, you cannot use it for a new generator.
- **Kafka destination errors** — the topic may not exist yet. Create it first — see [Create a Kafka topic](create-a-kafka-topic.md).
- **Field mappings show "type mismatch"** — the destination expects a different type than the schema field. Pick a different destination field or update the schema.

For more help, see [Troubleshooting](../troubleshooting.md).
