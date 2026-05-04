---
id: getting-started/getting-started
title: Getting started with Daitics DTX Portal
category: getting-started
summary: Sign in to Daitics DTX Portal, learn the layout, search with a keyboard shortcut, and pick your first task as a data engineer or administrator.
tags: [getting-started, sign-in, login, navigation, search, first-time]
aliases:
  - how to sign in to daitics
  - first time using daitics dtx portal
  - log in to daitics
  - new user setup
  - where do i start
  - daitics tour
last_updated: 2026-05-02
version: 1
---

# Getting started with Daitics DTX Portal

This page walks you through signing in to Daitics DTX Portal for the first time, finding your way around, and picking a first task that matches your role.

## Sign in to Daitics DTX Portal {#sign-in-to-daitics-dtx-portal}

To sign in to Daitics DTX Portal, open the portal URL your administrator gave you. The portal sends you to your organization's sign-in screen, where you enter your username and password. If your team uses single sign-on (signing in once for all your work apps), use that option instead.

Steps:

1. Open the Daitics DTX Portal URL in your browser.
2. The portal sends you to the sign-in screen.
3. Enter your username and password, or pick your single sign-on option.
4. The portal opens at the **Home** page once you are signed in.

You cannot create your own account. If you do not have one, ask your Daitics administrator to add you.

![Daitics DTX Portal Home page after signing in](TODO/screenshots/home-after-signin.png)

## Find your way around Daitics DTX Portal {#find-your-way-around-daitics-dtx-portal}

Daitics DTX Portal has three areas you use on every page:

- **Sidebar (left)** — main navigation. Click a section name to expand it and see the pages inside. Sections include Pipelines, Schema Registry, Synthetic Data, Kafka, Cache, Access Management, and Dashboard.
- **Header (top)** — shows your current location as breadcrumbs (for example, *Home / Pipelines / My Pipeline*) and a search button.
- **Main area (centre)** — the page you are currently on.

Your name and a sign-out button sit at the bottom-left of the sidebar, inside your profile card.

![Daitics DTX Portal layout with sidebar, header, and main area labelled](TODO/screenshots/layout.png)

## Search inside Daitics DTX Portal {#search-inside-daitics-dtx-portal}

To search inside Daitics DTX Portal, press **⌘K** on a Mac or **Ctrl+K** on Windows or Linux. A search box opens in the centre of the screen. Type a few letters of a page name and press **Enter** to jump to it. Press **Esc** to close search.

Search jumps to common pages such as Home, Dashboard, Schema Registry, and Users. It does not currently search inside your own pipelines, schemas, or generators — for those, open the relevant page from the sidebar and use the search box on that page.

## Pick your first task in Daitics DTX Portal {#pick-your-first-task-in-daitics-dtx-portal}

Pick your first task in Daitics DTX Portal based on your role:

**If you are a data engineer:**

- [Create a schema](how-to/create-a-schema.md) — schemas describe the shape of your data. Pipelines and generators reuse them, so a schema is usually the first thing you create.
- [Create a pipeline](how-to/create-a-pipeline.md) — build a streaming or batch pipeline by dragging operators onto a canvas.
- [Create a data generator](how-to/create-a-data-generator.md) — produce synthetic records that match a schema, for testing pipelines without real data.

**If you are an administrator:**

- [Add a user to a role](how-to/add-a-user-to-a-role.md) — give a teammate the access they need.
- [Create a custom role](how-to/create-a-custom-role.md) — build a role with the exact permissions your team needs.
- [Reset a user password](how-to/reset-a-user-password.md) — help a teammate who is locked out.

If a sidebar section you expect is missing or greyed out, your account may not have permission for it yet. Ask your Daitics administrator to update your role.

## Sign out of Daitics DTX Portal {#sign-out-of-daitics-dtx-portal}

To sign out of Daitics DTX Portal, click the sign-out icon inside your profile card at the bottom-left of the sidebar. The portal sends you back to the sign-in screen. Closing your browser tab also ends your session, but signing out is cleaner if you share your computer.

## What to expect while using Daitics DTX Portal {#what-to-expect-while-using-daitics-dtx-portal}

While using Daitics DTX Portal, you will see a few patterns repeat across pages:

- **Loading spinners** appear while a page or list is fetching data.
- **Toast messages** in the corner of the screen confirm actions (green) or report errors (red). They disappear after a few seconds.
- **Confirmation dialogs** appear before anything that cannot be undone — for example, deleting a Kafka topic or cancelling a running pipeline.
- **Long-running actions** like compiling or deploying a pipeline show progress in a modal until they finish.

## If you cannot sign in to Daitics DTX Portal {#if-you-cannot-sign-in-to-daitics-dtx-portal}

If you cannot sign in to Daitics DTX Portal, work through these checks before contacting your administrator:

1. Confirm you are using the correct portal URL for your environment (your team may have separate URLs for development, test, and production).
2. Confirm your username and password by signing in to another tool that uses the same account.
3. Try a private or incognito browser window to rule out cached sessions.
4. If you see *"Redirecting to login..."* and the page never finishes loading, refresh the tab.

If none of these work, ask your Daitics administrator to check that your account is active and has at least one role assigned. For more help, see [Troubleshooting](troubleshooting.md).
