---
id: how-to/browse-kafka-messages
title: Browse Kafka messages in Daitics DTX Portal
category: how-to
summary: To browse Kafka messages, open the topic in Infrastructure → Kafka, click Browse messages, then filter by partition, starting offset, key, and a limit between 10 and 500.
tags: [kafka, messages, browse, debug, partitions, offsets]
aliases:
  - read kafka messages
  - inspect kafka topic
  - view kafka records
  - debug kafka
  - kafka message viewer
  - tail kafka topic
last_updated: 2026-05-02
version: 1
---

# Browse Kafka messages in Daitics DTX Portal

## What this does {#what-this-does}

Browsing Kafka messages in Daitics DTX Portal lets you read the actual records on a topic without leaving the portal. You filter by partition, set a starting offset (earliest or latest), pick a limit between 10 and 500, and optionally filter by key. Each row expands to show the full message value as JSON if it is JSON, or as plain text otherwise.

## When you would browse Kafka messages {#when-you-would-browse-kafka-messages}

You would browse Kafka messages in Daitics DTX Portal when you need to:

- Confirm a pipeline or generator is writing what you expect to a topic.
- Debug a pipeline that is producing the wrong output.
- Look at the latest few records on a topic to spot anomalies.
- Find a specific record by its key.

Browsing is read-only. You cannot edit or delete individual messages from this view.

## Steps to browse Kafka messages {#steps-to-browse-kafka-messages}

Follow these steps to browse Kafka messages in Daitics DTX Portal:

1. In the sidebar, click **Infrastructure → Kafka**.
2. Click the topic you want to inspect.
3. On the topic detail page, click **Browse messages**.
4. In the message browser, set:
   - **Partition** — pick one partition or **All**.
   - **Starting offset** — **Earliest** to read from the beginning, or **Latest** to read only new records.
   - **Limit** — between 10 and 500 records per page.
   - **Key filter** (optional) — show only records with this key.
5. Click **Load messages**.
6. Click any row to expand it and see the full value.

To page through more results, change the offset or scroll back and click **Load messages** again.

## What to expect when browsing Kafka messages {#what-to-expect-when-browsing-kafka-messages}

When you browse Kafka messages in Daitics DTX Portal, you should see:

- A table of records with offset, partition, key, timestamp, and a short preview of the value.
- Up to your chosen limit (10 to 500) of records on a single page.
- Expanded rows showing pretty-printed JSON when the record is JSON, or plain text otherwise.
- A short loading spinner each time you click **Load messages**.

If a topic has no messages, you see "No messages" instead of the table.

## If something goes wrong browsing Kafka messages {#if-something-goes-wrong-browsing-kafka-messages}

If something goes wrong while browsing Kafka messages in Daitics DTX Portal, check the most likely causes:

- **"Failed to fetch messages"** — the Kafka cluster did not respond. Check the Observability dashboard for cluster health, or ask your administrator.
- **The table is empty even though you expect messages** — set Starting offset to **Earliest** so the browser reads from the beginning.
- **You see fewer messages than the limit** — you have reached the end of the partition. Try a different partition or wait for more records.
- **A value displays as garbled text** — the record may not be JSON or plain text (for example, it might be Avro-encoded). The browser shows raw text in that case.
- **Your key filter returns nothing** — keys are matched exactly. Confirm the key spelling and case.

For more help, see [Troubleshooting](../troubleshooting.md).
