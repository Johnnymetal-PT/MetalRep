# AGENTS --- Parâmetro Global (Odoo)

## Mandatory Consultation of the Odoo Core

Before proposing any technical solution, Codex must: - first consult the
code in `vendor/odoo_core` - identify existing patterns in the core -
explicitly reference the relevant paths used as reference

If no clear pattern exists in the core: - explicitly state that this is
custom development - justify the proposed approach

## Core is Read-Only

The code in `vendor/odoo_core` is for reference only. It must never be
modified.

## Parâmetro Global Prefix

Everything newly created must use the `pg_` prefix, including: -
modules - models - fields - xml ids - security rules - file names when
applicable

## Response Format (Consulting)

Whenever a client request is analyzed, the response must follow this
structure: 1. Functional analysis 2. Impact (modules, data, UX,
performance) 3. Estimate (including risks) 4. Technical proposal 5.
Implementation and testing steps

## Context Update (PG_CONTEXT)

The `PG_CONTEXT.md` file is the persistent memory of the project. It
must be updated only at relevant milestones, such as: - completion of a
feature - correction of a relevant bug - change in technical decision -
before a final commit or PR - when explicitly requested

When updating, include: - summary of what changed - decisions made -
risks or pending items - next steps - Odoo core paths consulted
