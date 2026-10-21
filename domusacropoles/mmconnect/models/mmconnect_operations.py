from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MmShiftTemplate(models.Model):
    _name = "mm.shift.template"
    _description = "MMConnect Shift Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    start_hour = fields.Float(required=True, tracking=True)
    end_hour = fields.Float(required=True, tracking=True)
    break_hours = fields.Float(default=0.0)
    note = fields.Text()


class MmShiftService(models.Model):
    _name = "mm.shift.service"
    _description = "MMConnect Shift Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    note = fields.Text()


class MmShiftGroup(models.Model):
    _name = "mm.shift.group"
    _description = "MMConnect Shift Group"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    note = fields.Text()


class MmShiftPlan(models.Model):
    _name = "mm.shift.plan"
    _description = "MMConnect Shift Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name"

    name = fields.Char(required=True)
    group_id = fields.Many2one("mm.shift.group", tracking=True)
    template_id = fields.Many2one("mm.shift.template", tracking=True)
    service_id = fields.Many2one("mm.shift.service", tracking=True)
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("published", "Published"), ("done", "Done")],
        default="draft",
        required=True,
        tracking=True,
    )
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    note = fields.Text()
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_end < record.date_start:
                raise ValidationError("The end date must be greater than or equal to the start date.")

    def action_publish(self):
        self.write({"state": "published"})

    def action_done(self):
        self.write({"state": "done"})


class MmShiftSwap(models.Model):
    _name = "mm.shift.swap"
    _description = "MMConnect Shift Swap"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    requested_employee_id = fields.Many2one("hr.employee", required=True, tracking=True)
    request_date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})


class MmShiftNote(models.Model):
    _name = "mm.shift.note"
    _description = "MMConnect Shift Note"
    _order = "date desc, id desc"

    date = fields.Date(required=True, default=fields.Date.context_today)
    employee_id = fields.Many2one("hr.employee", index=True)
    plan_id = fields.Many2one("mm.shift.plan", ondelete="cascade")
    note = fields.Text(required=True)


class MmSupervisorDashboardCache(models.Model):
    _name = "mm.supervisor.dashboard.cache"
    _description = "MMConnect Supervisor Dashboard Cache"
    _order = "write_date desc"

    supervisor_id = fields.Many2one("hr.employee", required=True, index=True)
    snapshot_date = fields.Date(required=True, default=fields.Date.context_today)
    team_size = fields.Integer(default=0)
    present_count = fields.Integer(default=0)
    absent_count = fields.Integer(default=0)
    pending_approvals = fields.Integer(default=0)
    note = fields.Text()


class MmTimeDistributionSheet(models.Model):
    _name = "mm.time.distribution.sheet"
    _description = "MMConnect Time Distribution Sheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, employee_id"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    supervisor_id = fields.Many2one("hr.employee", tracking=True)
    date = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many("mm.time.distribution.line", "sheet_id")
    total_hours = fields.Float(compute="_compute_total_hours", store=True)
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    @api.depends("line_ids.hours")
    def _compute_total_hours(self):
        for record in self:
            record.total_hours = sum(record.line_ids.mapped("hours"))

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.time.distribution.sheet") or "New"
        return super().create(vals_list)

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})


class MmTimeDistributionLine(models.Model):
    _name = "mm.time.distribution.line"
    _description = "MMConnect Time Distribution Line"
    _order = "id"

    sheet_id = fields.Many2one("mm.time.distribution.sheet", required=True, ondelete="cascade", index=True)
    work_code_id = fields.Many2one("mm.hr.work.code")
    absence_code_id = fields.Many2one("mm.hr.absence.code")
    cost_center_id = fields.Many2one("mm.hr.cost.center")
    location_id = fields.Many2one("mm.hr.location")
    project_id = fields.Many2one("project.project")
    description = fields.Char()
    hours = fields.Float(required=True)

    @api.constrains("hours")
    def _check_hours(self):
        for record in self:
            if record.hours <= 0:
                raise ValidationError("The allocated hours must be greater than zero.")


class MmExpenseCode(models.Model):
    _name = "mm.expense.code"
    _description = "MMConnect Expense Code"
    _order = "code, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    note = fields.Text()

    _sql_constraints = [
        ("mm_expense_code_company_uniq", "unique(code, company_id)", "The expense code must be unique per company."),
    ]


class MmPerDiemRule(models.Model):
    _name = "mm.per.diem.rule"
    _description = "MMConnect Per Diem Rule"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    active = fields.Boolean(default=True)


class MmPerDiemEntry(models.Model):
    _name = "mm.per.diem.entry"
    _description = "MMConnect Per Diem Entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    rule_id = fields.Many2one("mm.per.diem.rule", required=True, tracking=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    amount = fields.Monetary(required=True, currency_field="currency_id", tracking=True)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("paid", "Paid")],
        default="draft",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    def action_approve(self):
        self.write({"state": "approved"})

    def action_pay(self):
        self.write({"state": "paid"})


class HrExpense(models.Model):
    _inherit = "hr.expense"

    mm_expense_code_id = fields.Many2one("mm.expense.code")
    mm_cost_center_id = fields.Many2one("mm.hr.cost.center")
    mm_location_id = fields.Many2one("mm.hr.location")
    mm_per_diem_entry_id = fields.Many2one("mm.per.diem.entry")


class MmVisitorCompany(models.Model):
    _name = "mm.visitor.company"
    _description = "MMConnect Visitor Company"
    _order = "name"

    name = fields.Char(required=True)
    vat = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    active = fields.Boolean(default=True)


class MmVisitor(models.Model):
    _name = "mm.visitor"
    _description = "MMConnect Visitor"
    _order = "name"

    name = fields.Char(required=True)
    company_id = fields.Many2one("mm.visitor.company")
    email = fields.Char()
    phone = fields.Char()
    identification = fields.Char()
    active = fields.Boolean(default=True)


class MmVisitType(models.Model):
    _name = "mm.visit.type"
    _description = "MMConnect Visit Type"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)


class MmVisit(models.Model):
    _name = "mm.visit"
    _description = "MMConnect Visit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_start desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    visitor_id = fields.Many2one("mm.visitor", required=True, tracking=True)
    visit_type_id = fields.Many2one("mm.visit.type", tracking=True)
    scheduled_start = fields.Datetime(required=True, tracking=True)
    scheduled_end = fields.Datetime(required=True, tracking=True)
    actual_checkin = fields.Datetime(tracking=True)
    actual_checkout = fields.Datetime(tracking=True)
    location_id = fields.Many2one("mm.hr.location", tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("checked_in", "Checked In"), ("done", "Done"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    @api.constrains("scheduled_start", "scheduled_end")
    def _check_dates(self):
        for record in self:
            if record.scheduled_end <= record.scheduled_start:
                raise ValidationError("The scheduled end must be greater than the scheduled start.")

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.visit") or "New"
        return super().create(vals_list)

    def action_approve(self):
        self.write({"state": "approved"})

    def action_check_in(self):
        self.write({"state": "checked_in", "actual_checkin": fields.Datetime.now()})

    def action_check_out(self):
        self.write({"state": "done", "actual_checkout": fields.Datetime.now()})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class MmRoom(models.Model):
    _name = "mm.room"
    _description = "MMConnect Room"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    capacity = fields.Integer(default=1)
    location_id = fields.Many2one("mm.hr.location")
    active = fields.Boolean(default=True)


class MmRoomBooking(models.Model):
    _name = "mm.room.booking"
    _description = "MMConnect Room Booking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(required=True)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    room_id = fields.Many2one("mm.room", required=True, tracking=True)
    visit_id = fields.Many2one("mm.visit", tracking=True)
    start_datetime = fields.Datetime(required=True, tracking=True)
    end_datetime = fields.Datetime(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    @api.constrains("start_datetime", "end_datetime", "room_id", "state")
    def _check_booking_conflicts(self):
        for record in self:
            if record.end_datetime <= record.start_datetime:
                raise ValidationError("The end datetime must be greater than the start datetime.")
            if record.state == "cancelled":
                continue
            conflict = self.search(
                [
                    ("id", "!=", record.id),
                    ("room_id", "=", record.room_id.id),
                    ("state", "!=", "cancelled"),
                    ("start_datetime", "<", record.end_datetime),
                    ("end_datetime", ">", record.start_datetime),
                ],
                limit=1,
            )
            if conflict:
                raise ValidationError("There is already another active booking for the selected room in this period.")

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class MmVehicleBooking(models.Model):
    _name = "mm.vehicle.booking"
    _description = "MMConnect Vehicle Booking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(required=True)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    vehicle_id = fields.Many2one("fleet.vehicle", required=True, tracking=True)
    destination = fields.Char(required=True, tracking=True)
    start_datetime = fields.Datetime(required=True, tracking=True)
    end_datetime = fields.Datetime(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("done", "Done")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()
    company_id = fields.Many2one("res.company", related="employee_id.company_id", store=True, readonly=True)

    @api.constrains("start_datetime", "end_datetime", "vehicle_id", "state")
    def _check_booking_conflicts(self):
        for record in self:
            if record.end_datetime <= record.start_datetime:
                raise ValidationError("The end datetime must be greater than the start datetime.")
            if record.state == "cancelled":
                continue
            conflict = self.search(
                [
                    ("id", "!=", record.id),
                    ("vehicle_id", "=", record.vehicle_id.id),
                    ("state", "not in", ["cancelled", "done"]),
                    ("start_datetime", "<", record.end_datetime),
                    ("end_datetime", ">", record.start_datetime),
                ],
                limit=1,
            )
            if conflict:
                raise ValidationError("There is already another active booking for the selected vehicle in this period.")

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})
