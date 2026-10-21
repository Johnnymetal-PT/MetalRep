from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MmRgpdConsent(models.Model):
    _name = "mm.rgpd.consent"
    _description = "MMConnect RGPD Consent"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    state = fields.Selection([("granted", "Granted"), ("revoked", "Revoked")], default="granted", required=True, tracking=True)
    note = fields.Text()


class MmRgpdRequest(models.Model):
    _name = "mm.rgpd.request"
    _description = "MMConnect RGPD Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    request_type = fields.Selection(
        [("access", "Access"), ("rectification", "Rectification"), ("erasure", "Erasure"), ("portability", "Portability")],
        required=True,
        tracking=True,
    )
    request_date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("done", "Done"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.rgpd.request") or "New"
        return super().create(vals_list)

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class MmRgpdRetentionRule(models.Model):
    _name = "mm.rgpd.retention.rule"
    _description = "MMConnect RGPD Retention Rule"
    _order = "name"

    name = fields.Char(required=True)
    model_name = fields.Char(required=True)
    retention_days = fields.Integer(required=True)
    active = fields.Boolean(default=True)
    note = fields.Text()


class MmRgpdAuditLog(models.Model):
    _name = "mm.rgpd.audit.log"
    _description = "MMConnect RGPD Audit Log"
    _order = "event_datetime desc, id desc"

    event_datetime = fields.Datetime(required=True, default=fields.Datetime.now)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    model_name = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    event_type = fields.Selection([("read", "Read"), ("write", "Write"), ("export", "Export")], required=True)
    note = fields.Text()


class MmImportProfile(models.Model):
    _name = "mm.import.profile"
    _description = "MMConnect Import Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    source_type = fields.Selection([("file", "File"), ("database", "Database"), ("api", "API")], default="file", required=True)
    active = fields.Boolean(default=True)
    note = fields.Text()


class MmImportJob(models.Model):
    _name = "mm.import.job"
    _description = "MMConnect Import Job"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    profile_id = fields.Many2one("mm.import.profile", required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("running", "Running"), ("done", "Done"), ("failed", "Failed")],
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many("mm.import.job.line", "job_id")
    error_ids = fields.One2many("mm.import.error", "job_id")
    started_at = fields.Datetime()
    finished_at = fields.Datetime()
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.import.job") or "New"
        return super().create(vals_list)

    def action_start(self):
        self.write({"state": "running", "started_at": fields.Datetime.now()})

    def action_done(self):
        self.write({"state": "done", "finished_at": fields.Datetime.now()})

    def action_fail(self):
        self.write({"state": "failed", "finished_at": fields.Datetime.now()})


class MmImportJobLine(models.Model):
    _name = "mm.import.job.line"
    _description = "MMConnect Import Job Line"
    _order = "id"

    job_id = fields.Many2one("mm.import.job", required=True, ondelete="cascade", index=True)
    model_name = fields.Char(required=True)
    external_key = fields.Char()
    status = fields.Selection([("pending", "Pending"), ("done", "Done"), ("failed", "Failed")], default="pending", required=True)
    note = fields.Text()


class MmImportError(models.Model):
    _name = "mm.import.error"
    _description = "MMConnect Import Error"
    _order = "id desc"

    job_id = fields.Many2one("mm.import.job", required=True, ondelete="cascade", index=True)
    model_name = fields.Char()
    external_key = fields.Char()
    message = fields.Text(required=True)


class MmObra(models.Model):
    _name = "mm.obra"
    _description = "MMConnect Obra"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    cost_center_id = fields.Many2one("mm.hr.cost.center")
    location_id = fields.Many2one("mm.hr.location")
    note = fields.Text()

    _sql_constraints = [
        ("mm_obra_code_uniq", "unique(code)", "The obra code must be unique."),
    ]


class MmTaskLocation(models.Model):
    _name = "mm.task.location"
    _description = "MMConnect Task Location"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    location_id = fields.Many2one("mm.hr.location")
    latitude = fields.Float()
    longitude = fields.Float()
    active = fields.Boolean(default=True)


class MmTaskRoute(models.Model):
    _name = "mm.task.route"
    _description = "MMConnect Task Route"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    task_location_ids = fields.Many2many("mm.task.location", string="Task Locations")
    active = fields.Boolean(default=True)


class MmTask(models.Model):
    _name = "mm.task"
    _description = "MMConnect Task"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_start desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    route_id = fields.Many2one("mm.task.route", tracking=True)
    location_id = fields.Many2one("mm.task.location", tracking=True)
    scheduled_start = fields.Datetime(required=True, tracking=True)
    scheduled_end = fields.Datetime(required=True, tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("in_progress", "In Progress"), ("done", "Done"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()

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
                vals["name"] = sequence.next_by_code("mm.task") or "New"
        return super().create(vals_list)

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class MmTaskGpsEvent(models.Model):
    _name = "mm.task.gps.event"
    _description = "MMConnect Task GPS Event"
    _order = "event_datetime desc, id desc"

    task_id = fields.Many2one("mm.task", required=True, ondelete="cascade", index=True)
    employee_id = fields.Many2one("hr.employee", required=True, index=True)
    event_datetime = fields.Datetime(required=True, default=fields.Datetime.now)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    note = fields.Text()


class MmAgroCampaign(models.Model):
    _name = "mm.agro.campaign"
    _description = "MMConnect Agro Campaign"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    date_start = fields.Date()
    date_end = fields.Date()
    active = fields.Boolean(default=True)
    note = fields.Text()


class MmAgroProject(models.Model):
    _name = "mm.agro.project"
    _description = "MMConnect Agro Project"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    campaign_id = fields.Many2one("mm.agro.campaign")
    active = fields.Boolean(default=True)
    note = fields.Text()


class MmAgroSubproject(models.Model):
    _name = "mm.agro.subproject"
    _description = "MMConnect Agro Subproject"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    project_id = fields.Many2one("mm.agro.project", required=True)
    active = fields.Boolean(default=True)
    note = fields.Text()


class MmWasteContainer(models.Model):
    _name = "mm.waste.container"
    _description = "MMConnect Waste Container"
    _order = "code, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    location_id = fields.Many2one("mm.hr.location")
    active = fields.Boolean(default=True)
    note = fields.Text()

    _sql_constraints = [
        ("mm_waste_container_code_uniq", "unique(code)", "The waste container code must be unique."),
    ]


class MmWasteRoute(models.Model):
    _name = "mm.waste.route"
    _description = "MMConnect Waste Route"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    container_ids = fields.Many2many("mm.waste.container", string="Containers")
    active = fields.Boolean(default=True)
    note = fields.Text()
