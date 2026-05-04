---
id: how-to/upload-a-data-sample
title: Upload a data sample to shape a generator in Daitics DTX Portal
category: how-to
summary: Uploading a data sample to a generator in Daitics DTX Portal lets the platform analyze your real records and apply a profile so generated data looks similar to your input.
tags: [generator, synthetic-data, sample, upload, profile, sdg]
aliases:
  - upload sample data
  - generator sample
  - data sample upload
  - apply profile
  - profile upload
  - shape generator from sample
last_updated: 2026-05-02
version: 1
---

# Upload a data sample to shape a generator in Daitics DTX Portal

## What this does {#what-this-does}

Uploading a data sample to a generator in Daitics DTX Portal lets you give the platform a small file of real records (for example a CSV or a JSON file) so it can analyze them and produce synthetic data with similar value distributions. The portal calls the analyzed result a **profile**. Applying a profile updates the generator's field configuration so its output mirrors the patterns in your sample.

This is useful when you need synthetic data that "feels real" — names that look like names, prices that fall in realistic ranges, dates that cluster the way they do in production.

## When you would upload a data sample {#when-you-would-upload-a-data-sample}

You would upload a data sample to a generator in Daitics DTX Portal when you need to:

- Make synthetic data look similar to a small sample of real data without copying that data directly.
- Configure a generator quickly without setting field rules by hand.
- Reproduce realistic value distributions for load-testing.

If you only need fully random data that matches a schema's types, you do not need to upload a sample. The default generator settings are enough.

## Steps to upload a data sample and apply a profile {#steps-to-upload-a-data-sample-and-apply-a-profile}

Follow these steps to upload a data sample to a generator in Daitics DTX Portal:

1. Open the generator on the Generators list and click its name.
2. On the generator detail page, find the **Data sample** or **Profile** section (location may vary by generator type).
3. Click **Upload sample**.
4. Choose a file from your computer. Supported formats include CSV and JSON files that match the generator's schema.
5. Wait for the portal to analyze the sample. A progress indicator appears while it runs.
6. Once analysis finishes, the portal shows a **profile preview** — the value distributions and patterns it found per field.
7. Click **Apply profile** to update the generator's field configuration with these patterns.

The generator's existing settings are replaced by the profile's. To go back, you can re-edit the generator and choose different field rules.

## What to expect after uploading and applying {#what-to-expect-after-uploading-and-applying}

After uploading a data sample and applying its profile in Daitics DTX Portal, you should see:

- A green toast confirms "Profile applied".
- The generator's field rules update to reflect the profile.
- When you start the generator, the records it writes follow the value patterns from the sample (without copying the sample records themselves).

The sample file itself is not stored as part of the generator's configuration. Only the derived profile is stored.

## If something goes wrong uploading or applying {#if-something-goes-wrong-uploading-or-applying}

If something goes wrong while uploading a data sample or applying a profile in Daitics DTX Portal, check the most likely causes:

- **"Failed to upload sample"** — the file may be too large, the wrong format, or unreadable. Try a smaller file or convert to a supported format (CSV or JSON).
- **The file uploads but analysis stalls** — the file may not match the generator's schema. Make sure the columns or fields in the file match what the schema expects.
- **"Failed to apply profile"** — the profile cannot be matched to the current schema. Re-check that the schema and the sample agree on field names and types.
- **Generated data does not look like the sample** — confirm the profile was applied (the generator detail page shows the active profile). Some random variation is normal; tight matches require larger samples.

For more help, see [Troubleshooting](../troubleshooting.md).
