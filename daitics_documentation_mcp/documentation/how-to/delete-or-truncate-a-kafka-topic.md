---
id: how-to/delete-or-truncate-a-kafka-topic
title: Delete or truncate a Kafka topic in Daitics DTX Portal
category: how-to
summary: Truncate empties a Kafka topic but keeps it in place. Delete removes the topic and all its records. Both ask for confirmation and cannot be undone.
tags: [kafka, topic, delete, truncate, cleanup]
aliases:
  - empty a kafka topic
  - clear kafka topic
  - drop kafka topic
  - reset kafka topic
  - remove kafka topic
last_updated: 2026-05-02
version: 1
---

# Delete or truncate a Kafka topic in Daitics DTX Portal

## What this does {#what-this-does}

Truncating a Kafka topic in Daitics DTX Portal deletes every record on the topic but leaves the topic itself in place. The topic stays available, but starts empty. Deleting a topic removes the topic and all its records from the cluster — pipelines and generators that referenced it will fail with "topic not found" the next time they try to use it.

Both actions are not reversible. The portal asks you to confirm before doing either.

## When you would truncate or delete a Kafka topic {#when-you-would-truncate-or-delete-a-kafka-topic}

You would truncate or delete a Kafka topic in Daitics DTX Portal when you need to:

- **Truncate** before re-running a test, so the new run starts with an empty topic.
- **Truncate** to clear out test data without recreating any pipelines that reference the topic.
- **Delete** when a topic is no longer needed and nothing depends on it.
- **Delete** to free up cluster resources.

If anything still depends on a topic, prefer truncate. Deleting a topic that pipelines depend on causes those pipelines to fail.

## Steps to truncate a Kafka topic {#steps-to-truncate-a-kafka-topic}

Follow these steps to truncate a Kafka topic in Daitics DTX Portal:

1. In the sidebar, click **Infrastructure → Kafka**.
2. Click the topic you want to truncate.
3. On the topic detail page, click **Truncate**.
4. Read the confirmation dialog. Truncate empties the topic and cannot be undone.
5. Click **Confirm truncate**.

The topic stays in the list and remains available, but its message count drops to zero.

## Steps to delete a Kafka topic {#steps-to-delete-a-kafka-topic}

Follow these steps to delete a Kafka topic in Daitics DTX Portal:

1. In the sidebar, click **Infrastructure → Kafka**.
2. Click the topic you want to delete.
3. On the topic detail page, click **Delete topic**.
4. Read the confirmation dialog carefully. Delete removes the topic and all its records and cannot be undone.
5. Type the topic name (if the dialog asks) and click **Confirm delete**.

After deletion, the topic disappears from the list. Any pipeline or generator that referenced it will fail until it is updated to use a different topic.

## What to expect after truncating or deleting {#what-to-expect-after-truncating-or-deleting}

After truncating or deleting a Kafka topic in Daitics DTX Portal, you should see:

- **After Truncate** — the topic stays in the list but its message count is 0. A green toast confirms the action.
- **After Delete** — the topic disappears from the list. A green toast confirms "Topic deleted".

Pipelines and generators that wrote to a truncated topic continue working without any change. Anything that referenced a deleted topic will report an error the next time it runs.

## If something goes wrong truncating or deleting {#if-something-goes-wrong-truncating-or-deleting}

If something goes wrong while truncating or deleting a Kafka topic in Daitics DTX Portal, check the most likely causes:

- **"Failed to delete topic"** — the cluster could not delete the topic. Check the toast's details. Common causes are permission issues or the broker being unreachable. Ask your administrator.
- **"Failed to truncate topic"** — same possible causes as deletion. Try again, then ask your administrator.
- **The topic still appears after delete** — refresh the list. If it persists, the cluster may not have finished the delete; wait a moment and refresh again.
- **Truncate or Delete is greyed out** — your account may not have the role needed for these actions. Ask your administrator.

For more help, see [Troubleshooting](../troubleshooting.md).
