---
id: how-to/create-a-cache-key
title: Create a cache key in Daitics DTX Portal
category: how-to
summary: To create a cache key, open Infrastructure → Cache, click New Key, then fill in the name, data type, value, and an optional time-to-live in seconds.
tags: [cache, key, create, ttl, dragonfly]
aliases:
  - new cache key
  - add cache key
  - create cache entry
  - cache new key
  - dragonfly key
last_updated: 2026-05-02
version: 1
---

# Create a cache key in Daitics DTX Portal

## What this does {#what-this-does}

Creating a cache key in Daitics DTX Portal adds a new entry to the distributed cache. You pick the data type (string, hash, list, set, or sorted set), provide the value, and optionally set a time-to-live in seconds. The key becomes immediately available for any service or pipeline that reads from the cache.

## When you would create a cache key {#when-you-would-create-a-cache-key}

You would create a cache key in Daitics DTX Portal when you need to:

- Set up a value for a pipeline to read during testing.
- Add a feature flag or configuration value the cache exposes to other services.
- Verify the cache server is writable from the portal.

Most cache keys come from running pipelines, not manual creation. Create keys by hand only when you have a specific reason.

## Steps to create a cache key {#steps-to-create-a-cache-key}

Follow these steps to create a cache key in Daitics DTX Portal:

1. In the sidebar, click **Infrastructure → Cache**.
2. Make sure you are on the **Key Browser** tab.
3. Click **New Key** in the top-right.
4. Fill in the dialog:
   - **Name** — required. Use the namespace convention your team follows (for example, `app:feature:flag-name`).
   - **Data type** — pick String, Hash, List, Set, or Sorted set. The dialog adjusts to fit the type.
   - **Value** — for String, type the value directly. For Hash, list each field and value. For List or Set, list values one per line. For Sorted set, list value-and-score pairs.
   - **TTL** (optional) — time-to-live in seconds. Leave empty for no expiry.
5. Click **Create**.

If you are unsure which data type to pick, use **String** for a single value and **Hash** for an object with named fields.

## What to expect after creating a cache key {#what-to-expect-after-creating-a-cache-key}

After creating a cache key in Daitics DTX Portal, you should see:

- The key appears in the Key Browser, in the namespace its name implies.
- A green toast confirms the action.
- The key shows its data type icon, TTL (or "no expiry"), and size.

Click the key to open its detail panel and see or change its value.

## If something goes wrong creating a cache key {#if-something-goes-wrong-creating-a-cache-key}

If something goes wrong while creating a cache key in Daitics DTX Portal, check the most likely causes:

- **"Failed to add element"** — the cache rejected the value. Check the toast's details. Common causes are an invalid value for the chosen data type (for example, non-numeric scores in a Sorted set).
- **The key does not appear after create** — refresh the Key Browser. If the key still does not show up, switch the data type filter — the browser hides keys whose type is not currently selected.
- **The cache shows as disconnected on the Dashboard tab** — the Key Browser cannot create keys when the cache is unreachable. Ask your administrator.
- **TTL behaves unexpectedly** — TTL is in seconds. A TTL of `60` expires after one minute, not one hour.

For more help, see [Troubleshooting](../troubleshooting.md).
