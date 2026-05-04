---
id: how-to/create-a-universe
title: Create a universe in Daitics DTX Portal
category: how-to
summary: To create a universe, open Synthetic Data → Universes, click New Universe, name it, optionally set a seed, add member generators, and mark which depend on which.
tags: [universe, synthetic-data, sdg, dependencies, create]
aliases:
  - new universe
  - create universe
  - sdg universe
  - link generators
  - coordinate generators
last_updated: 2026-05-02
version: 1
---

# Create a universe in Daitics DTX Portal

## What this does {#what-this-does}

Creating a universe in Daitics DTX Portal groups several generators so the data they produce stays consistent. For example, a "customer order" universe might include a customer generator and an order generator, with the order generator depending on the customer generator. The universe makes sure that every order references a customer that the customer generator actually produced. Optionally, a universe can use a seed so that running it twice produces the same records both times.

## When you would create a universe {#when-you-would-create-a-universe}

You would create a universe in Daitics DTX Portal when you need to:

- Generate two or more related types of records together (for example, customers and their orders).
- Make a test environment reproducible by re-using the same seed for every run.
- Coordinate several generators so their output is consistent across systems.

If you only need one type of record, do not create a universe. A single generator is enough.

## Steps to create a universe {#steps-to-create-a-universe}

Follow these steps to create a universe in Daitics DTX Portal:

1. In the sidebar, click **Data Management → Synthetic Data → Universes**.
2. Click **New Universe** in the top-right.
3. Enter a **Name**.
4. Optionally enter a **Seed**. Using a seed makes runs reproducible — running the universe twice with the same seed produces the same records.
5. In the **Members** section, pick generators to include from the dropdown.
6. For each member, mark its dependencies on other members by ticking the relevant checkboxes.
7. Click **Create Universe**.

The universe needs at least one member generator. If you skip Members, the create button stays disabled.

## What to expect after creating a universe {#what-to-expect-after-creating-a-universe}

After creating a universe in Daitics DTX Portal, you should see:

- The universe appears on the Universes list with its name and member count.
- The universe's detail page opens, showing every member generator and its dependencies.
- A green toast confirms "Universe created".

A new universe does not start producing data on its own. Open the universe and start its member generators when you are ready.

## If something goes wrong creating a universe {#if-something-goes-wrong-creating-a-universe}

If something goes wrong while creating a universe in Daitics DTX Portal, check the most likely causes:

- **The Members dropdown is empty** — there are no generators in your environment yet. Create at least one generator first — see [Create a data generator](create-a-data-generator.md).
- **"Cyclic dependency"** — two generators depend on each other in a way that the universe cannot resolve. Remove one of the dependency ticks.
- **"Failed to create universe"** — check your network and try again. If the error mentions permissions, ask your administrator.
- **Records do not look related across generators** — confirm the dependency direction. The dependent generator should reference fields from the generator it depends on, not the other way around.

For more help, see [Troubleshooting](../troubleshooting.md).
