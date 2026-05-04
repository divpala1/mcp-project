---
id: how-to/create-a-kafka-topic
title: Create a Kafka topic in Daitics DTX Portal
category: how-to
summary: To create a Kafka topic, open Infrastructure → Kafka, click New Topic, then set the name, partition count, and replication factor in the dialog.
tags: [kafka, topic, create, partitions, replication]
aliases:
  - new kafka topic
  - create topic
  - add kafka topic
  - kafka new topic
  - make a topic
last_updated: 2026-05-02
version: 1
---

# Create a Kafka topic in Daitics DTX Portal

## What this does {#what-this-does}

Creating a Kafka topic in Daitics DTX Portal adds a new topic to the connected Kafka cluster directly from the portal — no command line required. The topic becomes immediately available for pipelines and generators to read from or write to.

## When you would create a Kafka topic {#when-you-would-create-a-kafka-topic}

You would create a Kafka topic in Daitics DTX Portal when you need to:

- Set up a destination for a new generator.
- Provide a source for a new pipeline.
- Build a fresh test topic to avoid mixing test data with existing topics.

Some teams prefer to manage topics through their infrastructure tooling instead. If your team has that policy, ask your administrator before creating topics from the portal.

## Steps to create a Kafka topic {#steps-to-create-a-kafka-topic}

Follow these steps to create a Kafka topic in Daitics DTX Portal:

1. In the sidebar, click **Infrastructure → Kafka**.
2. Click **New Topic** in the top-right of the topics list.
3. Fill in the dialog:
   - **Name** — required. Topic names cannot include spaces or most punctuation.
   - **Partitions** — between 1 and 1000. More partitions allow more parallel readers, but also use more cluster resources.
   - **Replication factor** — at least 1. Production clusters usually use 2 or 3.
   - **Other settings** (retention, cleanup policy) if your cluster exposes them in the dialog.
4. Click **Create**.

If you are unsure what to pick, the defaults are usually safe for a test topic.

## What to expect after creating a Kafka topic {#what-to-expect-after-creating-a-kafka-topic}

After creating a Kafka topic in Daitics DTX Portal, you should see:

- The topic appears in the topics list immediately.
- A green toast confirms "Topic created".
- The topic has zero messages until something writes to it.

You can now pick the topic in a generator's destination dropdown or use it as a source in a pipeline.

## If something goes wrong creating a Kafka topic {#if-something-goes-wrong-creating-a-kafka-topic}

If something goes wrong while creating a Kafka topic in Daitics DTX Portal, check the most likely causes:

- **"Topic already exists"** — pick a different name. Topic names must be unique within the cluster.
- **"Partitions must be between 1 and 1000"** — adjust the partition count to fit the limit.
- **"Replication factor must be at least 1"** — the replication factor cannot be zero.
- **"Failed to create topic"** — the Kafka cluster did not accept the request. Check the toast's details. If it mentions broker availability or permissions, ask your administrator.
- **You do not see "New Topic" button** — your account may not have the role needed. Ask your administrator.

For more help, see [Troubleshooting](../troubleshooting.md).
