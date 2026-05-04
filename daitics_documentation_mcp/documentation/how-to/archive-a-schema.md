---
id: how-to/archive-a-schema
title: Archive a schema in Daitics DTX Portal
category: how-to
summary: Archiving a schema in Daitics DTX Portal hides it from new uses and prevents new versions, while keeping existing pipelines and generators that use it running.
tags: [schema, archive, deprecate, schema-registry, cleanup]
aliases:
  - retire a schema
  - hide a schema
  - delete a schema
  - remove schema
  - deprecate schema
last_updated: 2026-05-02
version: 1
---

# Archive a schema in Daitics DTX Portal

## What this does {#what-this-does}

Archiving a schema in Daitics DTX Portal marks it as no longer in use. Once archived:

- The schema does not appear in dropdowns when creating new pipelines or generators.
- You cannot save new versions of it.
- Existing pipelines and generators that already reference the schema keep working.

Archive is the closest thing to "delete" for a schema. The Schema Registry never permanently removes schemas, because doing so would break pipelines that depend on them.

## When you would archive a schema {#when-you-would-archive-a-schema}

You would archive a schema in Daitics DTX Portal when you need to:

- Stop teammates from accidentally using a schema you no longer maintain.
- Replace a schema with a newer one and prevent further use of the old one.
- Clean up the Schema Registry list after a project ends.

If you only want to discourage use without blocking it, deprecate the schema instead. Deprecation is a softer signal.

## Steps to archive a schema {#steps-to-archive-a-schema}

Follow these steps to archive a schema in Daitics DTX Portal:

1. In the sidebar, click **Data Management → Schema Registry**.
2. Find the schema in the list.
3. Click the row's actions menu and select **Archive**.
4. Confirm the action when prompted.

You can also archive from the schema's detail page using the same Archive option.

## What to expect after archiving a schema {#what-to-expect-after-archiving-a-schema}

After archiving a schema in Daitics DTX Portal, you should see:

- The schema's status changes to **Archived**.
- The schema disappears from the default list view (set the Status filter to **Archived** to see it).
- The schema no longer appears in the schema picker when creating a pipeline or generator.
- A green toast confirms the action.

Pipelines and generators that already use the archived schema keep running. The next time someone edits one of them, they will need to choose a different schema if they want to remove the dependency.

## If something goes wrong archiving a schema {#if-something-goes-wrong-archiving-a-schema}

If something goes wrong while archiving a schema in Daitics DTX Portal, check the most likely causes:

- **The Archive action is greyed out** — the schema may already be archived, or your account may not have permission. Check the status badge first; if it is not archived, ask your administrator.
- **"Failed to archive schema"** — check your network and try again. If the problem persists, ask your administrator.
- **You wanted to delete, not archive** — archive is the cleanest option the portal offers. There is no permanent delete.

For more help, see [Troubleshooting](../troubleshooting.md).
