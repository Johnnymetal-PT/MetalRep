from odoo import fields, models


class MmHrEntity(models.Model):
    _name = "mm.hr.entity"
    _description = "MMConnect HR Entity"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    legacy_id = fields.Char(index=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    note = fields.Text()
    employee_ids = fields.One2many("hr.employee", "mm_entity_id")

    _sql_constraints = [
        ("mm_hr_entity_code_company_uniq", "unique(code, company_id)", "The entity code must be unique per company."),
    ]


class MmHrCostCenter(models.Model):
    _name = "mm.hr.cost.center"
    _description = "MMConnect Cost Center"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    legacy_id = fields.Char(index=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    entity_id = fields.Many2one("mm.hr.entity", tracking=True)
    note = fields.Text()

    _sql_constraints = [
        ("mm_hr_cost_center_code_company_uniq", "unique(code, company_id)", "The cost center code must be unique per company."),
    ]


class MmHrLocation(models.Model):
    _name = "mm.hr.location"
    _description = "MMConnect Work Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    legacy_id = fields.Char(index=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    entity_id = fields.Many2one("mm.hr.entity", tracking=True)
    cost_center_id = fields.Many2one("mm.hr.cost.center", tracking=True)
    latitude = fields.Float()
    longitude = fields.Float()
    address = fields.Char()
    note = fields.Text()

    _sql_constraints = [
        ("mm_hr_location_code_company_uniq", "unique(code, company_id)", "The location code must be unique per company."),
    ]


class MmHrEmployeeProfile(models.Model):
    _name = "mm.hr.employee.profile"
    _description = "MMConnect Employee Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    legacy_id = fields.Char(index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    description = fields.Text()
    employee_ids = fields.One2many("hr.employee", "mm_profile_id")

    _sql_constraints = [
        ("mm_hr_employee_profile_code_company_uniq", "unique(code, company_id)", "The employee profile code must be unique per company."),
    ]


class MmHrEmployeeChild(models.Model):
    _name = "mm.hr.employee.child"
    _description = "MMConnect Employee Child"
    _order = "birthdate desc, name"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    birthdate = fields.Date()
    relationship = fields.Selection(
        [
            ("child", "Child"),
            ("dependent", "Dependent"),
        ],
        default="child",
        required=True,
    )
    note = fields.Text()


class MmHrDisciplinaryReason(models.Model):
    _name = "mm.hr.disciplinary.reason"
    _description = "MMConnect Disciplinary Reason"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        ("mm_hr_disciplinary_reason_code_company_uniq", "unique(code, company_id)", "The disciplinary reason code must be unique per company."),
    ]


class MmHrExternalServiceType(models.Model):
    _name = "mm.hr.external.service.type"
    _description = "MMConnect External Service Type"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    requires_document = fields.Boolean()

    _sql_constraints = [
        ("mm_hr_external_service_type_code_company_uniq", "unique(code, company_id)", "The external service type code must be unique per company."),
    ]


class MmHrWorkCode(models.Model):
    _name = "mm.hr.work.code"
    _description = "MMConnect Work Code"
    _order = "code, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    note = fields.Text()

    _sql_constraints = [
        ("mm_hr_work_code_company_uniq", "unique(code, company_id)", "The work code must be unique per company."),
    ]


class MmHrAbsenceCode(models.Model):
    _name = "mm.hr.absence.code"
    _description = "MMConnect Absence Code"
    _order = "code, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    deduct_bank_hours = fields.Boolean()
    note = fields.Text()

    _sql_constraints = [
        ("mm_hr_absence_code_company_uniq", "unique(code, company_id)", "The absence code must be unique per company."),
    ]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    mm_legacy_id = fields.Char(index=True)
    mm_entity_id = fields.Many2one("mm.hr.entity", tracking=True)
    mm_profile_id = fields.Many2one("mm.hr.employee.profile", tracking=True)
    mm_cost_center_id = fields.Many2one("mm.hr.cost.center", tracking=True)
    mm_location_id = fields.Many2one("mm.hr.location", tracking=True)
    mm_external_code = fields.Char(tracking=True)
    mm_terminal_pin = fields.Char()
    mm_card_number = fields.Char()
    mm_biometric_code = fields.Char()
    mm_mobile_app_enabled = fields.Boolean(default=True)
    mm_rgpd_consent_state = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("granted", "Granted"),
            ("revoked", "Revoked"),
        ],
        default="unknown",
        tracking=True,
    )
    mm_child_ids = fields.One2many("mm.hr.employee.child", "employee_id")
