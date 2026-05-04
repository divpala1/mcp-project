---
id: glossary/glossary
title: Glossary of Daitics DTX Portal terms
category: glossary
summary: Plain-language definitions of terms used in Daitics DTX Portal — from Adaptor and Compile to Universe and Savepoint.
tags: [glossary, terms, definitions, vocabulary]
aliases:
  - terms
  - definitions
  - what does X mean
  - daitics vocabulary
last_updated: 2026-05-02
version: 1
---

# Glossary of Daitics DTX Portal terms

This page defines the terms you will see while using Daitics DTX Portal. Each entry is short on purpose. For deeper coverage, follow the links into the features and how-to sections.

## Adaptor {#adaptor}

An Adaptor is the operator catalog inside the pipeline designer's Adaptor Palette. Each adaptor is a draggable building block — a source, a processor, or a sink — that you place on the canvas to build a pipeline.

<!-- aliases: operator, connector, adapter, building block -->

## Adaptor Palette {#adaptor-palette}

The Adaptor Palette is the floating panel that opens when you click the **+** button on a pipeline canvas. It lists every adaptor available in your environment, grouped by category, and lets you search and drag them onto the canvas.

<!-- aliases: operator palette, palette, operator list -->

## Alert {#alert}

An Alert in the Observability dashboard is a notification that something crossed a threshold — for example, a service went down or latency spiked. Alerts are grouped by severity (critical, warning, info) and clear automatically when the underlying condition is resolved.

<!-- aliases: notification, warning, observability alert -->

## Archive (schema) {#archive-schema}

Archive is the action that hides a schema from new uses without deleting it. Archived schemas keep working in the pipelines and generators that already reference them, but they cannot be picked when creating new ones, and you cannot save new versions of them.

<!-- aliases: archive schema, retire schema, hide schema -->

## Batch mode {#batch-mode}

Batch mode runs a pipeline or generator over a fixed amount of data and then stops. You set the total record count for a generator, or the input file or table for a pipeline.

<!-- aliases: batch, one-off run, finite mode -->

## Cancel (pipeline) {#cancel-pipeline}

Cancel is a hard stop for a running pipeline. It ends the pipeline immediately without creating a savepoint. A cancelled pipeline cannot be resumed — you must redeploy it from scratch to run it again.

<!-- aliases: hard stop, kill pipeline, abort pipeline -->

## Compatibility check {#compatibility-check}

The compatibility check runs when you save a new schema version. It compares the new version against the previous one and warns you if your changes are breaking — for example, if you renamed a required field. You can override the warning if you accept the impact.

<!-- aliases: schema compatibility, breaking change check, schema diff -->

## Compile (pipeline) {#compile-pipeline}

Compile turns the visual pipeline you built on the canvas into a runnable job. Compiling does not start the pipeline; it only validates and translates it. Deploy is the next step that actually runs the job.

<!-- aliases: build pipeline, validate pipeline -->

## Cache (Dragonfly) {#cache-dragonfly}

The Cache is the platform's distributed in-memory store. It uses Dragonfly, which is compatible with Redis. Pipelines and services use the cache for fast-access data. Anything stored in the cache is short-lived — it may be evicted when memory is full.

<!-- aliases: distributed cache, dragonfly, redis, in-memory store -->

## Data Pool {#data-pool}

A Data Pool is a system-managed set of reference data that generators and pipelines can read from for realistic field values like country codes or product categories. Pools are not user-editable; you can only refresh them.

<!-- aliases: pool, reference data, lookup data -->

## Deploy (pipeline) {#deploy-pipeline}

Deploy submits a compiled pipeline to the runtime so it starts processing data. After deployment the pipeline reaches the **Deployed** status and the canvas shows live metrics on each operator.

<!-- aliases: launch pipeline, run pipeline, start pipeline -->

## Deprecate (schema) {#deprecate-schema}

Deprecate marks a schema as discouraged but still working. Pipelines and generators using a deprecated schema keep running. New work should use a different schema. Only administrators can deprecate.

<!-- aliases: discourage schema, mark schema deprecated -->

## Designer (pipeline) {#designer-pipeline}

The Pipeline Designer is the full-screen visual canvas where you build, save, compile, and deploy pipelines. You add operators by dragging from the Adaptor Palette, configure them on a side panel, and connect them with lines.

<!-- aliases: pipeline canvas, visual builder, pipeline editor -->

## Generator {#generator}

A Generator produces synthetic records that match a schema and writes them to a destination such as Kafka, PostgreSQL, Dragonfly, or a file. Generators run in batch mode (a fixed number of records) or real-time mode (a continuous rate).

<!-- aliases: data generator, synthetic data generator, fake data producer -->

## Group (user group) {#group-user-group}

A Group bundles users together so administrators can grant the same roles to many people at once. Adding a user to a group automatically gives them every role assigned to the group.

<!-- aliases: user group, team, role group -->

## Health badge (cluster health) {#health-badge-cluster-health}

The cluster health badge sits at the top of the Observability dashboard and summarises platform health in one word: **Healthy**, **Degraded**, or **Unhealthy**. It is a quick answer to "is anything broken right now?".

<!-- aliases: cluster health, health status, system status -->

## Identity service (Keycloak) {#identity-service-keycloak}

The Identity service is the system that decides who can sign in to the portal. Daitics DTX Portal uses Keycloak as its identity service. Users, groups, and password resets all live in the identity service — the portal just shows them.

<!-- aliases: keycloak, sso, auth provider, identity provider -->

## Limit (Kafka message browser) {#limit-kafka-message-browser}

The Limit is the maximum number of records the Kafka message browser will load in one page. You can set it between 10 and 500.

<!-- aliases: page size, message limit, batch size -->

## Mode (streaming or batch) {#mode-streaming-or-batch}

Mode is the run style of a pipeline or generator. **Streaming** processes records continuously as they arrive. **Batch** processes a fixed amount of data and then stops.

<!-- aliases: pipeline mode, generation mode, run mode -->

## Offset (Kafka) {#offset-kafka}

An Offset is the position of a record in a Kafka partition. The Kafka message browser uses offsets to decide where to start reading: **Earliest** reads from the beginning of the partition, **Latest** reads only new records.

<!-- aliases: kafka offset, position, starting point -->

## Operator (pipeline) {#operator-pipeline}

An Operator is one box on the pipeline canvas. It performs one role: read data (source), transform data (process), or write data (sink). Operators have input and output handles you connect with lines.

<!-- aliases: node, pipeline node, processor, adaptor instance -->

## Pause (pipeline) {#pause-pipeline}

Pause stops a running pipeline at a savepoint. The pipeline reaches the **Paused** state, and you can resume it later from exactly where it stopped. Pause is the safe way to temporarily stop a pipeline.

<!-- aliases: pause pipeline, suspend pipeline -->

## Permission {#permission}

A Permission is one specific allowed action — for example, "read pipelines" or "delete schemas". Roles are bundles of permissions. Custom roles let you pick the exact permissions you want.

<!-- aliases: rights, access right, allowed action -->

## Pipeline {#pipeline}

A Pipeline is a visual data flow that reads from one or more sources, processes the data, and writes it to one or more destinations. Pipelines run in streaming mode or batch mode.

<!-- aliases: data pipeline, data flow, etl, streaming pipeline -->

## Profile (data sample) {#profile-data-sample}

A Profile is the analyzed result of a data sample you upload to a generator. Applying a profile updates the generator's field rules so its output mirrors the value distributions of your sample.

<!-- aliases: data profile, sample profile, generator profile -->

## Real-Time mode {#real-time-mode}

Real-Time mode runs a generator at a fixed rate of records per second, optionally up to a maximum. The generator keeps producing until you stop it.

<!-- aliases: streaming mode (generator), continuous mode -->

## Resume (pipeline) {#resume-pipeline}

Resume restarts a paused pipeline from its savepoint. The pipeline picks up exactly where it left off — no records are reprocessed.

<!-- aliases: restart pipeline, continue pipeline -->

## Role {#role}

A Role is a named bundle of permissions. Administrators assign roles to users or groups to grant access. The portal has built-in system roles that cannot be edited and custom roles administrators create.

<!-- aliases: rbac role, access role, permission set -->

## Savepoint {#savepoint}

A Savepoint is a snapshot of a pipeline's progress. The portal creates one when you pause a pipeline, so resume can pick up where it left off without re-processing records.

<!-- aliases: checkpoint, snapshot, pipeline state -->

## Schema {#schema}

A Schema is a definition of the shape of your data — field names, types, and which fields are required. Schemas live in the Schema Registry and are reused by pipelines and generators.

<!-- aliases: data schema, record schema, data shape, contract -->

## Schema Registry {#schema-registry}

The Schema Registry is the versioned store for schemas in Daitics DTX Portal. It supports JSON, AVRO, PROTO, and OpenAPI formats and keeps every change as a new version.

<!-- aliases: registry, schema store -->

## Seed (universe) {#seed-universe}

A Seed is a value that makes a universe's output reproducible. Running the same universe with the same seed produces the same records both times.

<!-- aliases: random seed, reproducibility seed -->

## Session {#session}

A Session represents one signed-in browser window for one user. Each session has a sign-in time and an identifier. Administrators can terminate individual sessions to force a user to sign in again.

<!-- aliases: signed-in session, login session, browser session -->

## Sink (operator) {#sink-operator}

A Sink is an operator that writes data out of a pipeline — to a Kafka topic, a database, the cache, or a file. Pipelines usually end with one or more sinks.

<!-- aliases: destination operator, output operator -->

## Source (operator) {#source-operator}

A Source is an operator that reads data into a pipeline — from a Kafka topic, a database, the cache, or a file. Pipelines usually start with one or more sources.

<!-- aliases: input operator, reader operator -->

## Status badge {#status-badge}

A Status Badge is a coloured label that shows the current state of a pipeline, schema, or data pool. For pipelines: Draft, Compiled, Deployed, Paused, Cancelled, Failed. For schemas: Active, Deprecated, Archived. For pools: Loaded, Loading, Error.

<!-- aliases: status label, state badge, pipeline status -->

## Streaming mode {#streaming-mode}

Streaming mode runs a pipeline continuously, processing records as they arrive. The pipeline keeps running until you pause or cancel it.

<!-- aliases: continuous mode, real-time mode (pipeline) -->

## Synthetic data {#synthetic-data}

Synthetic data is realistic but made-up records produced by a generator. It lets you test pipelines, fill development environments, and run demos without using real customer data.

<!-- aliases: test data, fake data, mock data, dummy data -->

## Topic (Kafka) {#topic-kafka}

A Topic is a named stream of records in Kafka. Records are written to a topic and read from a topic. Topics are split into partitions to allow parallel reading and writing.

<!-- aliases: kafka topic, stream, message queue -->

## TTL (time-to-live) {#ttl-time-to-live}

TTL is the lifespan of a cache key in seconds. When a key's TTL elapses, the cache deletes the key automatically. A key with no TTL never expires on its own, but may still be evicted under memory pressure.

<!-- aliases: time to live, expiry, key lifetime -->

## Truncate (Kafka topic) {#truncate-kafka-topic}

Truncate empties a Kafka topic by deleting every record on it. The topic itself stays in place. Truncate is useful for resetting a test topic between runs.

<!-- aliases: empty topic, clear topic -->

## Universe {#universe}

A Universe groups several generators so the data they produce stays consistent across systems. Members of a universe can depend on each other, and an optional seed makes runs reproducible.

<!-- aliases: generator group, coordinated generators -->

## User Group {#user-group}

See [Group](#group-user-group).

<!-- aliases: group, team, role group -->

## Version (schema) {#version-schema}

A Schema Version is one revision of a schema, identified by a `major.minor.patch` number. Every save in edit mode creates a new version. Old versions stay available, so existing pipelines and generators keep working when a schema changes.

<!-- aliases: schema version, semver -->
