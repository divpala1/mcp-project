---
id: how-to/create-a-custom-role
title: Create a custom role in Daitics DTX Portal
category: how-to
summary: To create a custom role, open Access Management → Roles & Permissions, click New Role, name it, then pick permissions grouped by resource (read, write, delete, admin).
tags: [admin, access-management, role, permissions, create]
aliases:
  - new role
  - custom role
  - build a role
  - define a role
  - create permissions role
last_updated: 2026-05-02
version: 1
---

# Create a custom role in Daitics DTX Portal

## What this does {#what-this-does}

Creating a custom role in Daitics DTX Portal builds a new named permission set that you can assign to users or groups. Permissions are grouped by resource (for example, pipelines or schemas) and by action level (read, write, delete, admin). A custom role lives alongside the system roles that come with the portal — system roles are read-only, but custom ones you can edit and delete.

This task is for administrators only.

## When you would create a custom role {#when-you-would-create-a-custom-role}

You would create a custom role in Daitics DTX Portal when you need to:

- Give a team a permission set the system roles do not cover.
- Limit access tightly — for example, "read-only on schemas, no other access".
- Build a project-specific role for a temporary engagement.

If a system role already matches what you need, use that instead. Custom roles add maintenance overhead.

## Steps to create a custom role {#steps-to-create-a-custom-role}

Follow these steps to create a custom role in Daitics DTX Portal:

1. In the sidebar, click **Access Management → Roles & Permissions**.
2. Click **New Role** in the top-right.
3. Enter a **Name** that describes what the role lets people do.
4. Optionally enter a **Description** so other administrators understand its purpose.
5. In the **Permissions** section, expand each resource you want to grant access to. Tick the action levels you want for that resource:
   - **Read** — view only.
   - **Write** — create and update.
   - **Delete** — remove.
   - **Admin** — manage settings and assignments for that resource.
6. Click **Create role**.

Higher action levels often imply lower ones (admin includes write and read), but the toggles are independent — tick them explicitly to be sure.

## What to expect after creating a custom role {#what-to-expect-after-creating-a-custom-role}

After creating a custom role in Daitics DTX Portal, you should see:

- The role appears in the Roles & Permissions list. Toggle "show system roles" off to filter to custom ones only.
- A green toast confirms "Role created".
- The role becomes selectable when assigning roles to users or groups.

To change the role's permissions later, click it on the list and use **Edit**.

## If something goes wrong creating a custom role {#if-something-goes-wrong-creating-a-custom-role}

If something goes wrong while creating a custom role in Daitics DTX Portal, check the most likely causes:

- **"Name already exists"** — every role name must be unique. Pick a different name.
- **"New Role" button is missing or greyed out** — your account does not have admin privileges. Ask another administrator.
- **"Failed to create role"** — your network may have dropped. Try again. If it keeps failing, ask another administrator.
- **The role saved but you cannot assign it to anyone** — refresh the page. If the issue persists, the role may need a moment to propagate to other parts of the platform.

For more help, see [Troubleshooting](../troubleshooting.md).
