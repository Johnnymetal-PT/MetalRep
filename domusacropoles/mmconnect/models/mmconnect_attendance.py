from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MmAttendanceBankAccount(models.Model):
    _name = "mm.att.bank.account"
    _description = "MMConnect Attendance Bank Account"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "employee_id"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True, tracking=True)
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)
    balance_hours = fields.Float(default=0.0, tracking=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("mm_att_bank_account_employee_uniq", "unique(employee_id)", "Each employee can only have one time bank account."),
    ]


class MmAttendanceBankEntry(models.Model):
    _name = "mm.att.bank.entry"
    _description = "MMConnect Attendance Bank Entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True, tracking=True)
    account_id = fields.Many2one("mm.att.bank.account", required=True, ondelete="cascade", index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    hours = fields.Float(required=True, tracking=True)
    entry_type = fields.Selection(
        [("credit", "Credit"), ("debit", "Debit"), ("adjustment", "Adjustment")],
        default="credit",
        required=True,
        tracking=True,
    )
    result_id = fields.Many2one("mm.att.result", ondelete="set null")
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)


class MmAttendanceLeaveBankAccount(models.Model):
    _name = "mm.att.leave.bank.account"
    _description = "MMConnect Leave Bank Account"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "employee_id"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True, tracking=True)
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)
    balance_days = fields.Float(default=0.0, tracking=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("mm_att_leave_bank_account_employee_uniq", "unique(employee_id)", "Each employee can only have one leave bank account."),
    ]


class MmAttendanceLeaveBankEntry(models.Model):
    _name = "mm.att.leave.bank.entry"
    _description = "MMConnect Leave Bank Entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True, tracking=True)
    account_id = fields.Many2one("mm.att.leave.bank.account", required=True, ondelete="cascade", index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    days = fields.Float(required=True, tracking=True)
    entry_type = fields.Selection(
        [("credit", "Credit"), ("debit", "Debit"), ("adjustment", "Adjustment")],
        default="credit",
        required=True,
        tracking=True,
    )
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)


class MmAttendanceRawEvent(models.Model):
    _name = "mm.att.raw.event"
    _description = "MMConnect Raw Attendance Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "event_datetime desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    device_id = fields.Many2one("mm.device", ondelete="set null", tracking=True)
    event_datetime = fields.Datetime(required=True, tracking=True)
    event_type = fields.Selection(
        [
            ("check_in", "Check In"),
            ("check_out", "Check Out"),
            ("access", "Access"),
            ("gps", "GPS"),
            ("manual", "Manual"),
        ],
        required=True,
        default="check_in",
        tracking=True,
    )
    source = fields.Selection(
        [("terminal", "Terminal"), ("portal", "Portal"), ("import", "Import"), ("api", "API")],
        default="terminal",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("validated", "Validated"), ("ignored", "Ignored")],
        default="draft",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.att.raw.event") or "New"
        return super().create(vals_list)

    def action_validate(self):
        self.write({"state": "validated"})

    def action_ignore(self):
        self.write({"state": "ignored"})


class MmAttendanceResult(models.Model):
    _name = "mm.att.result"
    _description = "MMConnect Attendance Result"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, employee_id"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    date = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("processed", "Processed"), ("exception", "Exception"), ("closed", "Closed")],
        default="draft",
        required=True,
        tracking=True,
    )
    scheduled_hours = fields.Float(default=8.0, tracking=True)
    worked_hours = fields.Float(default=0.0, tracking=True)
    extra_hours = fields.Float(default=0.0, tracking=True)
    missing_punch = fields.Boolean(default=False, tracking=True)
    raw_event_ids = fields.Many2many(
        "mm.att.raw.event",
        "mm_att_result_raw_event_rel",
        "result_id",
        "event_id",
        string="Raw Events",
    )
    bank_entry_id = fields.Many2one("mm.att.bank.entry", readonly=True)
    leave_bank_entry_id = fields.Many2one("mm.att.leave.bank.entry", readonly=True)
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)
    note = fields.Text()

    _sql_constraints = [
        ("mm_att_result_employee_date_uniq", "unique(employee_id, date)", "There can only be one attendance result per employee and date."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.att.result") or "New"
        return super().create(vals_list)

    def _ensure_bank_account(self):
        self.ensure_one()
        account = self.env["mm.att.bank.account"].search([("employee_id", "=", self.employee_id.id)], limit=1)
        if not account:
            account = self.env["mm.att.bank.account"].create({"employee_id": self.employee_id.id})
        return account

    def action_process(self):
        for record in self:
            start_dt = datetime.combine(fields.Date.to_date(record.date), datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            events = self.env["mm.att.raw.event"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("event_datetime", ">=", start_dt),
                    ("event_datetime", "<", end_dt),
                    ("state", "!=", "ignored"),
                ],
                order="event_datetime asc",
            )
            values = {"raw_event_ids": [(6, 0, events.ids)]}
            if not events:
                values.update(
                    {
                        "worked_hours": 0.0,
                        "extra_hours": 0.0,
                        "missing_punch": True,
                        "state": "exception",
                        "note": "No raw events found for the selected date.",
                    }
                )
                record.write(values)
                continue

            if len(events) % 2 != 0:
                values["missing_punch"] = True
                values["state"] = "exception"
                values["note"] = "Odd number of raw events detected."
            else:
                values["missing_punch"] = False
                values["state"] = "processed"

            worked_hours = 0.0
            ordered_events = events.sorted("event_datetime")
            for idx in range(0, len(ordered_events) - 1, 2):
                start_event = fields.Datetime.to_datetime(ordered_events[idx].event_datetime)
                end_event = fields.Datetime.to_datetime(ordered_events[idx + 1].event_datetime)
                worked_hours += max((end_event - start_event).total_seconds() / 3600.0, 0.0)

            values["worked_hours"] = worked_hours
            values["extra_hours"] = max(worked_hours - record.scheduled_hours, 0.0)
            record.write(values)
        return True

    def action_close(self):
        for record in self:
            if record.state not in ("processed", "exception"):
                raise ValidationError("Only processed or exception results can be closed.")
            if record.extra_hours and not record.bank_entry_id:
                account = record._ensure_bank_account()
                entry = self.env["mm.att.bank.entry"].create(
                    {
                        "employee_id": record.employee_id.id,
                        "account_id": account.id,
                        "date": record.date,
                        "hours": record.extra_hours,
                        "entry_type": "credit",
                        "result_id": record.id,
                        "note": f"Automatic credit from result {record.name}",
                    }
                )
                account.balance_hours += record.extra_hours
                record.bank_entry_id = entry.id
            record.state = "closed"

    def action_reset_to_draft(self):
        self.write({"state": "draft", "missing_punch": False, "note": False})


class MmAttendanceMissingPunch(models.Model):
    _name = "mm.att.missing.punch"
    _description = "MMConnect Missing Punch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, employee_id"

    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    date = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    _sql_constraints = [
        ("mm_att_missing_punch_employee_date_uniq", "unique(employee_id, date)", "There can only be one missing punch request per employee and date."),
    ]

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})


class MmAttendanceProcessingBatch(models.Model):
    _name = "mm.att.processing.batch"
    _description = "MMConnect Attendance Processing Batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("running", "Running"), ("done", "Done")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_end < record.date_start:
                raise ValidationError("The end date must be greater than or equal to the start date.")

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.att.processing.batch") or "New"
        return super().create(vals_list)

    def action_run(self):
        result_model = self.env["mm.att.result"]
        for batch in self:
            batch.state = "running"
            date_cursor = fields.Date.to_date(batch.date_start)
            date_end = fields.Date.to_date(batch.date_end)
            employees = batch.employee_ids or self.env["hr.employee"].search([("company_id", "=", self.env.company.id)])
            while date_cursor <= date_end:
                for employee in employees:
                    result = result_model.search([("employee_id", "=", employee.id), ("date", "=", date_cursor)], limit=1)
                    if not result:
                        result = result_model.create({"employee_id": employee.id, "date": date_cursor})
                    result.action_process()
                date_cursor += timedelta(days=1)
            batch.state = "done"


class MmExternalServiceRequest(models.Model):
    _name = "mm.external.service.request"
    _description = "MMConnect External Service Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    supervisor_id = fields.Many2one("hr.employee", tracking=True)
    service_type_id = fields.Many2one("mm.hr.external.service.type", tracking=True)
    start_datetime = fields.Datetime(required=True, tracking=True)
    end_datetime = fields.Datetime(required=True, tracking=True)
    duration_hours = fields.Float(compute="_compute_duration_hours", store=True)
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected"), ("done", "Done")],
        default="draft",
        required=True,
        tracking=True,
    )
    cost_center_id = fields.Many2one("mm.hr.cost.center", tracking=True)
    location_id = fields.Many2one("mm.hr.location", tracking=True)
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    @api.depends("start_datetime", "end_datetime")
    def _compute_duration_hours(self):
        for record in self:
            if record.start_datetime and record.end_datetime:
                start_dt = fields.Datetime.to_datetime(record.start_datetime)
                end_dt = fields.Datetime.to_datetime(record.end_datetime)
                record.duration_hours = max((end_dt - start_dt).total_seconds() / 3600.0, 0.0)
            else:
                record.duration_hours = 0.0

    @api.constrains("start_datetime", "end_datetime")
    def _check_dates(self):
        for record in self:
            if record.end_datetime <= record.start_datetime:
                raise ValidationError("The end datetime must be greater than the start datetime.")

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.external.service.request") or "New"
        return super().create(vals_list)

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})

    def action_done(self):
        self.write({"state": "done"})


class HrLeave(models.Model):
    _inherit = "hr.leave"

    mm_absence_code_id = fields.Many2one("mm.hr.absence.code")
    mm_requires_document = fields.Boolean()
    mm_support_attachment_ids = fields.Many2many("ir.attachment", string="MMConnect Attachments")
    mm_service_external_type_id = fields.Many2one("mm.hr.external.service.type")
    mm_disciplinary_reason_id = fields.Many2one("mm.hr.disciplinary.reason")
    mm_start_hour = fields.Float()
    mm_end_hour = fields.Float()
