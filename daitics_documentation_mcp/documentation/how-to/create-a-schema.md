---
id: how-to/create-a-schema
title: Create a schema in Daitics DTX Portal
category: how-to
summary: To create a schema, open Schema Registry, click New Schema, and complete the three-step wizard — Basic Info, Schema, and Review.
tags: [schema, create, new, schema-registry, wizard]
aliases:
  - new schema
  - add a schema
  - register a schema
  - define a schema
  - first schema
last_updated: 2026-05-02
version: 1
---

# Create a schema in Daitics DTX Portal

## What this does {#what-this-does}

Creating a schema in Daitics DTX Portal registers the shape of your data with the platform. Once registered, the schema can be reused by pipelines, generators, and any other feature that needs to know what records look like. The schema is stored as version 1.0.0 and gets a new version every time you save changes later.

## When you would create a schema {#when-you-would-create-a-schema}

You would create a schema in Daitics DTX Portal when you need to:

- Describe a new type of record before building a pipeline that processes it.
- Set up a contract that several teams or tools will share.
- Test a generator that produces data matching a known shape.

If a schema already exists for the data you are working with, do not create a new one. Edit the existing schema instead — see [Save a new schema version](save-a-new-schema-version.md).

## Steps to create a schema {#steps-to-create-a-schema}

Follow these steps to create a schema in Daitics DTX Portal:

1. In the sidebar, click **Data Management → Schema Registry**.
2. Click **New Schema** in the top-right of the list.
3. The wizard opens to the **Basic Info** step. Fill in:
   - **Name** (required).
   - **Description** — optional but useful.
   - **Version** — defaults to `1.0.0`. You usually leave this alone for a new schema.
   - **Tags** — optional labels for easier searching later.
   - **Format** — pick JSON, AVRO, PROTO, or OpenAPI.
4. Click **Next**.
5. On the **Schema** step, paste or type the schema definition into the editor. The editor validates against the format you chose. Errors appear inline.
6. Click **Next**.
7. On the **Review** step, check the summary. If anything is wrong, click **Back**.
8. Click **Create Schema**.

![Schema Registry create wizard on the Schema step](TODO/screenshots/schema-create-wizard.png)

## What to expect after creating a schema {#what-to-expect-after-creating-a-schema}

After creating a schema in Daitics DTX Portal, you should see:

- The schema appears on the Schema Registry list with status **Active**.
- The schema's detail page opens, showing the Overview, Schema, Fields, Versions, and Settings tabs.
- Version `1.0.0` is recorded in the Versions tab.
- A green toast confirms "Schema created".

You can now use the schema in pipelines and generators by selecting it from a schema dropdown.

## If something goes wrong creating a schema {#if-something-goes-wrong-creating-a-schema}

If something goes wrong while creating a schema in Daitics DTX Portal, check the most likely causes:

- **"Name already exists"** — every schema name must be unique. Pick a different name or open the existing schema.
- **Schema editor shows red error markers** — the schema does not match the format you picked. Read the inline error and fix the syntax. AVRO requires record types and listed required fields.
- **"Failed to create schema"** — the wizard could not save. Check your network and try again. If the error mentions permissions, ask your administrator.
- **You do not see "New Schema" button** — your account may not have the role needed to create schemas. Ask your administrator.

For more help, see [Troubleshooting](../troubleshooting.md).
