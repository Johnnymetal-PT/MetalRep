from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MmDeviceProfile(models.Model):
    _name = "mm.device.profile"
    _description = "MMConnect Device Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    protocol = fields.Selection(
        [("rest", "REST"), ("soap", "SOAP"), ("sdk", "SDK"), ("file", "File")],
        default="rest",
        required=True,
    )
    note = fields.Text()


class MmDevice(models.Model):
    _name = "mm.device"
    _description = "MMConnect Device"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    profile_id = fields.Many2one("mm.device.profile", tracking=True)
    location_id = fields.Many2one("mm.hr.location", tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    host = fields.Char()
    port = fields.Integer()
    serial_number = fields.Char()
    state = fields.Selection(
        [("offline", "Offline"), ("online", "Online"), ("maintenance", "Maintenance")],
        default="offline",
        required=True,
        tracking=True,
    )
    note = fields.Text()
    employee_ids = fields.Many2many("hr.employee", string="Assigned Employees")


class MmDeviceCommand(models.Model):
    _name = "mm.device.command"
    _description = "MMConnect Device Command"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(required=True, default="New", copy=False)
    device_id = fields.Many2one("mm.device", required=True, index=True, tracking=True)
    command_type = fields.Selection(
        [("sync_users", "Sync Users"), ("sync_biometrics", "Sync Biometrics"), ("pull_events", "Pull Events"), ("restart", "Restart")],
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("queued", "Queued"), ("sent", "Sent"), ("done", "Done"), ("failed", "Failed")],
        default="draft",
        required=True,
        tracking=True,
    )
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    payload = fields.Text()
    response_message = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = sequence.next_by_code("mm.device.command") or "New"
        return super().create(vals_list)

    def action_queue(self):
        self.write({"state": "queued"})

    def action_send(self):
        self.write({"state": "sent"})

    def action_done(self):
        self.write({"state": "done"})

    def action_fail(self):
        self.write({"state": "failed"})


class MmBiometricTemplate(models.Model):
    _name = "mm.biometric.template"
    _description = "MMConnect Biometric Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "employee_id, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    device_id = fields.Many2one("mm.device", tracking=True)
    template_type = fields.Selection(
        [("fingerprint", "Fingerprint"), ("face", "Face"), ("palm", "Palm")],
        default="fingerprint",
        required=True,
        tracking=True,
    )
    template_data = fields.Text(required=True)
    active = fields.Boolean(default=True)


class MmAccessZone(models.Model):
    _name = "mm.access.zone"
    _description = "MMConnect Access Zone"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    location_id = fields.Many2one("mm.hr.location")


class MmAccessDoor(models.Model):
    _name = "mm.access.door"
    _description = "MMConnect Access Door"
    _order = "name"

    name = fields.Char(required=True)
    zone_id = fields.Many2one("mm.access.zone", required=True)
    device_id = fields.Many2one("mm.device")
    active = fields.Boolean(default=True)


class MmAccessPermission(models.Model):
    _name = "mm.access.permission"
    _description = "MMConnect Access Permission"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "employee_id, zone_id"

    employee_id = fields.Many2one("hr.employee", required=True, index=True, tracking=True)
    zone_id = fields.Many2one("mm.access.zone", required=True, tracking=True)
    date_start = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    date_end = fields.Date(tracking=True)
    state = fields.Selection(
        [("active", "Active"), ("blocked", "Blocked")],
        default="active",
        required=True,
        tracking=True,
    )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_end and record.date_end < record.date_start:
                raise ValidationError("The end date must be greater than or equal to the start date.")


class MmGeoArea(models.Model):
    _name = "mm.geo.area"
    _description = "MMConnect Geo Area"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    location_id = fields.Many2one("mm.hr.location")
    cost_center_id = fields.Many2one("mm.hr.cost.center")
    active = fields.Boolean(default=True)
    point_ids = fields.One2many("mm.geo.area.point", "area_id")


class MmGeoAreaPoint(models.Model):
    _name = "mm.geo.area.point"
    _description = "MMConnect Geo Area Point"
    _order = "sequence, id"

    area_id = fields.Many2one("mm.geo.area", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class MmLprCamera(models.Model):
    _name = "mm.lpr.camera"
    _description = "MMConnect LPR Camera"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    device_id = fields.Many2one("mm.device")
    location_id = fields.Many2one("mm.hr.location")
    active = fields.Boolean(default=True)


class MmLprEvent(models.Model):
    _name = "mm.lpr.event"
    _description = "MMConnect LPR Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "event_datetime desc, id desc"

    camera_id = fields.Many2one("mm.lpr.camera", required=True)
    vehicle_id = fields.Many2one("fleet.vehicle")
    license_plate = fields.Char(required=True)
    event_datetime = fields.Datetime(required=True, default=fields.Datetime.now)
    event_type = fields.Selection(
        [("entry", "Entry"), ("exit", "Exit"), ("alert", "Alert")],
        default="entry",
        required=True,
    )
    note = fields.Text()


class MmLprVehicleBooking(models.Model):
    _name = "mm.lpr.vehicle.booking"
    _description = "MMConnect LPR Vehicle Booking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    vehicle_booking_id = fields.Many2one("mm.vehicle.booking", required=True, ondelete="cascade")
    license_plate = fields.Char(required=True)
    start_datetime = fields.Datetime(required=True)
    end_datetime = fields.Datetime(required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("authorized", "Authorized"), ("done", "Done")],
        default="draft",
        required=True,
    )

    @api.constrains("start_datetime", "end_datetime")
    def _check_dates(self):
        for record in self:
            if record.end_datetime <= record.start_datetime:
                raise ValidationError("The end datetime must be greater than the start datetime.")

    def action_authorize(self):
        self.write({"state": "authorized"})

    def action_done(self):
        self.write({"state": "done"})
