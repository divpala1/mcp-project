---
id: how-to/save-a-new-schema-version
title: Save a new schema version in Daitics DTX Portal
category: how-to
summary: To save a new version of a schema, open it from Schema Registry, click Edit, change the schema, write a change note, and confirm any compatibility warnings.
tags: [schema, version, edit, update, schema-registry]
aliases:
  - update a schema
  - edit a schema
  - new schema version
  - bump schema version
  - change a schema
last_updated: 2026-05-02
version: 1
---

# Save a new schema version in Daitics DTX Portal

## What this does {#what-this-does}

Saving a new schema version in Daitics DTX Portal stores your edits as the next version of an existing schema. The previous version stays available, so any pipeline or generator using the older version keeps working. The portal also runs a compatibility check between the new and old versions and warns you if your changes are breaking.

## When you would save a new schema version {#when-you-would-save-a-new-schema-version}

You would save a new schema version in Daitics DTX Portal when you need to:

- Add a new field to a schema.
- Rename or remove a field (a breaking change).
- Change a field's type, required state, or default value.
- Reword a description without changing structure.

If you are starting a new shape from scratch, create a new schema instead — see [Create a schema](create-a-schema.md).

## Steps to save a new schema version {#steps-to-save-a-new-schema-version}

Follow these steps to save a new schema version in Daitics DTX Portal:

1. In the sidebar, click **Data Management → Schema Registry**.
2. Find the schema you want to update and click its name.
3. On the schema's detail page, click **Edit**.
4. The wizard opens to the **Basic Info** step with the current values pre-filled. Update the **Version** number to the next one (for example, `1.1.0` for a small change or `2.0.0` for a breaking change).
5. Click **Next** to reach the **Schema** step. Edit the schema definition.
6. Click **Next** to reach the **Review** step. Write a short **change note** describing what changed and why. The change note is required.
7. The portal runs a compatibility check against the previous version. If it warns of breaking changes, read the warning carefully.
8. Click **Save New Version**. To override a breaking-change warning, confirm the override when asked.

## What to expect after saving a new schema version {#what-to-expect-after-saving-a-new-schema-version}

After saving a new schema version in Daitics DTX Portal, you should see:

- The new version number appears at the top of the schema's detail page.
- The Versions tab lists the new version with its change note and timestamp.
- A green toast confirms "Schema updated".
- Existing pipelines and generators continue using whichever version they were configured with — they do not switch automatically.

To use the new version in a pipeline or generator, open that pipeline or generator and select the new version from its schema dropdown.

## If something goes wrong saving a new schema version {#if-something-goes-wrong-saving-a-new-schema-version}

If something goes wrong while saving a new schema version in Daitics DTX Portal, check the most likely causes:

- **"Change note is required"** — write a short note in the Review step before saving.
- **"Version number must be higher than the current version"** — bump the version number. The portal does not allow saving a version lower than what already exists.
- **"Schema is already deprecated"** — deprecated schemas cannot be edited. Create a new schema or ask an administrator to make it active again.
- **"Failed to update schema"** — check your network and try again. If the error mentions permissions, ask your administrator.
- **Compatibility warning you do not understand** — open the previous version on the schema detail page and compare. The warning text usually names the field that changed.

For more help, see [Troubleshooting](../troubleshooting.md).
