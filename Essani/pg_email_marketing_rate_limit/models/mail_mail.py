# -*- coding: utf-8 -*-
"""Throttle de emails de marketing antes do envio efetivo pela queue standard do Odoo."""
import logging
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    _MARKETING_LIMIT_PER_HOUR = 200
    _MARKETING_LIMIT_PER_DAY = 5000
    _MARKETING_RETRY_DELAY_MINUTES = 5

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, **kwargs):
        marketing_mails = self._filter_marketing_mails()
        regular_mails = self - marketing_mails
        results = []

        if regular_mails:
            results.append(
                super(MailMail, regular_mails)._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                    **kwargs,
                )
            )

        if marketing_mails:
            for mailing in marketing_mails.mapped("mailing_id"):
                mailing_mails = marketing_mails.filtered(lambda m: m.mailing_id == mailing)
                if not mailing_mails:
                    continue

                if not self._try_lock_mailing(mailing.id):
                    mailing_mails._postpone_marketing_queue(minutes=self._get_retry_delay_minutes())
                    _logger.info(
                        "Mailing %s locked by another worker; postponed %s mail(s).",
                        mailing.id,
                        len(mailing_mails),
                    )
                    continue

                allowed_mails, postponed_mails = mailing_mails._split_single_mailing_quota(mailing)

                if allowed_mails:
                    log_candidates = allowed_mails._prepare_marketing_log_candidates()
                    results.append(
                        super(MailMail, allowed_mails)._send(
                            auto_commit=auto_commit,
                            raise_exception=raise_exception,
                            smtp_session=smtp_session,
                            **kwargs,
                        )
                    )
                    allowed_mails._log_marketing_sends(log_candidates)

                if postponed_mails:
                    postponed_mails._reschedule_marketing_queue()
                    _logger.info(
                        "Throttled %s marketing email(s) (mailing %s).",
                        len(postponed_mails),
                        mailing.id,
                    )

        return all(results) if results else True

    # -------------------------------------------------------------------------
    # Locking / postponing helpers
    # -------------------------------------------------------------------------

    def _try_lock_mailing(self, mailing_id):
        try:
            self.env.cr.execute(
                "SELECT id FROM mailing_mailing WHERE id = %s FOR UPDATE NOWAIT",
                (mailing_id,),
            )
            return True
        except Exception:
            self.env.cr.rollback()
            return False

    def _postpone_marketing_queue(self, minutes=5):
        if not self:
            return
        now = fields.Datetime.now()
        postpone_to = now + relativedelta(minutes=minutes)
        for mail in self:
            if not mail.scheduled_date or mail.scheduled_date < postpone_to:
                mail.write({"scheduled_date": postpone_to})

    # -------------------------------------------------------------------------
    # Filtering / splitting
    # -------------------------------------------------------------------------

    def _filter_marketing_mails(self):
        return self.filtered(lambda mail: mail.mailing_id)

    def _split_by_marketing_quota(self):
        allowed_mails = self.browse()
        postponed_mails = self.browse()

        for mailing in self.mapped("mailing_id"):
            mailing_mails = self.filtered(lambda mail: mail.mailing_id == mailing)
            allowed, postponed = mailing_mails._split_single_mailing_quota(mailing)
            allowed_mails |= allowed
            postponed_mails |= postponed

        return allowed_mails, postponed_mails

    def _split_single_mailing_quota(self, mailing):
        hourly_limit = self._get_marketing_hourly_limit(mailing)
        daily_limit = self._get_marketing_daily_limit(mailing)

        if not hourly_limit and not daily_limit:
            return self, self.browse()

        hourly_remaining = (
            self._get_remaining_marketing_quota(mailing, hourly_limit)
            if hourly_limit
            else len(self)
        )
        daily_remaining = (
            self._get_remaining_marketing_daily_quota(mailing, daily_limit)
            if daily_limit
            else len(self)
        )

        remaining = min(hourly_remaining, daily_remaining)
        if remaining <= 0:
            return self.browse(), self

        allowed_mails = self[:remaining]
        postponed_mails = self - allowed_mails
        return allowed_mails, postponed_mails

    # -------------------------------------------------------------------------
    # Quota helpers (HARD GAP for hourly)
    # -------------------------------------------------------------------------

    def _get_remaining_marketing_quota(self, mailing, hourly_limit):
        """
        HARD GAP rule for hourly_limit.

        If hourly_limit is 1, this enforces:
            now >= last_sent_at + 60 minutes

        For hourly_limit > 1, we treat it as "capacity per hour slot" and still
        enforce a minimum gap based on the Nth last send inside the current hour window.
        (If you only ever use 1, this behaves exactly as required.)
        """
        if not hourly_limit:
            return len(self)

        logs_env = self.env["pg.email.marketing.log"].sudo()

        # Fetch the most recent <hourly_limit> sends
        last_logs = logs_env.search(
            [("mailing_id", "=", mailing.id)],
            order="sent_at desc",
            limit=hourly_limit,
        )

        # If fewer than hourly_limit have ever been sent, we're allowed
        if len(last_logs) < hourly_limit:
            return hourly_limit

        now = fields.Datetime.now()

        # The "oldest" among those last N defines the next allowed time
        oldest_of_last_n = last_logs[-1].sent_at
        next_allowed = oldest_of_last_n + relativedelta(hours=1)

        if now < next_allowed:
            return 0

        return hourly_limit

    def _get_remaining_marketing_daily_quota(self, mailing, daily_limit):
        now = fields.Datetime.now()
        day_ago = now - relativedelta(days=1)
        logs_env = self.env["pg.email.marketing.log"].sudo()
        domain = [("sent_at", ">=", day_ago)]
        if mailing:
            domain.append(("mailing_id", "=", mailing.id))
        sent_last_day = logs_env.search_count(domain)
        return max(daily_limit - sent_last_day, 0)

    # -------------------------------------------------------------------------
    # Slot/grid scheduling helpers
    # -------------------------------------------------------------------------

    def _ceil_to_slot(self, dt, slot_minutes, anchor_dt):
        if not dt or not anchor_dt:
            return dt

        dt = dt.replace(second=0, microsecond=0)
        anchor_dt = anchor_dt.replace(second=0, microsecond=0)

        delta = dt - anchor_dt
        delta_minutes = int(delta.total_seconds() // 60)

        if delta_minutes <= 0:
            return anchor_dt

        slots = (delta_minutes + slot_minutes - 1) // slot_minutes
        return anchor_dt + relativedelta(minutes=slots * slot_minutes)

    def _get_mailing_anchor_time(self, mailing, now):
        logs_env = self.env["pg.email.marketing.log"].sudo()
        first_log = logs_env.search([("mailing_id", "=", mailing.id)], order="sent_at asc", limit=1)
        if first_log and first_log.sent_at:
            return first_log.sent_at
        return (mailing.scheduled_date or now)

    # -------------------------------------------------------------------------
    # Rescheduling postponed emails
    # -------------------------------------------------------------------------

    def _reschedule_marketing_queue(self):
        if not self:
            return

        now = fields.Datetime.now()
        logs_env = self.env["pg.email.marketing.log"].sudo()

        for mailing in self.mapped("mailing_id"):
            mailing_mails = self.filtered(lambda mail: mail.mailing_id == mailing)
            if not mailing_mails:
                continue

            hourly_limit = self._get_marketing_hourly_limit(mailing) or 0
            daily_limit = self._get_marketing_daily_limit(mailing) or 0
            if not hourly_limit and not daily_limit:
                continue

            next_allowed = self._next_available_marketing_send_time(mailing, now)

            slot_minutes = 60 if hourly_limit else None
            anchor = self._get_mailing_anchor_time(mailing, now)

            base_time = mailing.scheduled_date or now
            if base_time < now:
                base_time = now
            if base_time < next_allowed:
                base_time = next_allowed

            if slot_minutes:
                base_time = self._ceil_to_slot(base_time, slot_minutes, anchor)

            hour_capacity = hourly_limit
            if daily_limit:
                hour_capacity = min(hour_capacity or daily_limit, daily_limit)
            hour_capacity = hour_capacity or len(mailing_mails)

            day_capacity = daily_limit or len(mailing_mails)

            sorted_mails = mailing_mails.sorted(
                key=lambda mail: (mail.scheduled_date or base_time, mail.id)
            )

            sent_since_base = logs_env.search_count(
                [("mailing_id", "=", mailing.id), ("sent_at", ">=", base_time)]
            )
            pending_since_base = self.env["mail.mail"].sudo().search_count(
                [
                    ("mailing_id", "=", mailing.id),
                    ("id", "not in", mailing_mails.ids),
                    ("scheduled_date", ">=", base_time),
                    ("state", "not in", ["cancel", "sent"]),
                ]
            )
            start_offset = sent_since_base + pending_since_base

            updates = []
            for index, mail in enumerate(sorted_mails):
                position = start_offset + index
                day_offset = position // day_capacity
                within_day_index = position % day_capacity
                hour_offset = within_day_index // hour_capacity
                scheduled_date = base_time + relativedelta(days=day_offset, hours=hour_offset)

                if slot_minutes:
                    scheduled_date = self._ceil_to_slot(scheduled_date, slot_minutes, anchor)

                updates.append((mail, scheduled_date))

            for mail, scheduled_date in updates:
                if not mail.scheduled_date or mail.scheduled_date < scheduled_date:
                    mail.write({"scheduled_date": scheduled_date})

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    def _prepare_marketing_log_candidates(self):
        return [
            {"mail_id": mail.id, "mailing_id": mail.mailing_id.id}
            for mail in self.exists()
            if mail.mailing_id
        ]

    def _log_marketing_sends(self, log_candidates=None):
        if log_candidates:
            mail_ids = [c["mail_id"] for c in log_candidates]
            fresh_mails = self.env["mail.mail"].sudo().browse(mail_ids).exists()
        else:
            fresh_mails = self.env["mail.mail"].sudo().browse(self.ids).exists()

        sent_mails = [
            {"mail_id": m.id, "mailing_id": m.mailing_id.id}
            for m in fresh_mails
            if m.state == "sent" and m.mailing_id
        ]

        if not sent_mails:
            return

        now = fields.Datetime.now()
        logs_env = self.env["pg.email.marketing.log"].sudo()

        existing_logs = logs_env.search([("mail_id", "in", [m["mail_id"] for m in sent_mails])])
        existing_mail_ids = set(existing_logs.mapped("mail_id").ids)

        to_create = [
            {"mail_id": c["mail_id"], "mailing_id": c["mailing_id"], "sent_at": now}
            for c in sent_mails
            if c["mail_id"] not in existing_mail_ids
        ]

        if to_create:
            logs_env.create(to_create)

    # -------------------------------------------------------------------------
    # Limits / retry helpers
    # -------------------------------------------------------------------------

    @api.model
    def _get_marketing_hourly_limit(self, mailing=None):
        if mailing:
            return mailing.marketing_hourly_limit
        return self._MARKETING_LIMIT_PER_HOUR

    @api.model
    def _get_marketing_daily_limit(self, mailing=None):
        if mailing:
            return mailing.marketing_daily_limit
        return self._MARKETING_LIMIT_PER_DAY

    @api.model
    def _get_retry_delay_minutes(self):
        return self._MARKETING_RETRY_DELAY_MINUTES

    def _next_available_marketing_send_time(self, mailing, now):
        """
        Compute the next time we're allowed to send again.
        Hourly uses HARD GAP logic (same as _get_remaining_marketing_quota).
        Daily stays as sliding 24h window.
        """
        deadlines = []
        logs_env = self.env["pg.email.marketing.log"].sudo()

        hourly_limit = self._get_marketing_hourly_limit(mailing)
        if hourly_limit:
            last_logs = logs_env.search(
                [("mailing_id", "=", mailing.id)],
                order="sent_at desc",
                limit=hourly_limit,
            )
            if len(last_logs) >= hourly_limit:
                oldest_of_last_n = last_logs[-1].sent_at
                deadlines.append(oldest_of_last_n + relativedelta(hours=1))

        daily_limit = self._get_marketing_daily_limit(mailing)
        if daily_limit:
            day_ago = now - relativedelta(days=1)
            day_domain = [("sent_at", ">=", day_ago)]
            if mailing:
                day_domain.append(("mailing_id", "=", mailing.id))
            day_logs = logs_env.search(day_domain, order="sent_at asc")
            if len(day_logs) >= daily_limit:
                deadlines.append(day_logs[0].sent_at + relativedelta(days=1))

        if deadlines:
            return max(deadlines)

        return now + relativedelta(minutes=self._get_retry_delay_minutes())
