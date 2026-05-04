---
id: overview/index
title: Daitics DTX Portal documentation
category: overview
summary: Daitics DTX Portal is a web app for building and running real-time data pipelines, plus the schemas, generators, and infrastructure they depend on.
tags: [daitics, dtx-portal, overview, pipelines, documentation]
aliases:
  - what is daitics dtx portal
  - what is the daitics portal
  - daitics overview
  - portal docs home
  - daitics documentation index
last_updated: 2026-05-02
version: 1
---

# Daitics DTX Portal documentation

## What Daitics DTX Portal is {#what-daitics-dtx-portal-is}

Daitics DTX Portal is a web app for building and running real-time data pipelines. You design pipelines visually, define and version data schemas, generate synthetic test data, manage Kafka topics and cache keys, watch system health, and manage user access — all from one place. You do not need to write code to use the portal.

## Who this documentation is for {#who-this-documentation-is-for}

This documentation is written for two roles who use Daitics DTX Portal:

- **Data engineers** — design and run pipelines, define schemas, and create synthetic data for testing.
- **Administrators** — manage user accounts, groups, and roles inside the portal.

You do not need to know how the portal is built. The pages here cover what you see in the app and the tasks you can complete.

## How this documentation is organized {#how-this-documentation-is-organized}

Daitics DTX Portal documentation is split into five sections so you can find the right page fast:

- **Getting started** — sign in for the first time, learn the layout, and pick your first task. See [Getting started](getting-started.md).
- **Features** — one page per area of the portal, describing what it is and what you can do with it. Lives under `features/`.
- **How-to guides** — step-by-step instructions for one task at a time. Lives under `how-to/`.
- **Troubleshooting** — common errors and what they mean. See [Troubleshooting](troubleshooting.md).
- **Glossary** — plain-language definitions of terms used in the portal. See [Glossary](glossary.md).

## Features covered in Daitics DTX Portal documentation {#features-covered-in-daitics-dtx-portal-documentation}

The features documentation in Daitics DTX Portal covers seven areas of the app:

- [Pipelines](features/pipelines.md) — visual builder for streaming and batch data pipelines.
- [Schema Registry](features/schema-registry.md) — versioned store for data schemas in JSON, AVRO, PROTO, and OpenAPI formats.
- [Synthetic Data](features/synthetic-data.md) — generators, universes, and data pools for producing test data.
- [Access Management](features/access-management.md) — users, groups, roles, and sessions. (Mostly for administrators.)
- [Kafka](features/kafka.md) — browse Kafka topics, partitions, and messages.
- [Cache](features/cache.md) — browse and manage keys in the distributed cache.
- [Observability](features/observability.md) — system health, metrics, alerts, and service status.

## Where to start in Daitics DTX Portal {#where-to-start-in-daitics-dtx-portal}

Start with the page that matches what you need to do in Daitics DTX Portal:

- **First time signing in?** Read [Getting started](getting-started.md).
- **Data engineer building a pipeline?** Read [Create a pipeline](how-to/create-a-pipeline.md). Pipelines often depend on schemas, so you may also want [Create a schema](how-to/create-a-schema.md) first.
- **Administrator setting up access?** Read [Add a user to a role](how-to/add-a-user-to-a-role.md) and [Create a custom role](how-to/create-a-custom-role.md).
- **Something not working?** Read [Troubleshooting](troubleshooting.md).
- **Confused by a term?** Read the [Glossary](glossary.md).

## All how-to guides for Daitics DTX Portal {#all-how-to-guides-for-daitics-dtx-portal}

The how-to guides for Daitics DTX Portal are grouped here by feature area. Each guide focuses on one task.

**Pipelines:**

- [Create a pipeline](how-to/create-a-pipeline.md)
- [Compile and deploy a pipeline](how-to/compile-and-deploy-a-pipeline.md)
- [Pause, resume, or cancel a pipeline](how-to/pause-resume-or-cancel-a-pipeline.md)
- [Duplicate or delete a pipeline](how-to/duplicate-or-delete-a-pipeline.md)

**Schema Registry:**

- [Create a schema](how-to/create-a-schema.md)
- [Save a new schema version](how-to/save-a-new-schema-version.md)
- [Archive a schema](how-to/archive-a-schema.md)

**Synthetic Data:**

- [Create a data generator](how-to/create-a-data-generator.md)
- [Upload a data sample to shape a generator](how-to/upload-a-data-sample.md)
- [Create a universe](how-to/create-a-universe.md)
- [Refresh a data pool](how-to/refresh-a-data-pool.md)

**Kafka:**

- [Create a Kafka topic](how-to/create-a-kafka-topic.md)
- [Browse Kafka messages](how-to/browse-kafka-messages.md)
- [Delete or truncate a Kafka topic](how-to/delete-or-truncate-a-kafka-topic.md)

**Cache:**

- [Create a cache key](how-to/create-a-cache-key.md)

**Observability:**

- [Check system health](how-to/check-system-health.md)

**Access Management (administrators):**

- [Add a user to a role](how-to/add-a-user-to-a-role.md)
- [Assign a role to a group](how-to/assign-a-role-to-a-group.md)
- [Create a custom role](how-to/create-a-custom-role.md)
- [Reset a user password](how-to/reset-a-user-password.md)
- [Terminate a user session](how-to/terminate-a-user-session.md)

## What this documentation does not cover {#what-this-documentation-does-not-cover}

Daitics DTX Portal documentation focuses on what end users see and do. It does not cover:

- How the portal is built or deployed.
- Admin tasks performed outside the portal, such as installing Daitics or configuring Keycloak.
- Approval workflows. The Approval Workflows feature is still in development and will be documented when it is ready for general use.
- Pages you may see labelled "Coming soon" in the sidebar, including Guides, Projects, Settings, and Support.

If you cannot find what you need, ask your Daitics administrator.
