---
id: features/synthetic-data
title: Synthetic Data in Daitics DTX Portal
category: features
summary: Synthetic Data produces realistic test records on demand. Use Generators to create data, Universes to coordinate related generators, and Data Pools for shared reference data.
tags: [synthetic-data, generators, universes, data-pools, test-data, sdg]
aliases:
  - what is synthetic data
  - sdg
  - test data
  - data generator
  - fake data
  - mock data
  - dummy data
last_updated: 2026-05-02
version: 1
---

# Synthetic Data in Daitics DTX Portal

## What Synthetic Data is in Daitics DTX Portal {#what-synthetic-data-is-in-daitics-dtx-portal}

Synthetic Data in Daitics DTX Portal produces realistic, made-up records that match a schema. You use it to test pipelines, fill out development environments, or load-test infrastructure without using real customer data. The portal calls this feature SDG (Synthetic Data Generation) in some places.

Synthetic Data has three building blocks:

- **Generators** — produce records of one shape into one destination.
- **Universes** — group several generators together, so the records they produce are consistent across systems.
- **Data Pools** — shared reference data that the platform manages for you.

## When you would use Synthetic Data in Daitics DTX Portal {#when-you-would-use-synthetic-data-in-daitics-dtx-portal}

You would use Synthetic Data in Daitics DTX Portal whenever you need data but cannot or should not use production data. Common situations:

- Test a new pipeline before it sees real traffic.
- Load-test Kafka, Postgres, or the cache.
- Demo the platform without exposing customer information.
- Reproduce a bug that depends on specific data shapes.

## Where to find Synthetic Data in Daitics DTX Portal {#where-to-find-synthetic-data-in-daitics-dtx-portal}

Synthetic Data in Daitics DTX Portal lives under the **Data Management** section of the sidebar. Inside it you will find four pages:

- **Synthetic Data** (dashboard) — overview tiles and shortcuts.
- **Generators** — list of all generators.
- **Universes** — list of all universes.
- **Pools** — list of system-managed data pools.

## What a generator does in Daitics DTX Portal {#what-a-generator-does-in-daitics-dtx-portal}

A generator in Daitics DTX Portal produces records that match a schema and writes them to a destination. You configure the schema source, the destination, and how fast or how many records to produce.

Generator destinations include:

- **Kafka** — write to a topic, optionally with a key field.
- **PostgreSQL** — write to a table.
- **Dragonfly** — write to the distributed cache.
- **File** — write to a path on disk in JSON Lines, Parquet, or CSV format.

Generation runs in two modes:

- **Batch** — produce a fixed number of records, then stop. You set the total and the batch size.
- **Real-Time** — produce records continuously at a rate you set, up to an optional maximum.

You can start, pause, resume, and stop a generator at any time from its detail page.

## What a universe does in Daitics DTX Portal {#what-a-universe-does-in-daitics-dtx-portal}

A universe in Daitics DTX Portal groups several generators so the data they produce stays consistent. For example, a "customer order" universe might have one generator for customers and one for orders, with orders depending on customers. The universe makes sure the order records reference customer IDs that the customer generator actually produced.

A universe has:

- A **name** and an optional **seed**. The seed makes runs reproducible — running the same universe with the same seed produces the same records every time.
- A list of **member generators**.
- For each member, a list of **dependencies** on other members.

## What a data pool is in Daitics DTX Portal {#what-a-data-pool-is-in-daitics-dtx-portal}

A data pool in Daitics DTX Portal is a set of reference data that the platform loads and refreshes for you. Generators and pipelines can read from a pool when they need realistic values for fields like country codes, currency symbols, or product categories.

You cannot create, edit, or delete pools — they are system-managed. You can:

- See each pool's status (Loaded, Loading, or Error).
- See last refresh time, record count, and memory usage.
- See which fields the pool exposes.
- Click **Refresh** on a single pool to reload it.
- Click **Refresh All Pools** to reload every pool at once.

The Pools page also shows a memory distribution chart so you can see which pools take up the most space.

## What you see on the synthetic data dashboard {#what-you-see-on-the-synthetic-data-dashboard}

The synthetic data dashboard in Daitics DTX Portal gives you an overview of all three building blocks at once. You see:

- Counts of generators, universes, and pools.
- Status summaries for active generators.
- Quick links to the Generators, Universes, and Pools pages.

## Limits and things to know about Synthetic Data {#limits-and-things-to-know-about-synthetic-data}

A few things to keep in mind when working with Synthetic Data in Daitics DTX Portal:

- Generated data is **not** real. Do not use it for anything that needs accurate values, such as financial reports.
- Real-Time generators keep running until you stop them. They do not stop on their own.
- Data pools are read-only. If you need different reference data, ask your administrator.
- Auto-mapping field configuration from a schema works for most schemas but can fail on unusual structures. The portal shows "Auto-mapping failed" if it cannot work out a mapping; you then map fields by hand.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common Synthetic Data tasks in Daitics DTX Portal:

- [Create a data generator](../how-to/create-a-data-generator.md)
- [Upload a data sample to shape a generator](../how-to/upload-a-data-sample.md)
- [Create a universe](../how-to/create-a-universe.md)
- [Refresh a data pool](../how-to/refresh-a-data-pool.md)
