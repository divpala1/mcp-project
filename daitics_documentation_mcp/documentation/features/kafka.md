---
id: features/kafka
title: Kafka in Daitics DTX Portal
category: features
summary: Kafka pages in Daitics DTX Portal let you list topics, see partition details, browse messages, and create, truncate, or delete topics from one place.
tags: [kafka, topics, partitions, messages, brokers, infrastructure]
aliases:
  - kafka topics
  - kafka management
  - browse kafka messages
  - kafka admin
  - topic browser
  - kafka ui
last_updated: 2026-05-02
version: 1
---

# Kafka in Daitics DTX Portal

## What Kafka pages do in Daitics DTX Portal {#what-kafka-pages-do-in-daitics-dtx-portal}

The Kafka pages in Daitics DTX Portal give you a web view of your Kafka cluster. You can see every topic, look inside partitions, browse messages, and create or remove topics — all without using a Kafka command-line tool. The portal does not run Kafka; it talks to whichever Kafka cluster your team has connected to it.

Kafka is a system that moves records between systems in order. Pipelines and synthetic data generators in the portal often read from or write to Kafka topics.

## When you would use Kafka pages in Daitics DTX Portal {#when-you-would-use-kafka-pages-in-daitics-dtx-portal}

You would use the Kafka pages in Daitics DTX Portal when you need to:

- Check whether a topic exists or how many messages it holds.
- Look at the actual records on a topic to debug a pipeline.
- Create a new topic for a pipeline or generator to write to.
- Empty a test topic before a fresh run.
- Delete a topic you no longer need.

## Where to find Kafka in Daitics DTX Portal {#where-to-find-kafka-in-daitics-dtx-portal}

Kafka pages in Daitics DTX Portal live under **Infrastructure → Kafka** in the sidebar. The Kafka section has two views:

- **Topics list** — every topic in the cluster.
- **Topic detail** — opens when you click a topic name.

## What you can do on the Kafka topics list {#what-you-can-do-on-the-kafka-topics-list}

The Kafka topics list in Daitics DTX Portal shows every topic with these columns and tools:

- **Columns** — Name, Partitions, Replication Factor, Message Count, Size.
- **Search** — by topic name.
- **Toggle internal vs user topics** — Kafka uses internal topics like `__consumer_offsets` for its own bookkeeping. The toggle hides them by default.
- **New Topic** — opens a dialog to create a topic.

Click any row to open the topic's detail page.

## What you can do on a Kafka topic detail page {#what-you-can-do-on-a-kafka-topic-detail-page}

The Kafka topic detail page in Daitics DTX Portal shows everything about one topic and lets you act on it:

- **Per-partition info** — leader broker, in-sync replicas, earliest and latest offsets.
- **Consumer groups** — every group reading from this topic and where each is up to.
- **Total messages** — across all partitions.
- **Browse messages** — open the message viewer to read actual records.
- **Truncate** — delete every record on the topic but keep the topic itself.
- **Delete topic** — remove the topic and all its records.

Both Truncate and Delete ask you to confirm before doing anything.

## How to browse Kafka messages in Daitics DTX Portal {#how-to-browse-kafka-messages-in-daitics-dtx-portal}

To browse Kafka messages in Daitics DTX Portal, open a topic and click **Browse messages**. The browser lets you:

- **Filter by partition** — pick one or all partitions.
- **Pick a starting offset** — earliest (from the beginning) or latest (only new records).
- **Set a limit** — between 10 and 500 records per page.
- **Filter by key** — show only records with a matching key.
- **Expand a row** — see the full value as JSON if it is JSON, or as plain text otherwise.

For step-by-step instructions, see [Browse Kafka messages](../how-to/browse-kafka-messages.md).

## Limits and things to know about Kafka in the portal {#limits-and-things-to-know-about-kafka-in-the-portal}

A few things to keep in mind when using the Kafka pages in Daitics DTX Portal:

- The portal shows up to 500 messages per page in the message browser. To see more, page through results.
- Truncating or deleting a topic cannot be undone. Confirmation dialogs appear before either action.
- The portal validates a few topic settings on creation: partitions must be between 1 and 1000, and replication factor must be at least 1.
- If a topic name already exists, the portal returns an error rather than overwriting it.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common Kafka tasks in Daitics DTX Portal:

- [Create a Kafka topic](../how-to/create-a-kafka-topic.md)
- [Browse Kafka messages](../how-to/browse-kafka-messages.md)
- [Delete or truncate a Kafka topic](../how-to/delete-or-truncate-a-kafka-topic.md)
