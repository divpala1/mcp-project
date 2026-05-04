---
id: features/cache
title: Cache in Daitics DTX Portal
category: features
summary: Cache pages in Daitics DTX Portal let you browse, edit, and delete keys in the distributed cache (Dragonfly), and check the cache server's health and memory use.
tags: [cache, dragonfly, redis, keys, ttl, infrastructure]
aliases:
  - cache management
  - distributed cache
  - dragonfly browser
  - redis browser
  - key value store
  - cache keys
last_updated: 2026-05-02
version: 1
---

# Cache in Daitics DTX Portal

## What Cache pages do in Daitics DTX Portal {#what-cache-pages-do-in-daitics-dtx-portal}

The Cache pages in Daitics DTX Portal give you a web view of the distributed cache (Dragonfly, which is compatible with Redis). You can browse keys grouped by namespace, see what each key holds, change time-to-live (TTL), and add or delete keys. You can also check the cache server's health and memory usage from the dashboard tab.

The cache stores fast-access data for pipelines and other Daitics services. Treat it as short-lived storage — anything in the cache may be evicted when the cache fills up.

## When you would use Cache pages in Daitics DTX Portal {#when-you-would-use-cache-pages-in-daitics-dtx-portal}

You would use the Cache pages in Daitics DTX Portal when you need to:

- Check whether a pipeline wrote the value you expected to a cache key.
- Add a key by hand for testing.
- Change a key's TTL so it lives longer or expires sooner.
- Delete a stuck or stale key.
- Confirm the cache server is healthy and not running low on memory.

## Where to find Cache in Daitics DTX Portal {#where-to-find-cache-in-daitics-dtx-portal}

Cache pages in Daitics DTX Portal live under **Infrastructure → Cache** in the sidebar. The Cache section has two tabs:

- **Key Browser** — search and edit keys.
- **Dashboard** — server health and overall stats.

## What you can do in the Key Browser {#what-you-can-do-in-the-key-browser}

The Key Browser in Daitics DTX Portal shows every key in the cache, grouped by namespace. You can:

- **Pick a namespace** in the sidebar to filter to just those keys.
- **Filter by data type** — string, hash, list, set, or sorted set.
- **See key metadata at a glance** — type icon, time-to-live (or "no expiry"), and size.
- **Click a key** to open its detail panel, where you can read the value, rename the key, set or update the TTL, or delete it.
- **Click New Key** to add a key. You set the name, data type, value, and an optional TTL.

## What you see on the Cache Dashboard tab {#what-you-see-on-the-cache-dashboard-tab}

The Cache Dashboard tab in Daitics DTX Portal shows the health of the cache server itself:

- **Connection status** — connected or disconnected.
- **Memory usage** — how much of the cache's memory is in use.
- **Key count** — the total number of keys.
- **Eviction policy** — how the cache decides which keys to drop when full.
- **Uptime** — how long the cache server has been running.

A **Refresh** button lets you reload the stats on demand.

## What the cache key data types mean {#what-the-cache-key-data-types-mean}

Each key in the Daitics DTX Portal cache has one data type. The key browser supports five:

- **String** — a single value, like a number or a small JSON document.
- **Hash** — a set of named fields, like a small object. Use this for related values that share a key.
- **List** — an ordered collection of values. Useful for queues.
- **Set** — an unordered collection of unique values.
- **Sorted set (zset)** — a set where each value has a score, and values are kept in score order.

Pick the type that matches the shape of the data you want to store. Most pipeline-written keys are strings or hashes.

## Limits and things to know about the cache {#limits-and-things-to-know-about-the-cache}

A few things to keep in mind when using the Cache pages in Daitics DTX Portal:

- The cache evicts keys when memory is full. Anything you store should be re-creatable from a more permanent source.
- Time-to-live (TTL) is in seconds. A key with no TTL never expires on its own, but may still be evicted under memory pressure.
- Renaming or deleting a key cannot be undone from the portal. Confirmation appears before deletion.
- If the Dashboard tab shows the cache as disconnected, the Key Browser will fail to load. Ask your administrator to check the cache server.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common Cache tasks in Daitics DTX Portal:

- [Create a cache key](../how-to/create-a-cache-key.md)
