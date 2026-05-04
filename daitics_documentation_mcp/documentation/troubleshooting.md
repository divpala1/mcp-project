---
id: troubleshooting/troubleshooting
title: Troubleshooting Daitics DTX Portal
category: troubleshooting
summary: Common errors and what to do about them, grouped by area — sign-in, pipelines, schemas, synthetic data, Kafka, cache, and access management.
tags: [troubleshooting, errors, fixes, faqs, problems]
aliases:
  - help
  - faq
  - common errors
  - what does this error mean
  - daitics not working
  - portal not working
last_updated: 2026-05-02
version: 1
---

# Troubleshooting Daitics DTX Portal

This page lists common errors you may see while using Daitics DTX Portal and what to do about them. Each section covers one area of the portal. If you see an error not listed here, search for the exact text — many errors include a specific reason that points to the fix.

## You cannot sign in to Daitics DTX Portal {#you-cannot-sign-in-to-daitics-dtx-portal}

If you cannot sign in to Daitics DTX Portal, work through these checks:

- Confirm you are using the correct portal URL for your environment.
- Confirm your username and password by signing in to another tool that uses the same identity service.
- Try a private or incognito browser window to rule out cached sessions.
- If the page shows "Redirecting to login..." and never loads, refresh the tab.
- If your browser blocks redirects, allow third-party cookies for the portal and the identity service domains.
- If none of these work, ask your Daitics administrator to confirm your account is active and has at least one role assigned.

## Pages or sidebar items are missing {#pages-or-sidebar-items-are-missing}

If pages or sidebar items are missing in Daitics DTX Portal, your account may not have the role needed to see them. The portal hides anything you do not have permission to use rather than showing it greyed out.

What to do:

- Ask your administrator to confirm your roles match the work you are trying to do.
- Sign out and back in after a role change so the new permissions take effect. Or ask the administrator to terminate your sessions.
- Check that your administrator did not assign you to a deactivated account by mistake.

## A pipeline error tells you what is wrong {#a-pipeline-error-tells-you-what-is-wrong}

Pipeline errors in Daitics DTX Portal are usually about lifecycle order:

- **"Pipeline must be saved first"** — click **Save** in the designer's top bar, then try the action again.
- **"Pipeline must be compiled first"** — click **Compile** before **Deploy**.
- **"Pipeline must be deployed to pause"** — pause is only available while the pipeline is in the **Deployed** state.
- **"Pipeline must be paused to resume"** — resume is only available from the **Paused** state.
- **"No pipeline to pause"** — the pipeline is not currently deployed.
- **"Pipeline too large"** — the compiled job exceeds a runtime limit. Split the pipeline into smaller pieces.
- **"Failed to deploy pipeline"** or **"Deployment failed"** — the runtime rejected the deploy. Open the toast for details. Common causes are unreachable sources or sinks, or missing credentials.
- **"Failed to cancel pipeline"** — the runtime did not respond. Refresh and try again. If it keeps failing, ask your administrator.

For step-by-step instructions, see [Pause, resume, or cancel a pipeline](how-to/pause-resume-or-cancel-a-pipeline.md) and [Compile and deploy a pipeline](how-to/compile-and-deploy-a-pipeline.md).

## A pipeline status stays stuck on Compiling or Deploying {#a-pipeline-status-stays-stuck-on-compiling-or-deploying}

If a pipeline status stays stuck on **Compiling** or **Deploying** in Daitics DTX Portal, the runtime may be slow or unreachable. What to do:

- Wait a few minutes. Large pipelines take time to compile and deploy.
- Refresh the page. Sometimes the portal misses the status update.
- Open the **Dashboard** to see if the runtime is healthy.
- If the status does not change, ask your administrator to check the runtime.

## Schema errors and what they mean {#schema-errors-and-what-they-mean}

Common schema errors in Daitics DTX Portal:

- **"Name already exists"** — every schema name must be unique. Pick a different name.
- **"Schema is already deprecated"** — you cannot edit a deprecated schema. Make it active again or create a new one.
- **"Admin role required to deprecate schemas"** — only administrators can deprecate. Ask one to do it for you.
- **"Failed to deprecate schema"** — the registry did not accept the change. Try again, then ask your administrator.
- **"Failed to update schema"** — your edit did not save. Check your network and try again. If the issue persists, the schema may be locked by another user.
- **Editor shows red error markers** — your schema does not match the chosen format. Read the inline error and fix the syntax.

## Synthetic data errors and what they mean {#synthetic-data-errors-and-what-they-mean}

Common synthetic data errors in Daitics DTX Portal:

- **"Failed to create generator"** — the wizard could not save. Check your network and try again.
- **"Auto-mapping failed"** — the wizard could not work out a default mapping from the schema. Set the field mappings by hand.
- **"Failed to start generator"** — the destination may be unreachable. Check that your Kafka topic, database, or file path exists and is writable.
- **"Failed to upload sample"** — the sample file may be too large or in the wrong format. Try a smaller file in CSV or JSON.
- **"Failed to apply profile"** — the profile cannot be matched to the current schema. Re-check that field names and types agree.
- **"Failed to refresh pool"** — the pool's source is unreachable. Try again, then ask your administrator.
- **"Preview generation failed"** — the preview could not produce records. Confirm the field mappings are valid.

## Kafka errors and what they mean {#kafka-errors-and-what-they-mean}

Common Kafka errors in Daitics DTX Portal:

- **"Topic already exists"** — pick a different name. Topic names are unique within the cluster.
- **"Partitions must be between 1 and 1000"** — adjust the partition count.
- **"Replication factor must be at least 1"** — replication factor cannot be zero.
- **"Failed to delete topic"** — the cluster did not delete the topic. Try again, then ask your administrator.
- **"Failed to fetch messages"** — the cluster did not respond to a read request. Check the Dashboard for cluster health.

## Cache errors and what they mean {#cache-errors-and-what-they-mean}

Common cache errors in Daitics DTX Portal:

- **"Failed to add element"** — the cache rejected the value. Common causes are an invalid value for the chosen data type.
- **The Key Browser will not load** — the cache server may be disconnected. Open the Cache Dashboard tab to check.
- **A key disappeared on its own** — the cache may have evicted it under memory pressure. Treat anything you store in the cache as short-lived.

## Access management errors and what they mean {#access-management-errors-and-what-they-mean}

Common access management errors in Daitics DTX Portal:

- **"Failed to assign role"** — your network may have dropped. Try again. If it keeps failing, ask another administrator.
- **"Failed to reset password"** — the identity service did not respond. Try again, then ask your platform team.
- **"Failed to terminate session"** — the identity service did not respond. Try again.
- **The user reports they still cannot do the thing the role allows** — they may be using a session from before the change. Terminate their sessions on their profile.

## What to do if a toast disappeared before you could read it {#what-to-do-if-a-toast-disappeared-before-you-could-read-it}

If a toast notification disappeared in Daitics DTX Portal before you could read it, retry the action that triggered it. The toast appears again with the same text. Toasts are not stored anywhere — there is no toast history page.

## When to ask for help {#when-to-ask-for-help}

If none of the steps above resolve your issue in Daitics DTX Portal, contact your Daitics administrator. When you do, share:

- The exact error text (copy and paste).
- What you were trying to do.
- The page or feature you were on (the URL helps).
- The time you saw the error, in your time zone.

This information makes it much faster for an administrator to investigate.
