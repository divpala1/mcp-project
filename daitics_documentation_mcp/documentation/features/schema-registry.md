---
id: features/schema-registry
title: Schema Registry in Daitics DTX Portal
category: features
summary: Schema Registry is a versioned store for the shape of your data. Pipelines and generators reuse schemas so all parts of the platform agree on field names and types.
tags: [schema-registry, schemas, json, avro, proto, openapi, versioning]
aliases:
  - what is schema registry
  - data schema
  - schema versioning
  - avro schema
  - json schema
  - proto schema
  - schema management
last_updated: 2026-05-02
version: 1
---

# Schema Registry in Daitics DTX Portal

## What Schema Registry is in Daitics DTX Portal {#what-schema-registry-is-in-daitics-dtx-portal}

Schema Registry in Daitics DTX Portal is a versioned store for the shape of your data. A schema lists the fields each record contains, their types, and which fields are required. You define a schema once, then reuse it in pipelines, data generators, and other parts of the portal so every system agrees on the same field names and types.

Schema Registry stores every change as a new version. Old versions stay available, so a pipeline using an older version keeps working when the schema changes.

## Schema formats supported in Daitics DTX Portal {#schema-formats-supported-in-daitics-dtx-portal}

Schema Registry in Daitics DTX Portal supports four schema formats:

- **JSON Schema** — the standard JSON-based way to describe records.
- **AVRO** — a compact format used widely in Kafka pipelines.
- **PROTO** — Protocol Buffers, used in many Google-derived systems.
- **OpenAPI** — describes API request and response shapes.

Pick the format that matches the systems your data already uses. If you are unsure, JSON Schema is the most general choice.

## When you would use Schema Registry in Daitics DTX Portal {#when-you-would-use-schema-registry-in-daitics-dtx-portal}

You would use Schema Registry in Daitics DTX Portal whenever you need a single source of truth for what your data looks like. Common situations:

- A pipeline reads records from Kafka and a synthetic data generator writes to Kafka — both need to agree on the format.
- Several teams share the same data and need consistent field names and types.
- A field changes (you add a column, or rename one) and you need to keep the old version available for systems that have not updated yet.

## Where to find Schema Registry in Daitics DTX Portal {#where-to-find-schema-registry-in-daitics-dtx-portal}

Schema Registry in Daitics DTX Portal lives under the **Data Management** section of the sidebar. Click **Schema Registry** to open the list of all schemas. Click a schema name to open its detail page. Click **New Schema** in the top-right of the list to create a new schema.

## What you can do on the Schema Registry list page {#what-you-can-do-on-the-schema-registry-list-page}

The Schema Registry list page in Daitics DTX Portal shows every schema in the registry, with these tools:

- **Search** — by schema name or description.
- **Status filter** — Active, Deprecated, or Archived.
- **Format filter** — JSON, AVRO, PROTO, or OpenAPI.
- **Row actions** — View (open the detail page), Edit (open in the wizard), Archive (mark as no longer used).

A schema's status badge shows at a glance whether it is Active (in normal use), Deprecated (still works but should not be used in new pipelines), or Archived (frozen and hidden from new uses).

## What you see on the schema detail page {#what-you-see-on-the-schema-detail-page}

The schema detail page in Daitics DTX Portal has five tabs:

- **Overview** — name, description, current version, format, owner, and tags.
- **Schema** — the raw schema text in its native format.
- **Fields** — a column-by-column breakdown of every field, with type and whether it is required.
- **Versions** — the history of changes, including change notes. You can compare any two versions.
- **Settings** — configuration that applies to all versions of the schema.

## How schema versions work in Daitics DTX Portal {#how-schema-versions-work-in-daitics-dtx-portal}

Schema versions in Daitics DTX Portal are numbered using the pattern `major.minor.patch`, starting at `1.0.0`. Every save of a schema in edit mode creates a new version with a change note describing what changed. When you save a new version, the registry runs a compatibility check against the previous version and warns if the change is breaking. You can override the warning if you accept the impact.

Old versions are never deleted. Pipelines and generators using an old version keep running until you switch them to the new one.

## Limits and things to know about Schema Registry {#limits-and-things-to-know-about-schema-registry}

A few things to keep in mind when working with Schema Registry in Daitics DTX Portal:

- Marking a schema as **Deprecated** requires the admin role. If the action is greyed out, ask your administrator.
- A deprecated schema still works in existing pipelines. Deprecation is a signal, not an automatic shutdown.
- Archiving a schema disables creating new versions of it.
- The wizard runs format-specific validation. AVRO requires record types and required fields, for example. The wizard tells you exactly what is wrong.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common Schema Registry tasks in Daitics DTX Portal:

- [Create a schema](../how-to/create-a-schema.md)
- [Save a new schema version](../how-to/save-a-new-schema-version.md)
- [Archive a schema](../how-to/archive-a-schema.md)
