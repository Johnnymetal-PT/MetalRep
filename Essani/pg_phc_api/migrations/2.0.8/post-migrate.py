"""Migration for pg_phc_api 2.0.8.

Moves the PHC "Responsavel Interno" mapping from a free-text Char on each
res.partner to a Char on res.users (pg_phc_responsavel_interno_name).

The migration runs in pure SQL to avoid triggering ORM hooks (and therefore
any PHC sync calls). It performs three steps:

1. For every internal user, look at the partners that have the legacy
   ``responsavel_interno`` Char filled and whose user.name (after stripping
   the database prefix using the old ``rsplit("|")`` rule) equals that value.
   When all matched partners agree on a single legacy value, copy it to
   ``res_users.pg_phc_responsavel_interno_name``.

2. For every partner whose legacy ``responsavel_interno`` value matches a
   unique internal user (same rule), set ``pg_responsavel_interno_user_id``
   on the partner to that user. Partners that don't resolve to exactly one
   user are left untouched and logged.

3. Refresh the (now stored related) ``responsavel_interno`` column so it
   reflects the user value — or NULL when no user is set.

Important: admins must review the result. Values copied from the legacy
Char may differ from the actual PHC name (e.g. Odoo "Carlos Santos" but PHC
"Carlos"). The post-migrate log lists every change made and every partner
that could not be resolved automatically.
"""

import logging


_logger = logging.getLogger(__name__)


def _clean_legacy_name(value):
    """Replica a regra antiga _pg_clean_responsavel_interno_name."""
    cleaned = (value or "").strip()
    if not cleaned:
        return ""
    if "|" in cleaned:
        cleaned = cleaned.rsplit("|", 1)[-1].strip()
    return cleaned


def migrate(cr, version):
    cr.execute(
        """
        SELECT u.id, p.name
          FROM res_users u
          JOIN res_partner p ON p.id = u.partner_id
         WHERE u.share = false
        """
    )
    users_by_clean_name = {}
    for user_id, user_name in cr.fetchall():
        clean = _clean_legacy_name(user_name)
        if not clean:
            continue
        users_by_clean_name.setdefault(clean, []).append(user_id)

    cr.execute(
        """
        SELECT id, name, responsavel_interno
          FROM res_partner
         WHERE responsavel_interno IS NOT NULL
           AND responsavel_interno <> ''
        """
    )
    partner_rows = cr.fetchall()

    legacy_values_by_user = {}
    partner_to_user = {}
    unresolved = []

    for partner_id, partner_name, raw_value in partner_rows:
        target = (raw_value or "").strip()
        if not target:
            continue
        matches = users_by_clean_name.get(target, [])
        if len(matches) == 1:
            user_id = matches[0]
            partner_to_user[partner_id] = user_id
            legacy_values_by_user.setdefault(user_id, set()).add(target)
        else:
            unresolved.append((partner_id, partner_name, target, len(matches)))

    user_phc_name = {}
    user_conflicts = []
    for user_id, values in legacy_values_by_user.items():
        if len(values) == 1:
            user_phc_name[user_id] = next(iter(values))[:30]
        else:
            user_conflicts.append((user_id, sorted(values)))

    for user_id, phc_name in user_phc_name.items():
        cr.execute(
            """
            UPDATE res_users
               SET pg_phc_responsavel_interno_name = %s
             WHERE id = %s
               AND (pg_phc_responsavel_interno_name IS NULL
                    OR pg_phc_responsavel_interno_name = '')
            """,
            (phc_name, user_id),
        )

    for partner_id, user_id in partner_to_user.items():
        if user_id not in user_phc_name:
            continue
        cr.execute(
            """
            UPDATE res_partner
               SET pg_responsavel_interno_user_id = %s
             WHERE id = %s
               AND pg_responsavel_interno_user_id IS NULL
            """,
            (user_id, partner_id),
        )

    cr.execute(
        """
        UPDATE res_partner p
           SET responsavel_interno = u.pg_phc_responsavel_interno_name
          FROM res_users u
         WHERE p.pg_responsavel_interno_user_id = u.id
           AND u.pg_phc_responsavel_interno_name IS NOT NULL
        """
    )
    cr.execute(
        """
        UPDATE res_partner
           SET responsavel_interno = NULL
         WHERE pg_responsavel_interno_user_id IS NULL
           AND responsavel_interno IS NOT NULL
        """
    )

    _logger.info(
        "pg_phc_api 2.0.8 migration: %s users received pg_phc_responsavel_interno_name; "
        "%s partners linked via pg_responsavel_interno_user_id; "
        "%s partners unresolved; %s users had conflicting legacy values.",
        len(user_phc_name),
        len(partner_to_user),
        len(unresolved),
        len(user_conflicts),
    )

    for user_id, phc_name in user_phc_name.items():
        _logger.info(
            "  res.users(id=%s) pg_phc_responsavel_interno_name='%s'",
            user_id, phc_name,
        )

    if user_conflicts:
        _logger.warning(
            "pg_phc_api 2.0.8 migration: users with multiple distinct legacy "
            "responsavel_interno values across partners — left blank for manual review:"
        )
        for user_id, values in user_conflicts:
            _logger.warning("  res.users(id=%s) candidates=%s", user_id, values)

    if unresolved:
        _logger.warning(
            "pg_phc_api 2.0.8 migration: partners with legacy responsavel_interno "
            "that did not map to a unique internal user — please review and re-link manually:"
        )
        for partner_id, partner_name, value, n_matches in unresolved:
            _logger.warning(
                "  res.partner(id=%s) name='%s' legacy_value='%s' user_matches=%s",
                partner_id, partner_name, value, n_matches,
            )
