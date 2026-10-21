from datetime import date, datetime

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMMConnectAttendance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.entity = self.env["mm.hr.entity"].create({"name": "Entity A", "code": "ENT-A", "company_id": self.company.id})
        self.cost_center = self.env["mm.hr.cost.center"].create(
            {"name": "Cost Center A", "code": "CC-A", "company_id": self.company.id, "entity_id": self.entity.id}
        )
        self.location = self.env["mm.hr.location"].create(
            {
                "name": "Location A",
                "code": "LOC-A",
                "company_id": self.company.id,
                "entity_id": self.entity.id,
                "cost_center_id": self.cost_center.id,
            }
        )
        self.profile = self.env["mm.hr.employee.profile"].create(
            {"name": "Profile A", "code": "PRO-A", "company_id": self.company.id}
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee A",
                "company_id": self.company.id,
                "mm_entity_id": self.entity.id,
                "mm_cost_center_id": self.cost_center.id,
                "mm_location_id": self.location.id,
                "mm_profile_id": self.profile.id,
            }
        )

    def test_attendance_result_processing_and_bank_credit(self):
        work_date = date(2026, 1, 15)
        self.env["mm.att.raw.event"].create(
            {
                "employee_id": self.employee.id,
                "event_datetime": fields.Datetime.to_string(datetime(2026, 1, 15, 8, 0, 0)),
                "event_type": "check_in",
                "source": "terminal",
            }
        )
        self.env["mm.att.raw.event"].create(
            {
                "employee_id": self.employee.id,
                "event_datetime": fields.Datetime.to_string(datetime(2026, 1, 15, 17, 0, 0)),
                "event_type": "check_out",
                "source": "terminal",
            }
        )

        result = self.env["mm.att.result"].create(
            {"employee_id": self.employee.id, "date": work_date, "scheduled_hours": 8.0}
        )
        result.action_process()
        self.assertEqual(result.state, "processed")
        self.assertEqual(result.worked_hours, 9.0)
        self.assertEqual(result.extra_hours, 1.0)
        self.assertFalse(result.missing_punch)

        result.action_close()
        self.assertEqual(result.state, "closed")
        self.assertTrue(result.bank_entry_id)
        self.assertEqual(result.bank_entry_id.hours, 1.0)
        self.assertEqual(result.bank_entry_id.account_id.balance_hours, 1.0)

    def test_attendance_result_with_missing_punch(self):
        work_date = date(2026, 1, 16)
        self.env["mm.att.raw.event"].create(
            {
                "employee_id": self.employee.id,
                "event_datetime": fields.Datetime.to_string(datetime(2026, 1, 16, 8, 0, 0)),
                "event_type": "check_in",
                "source": "terminal",
            }
        )

        result = self.env["mm.att.result"].create({"employee_id": self.employee.id, "date": work_date})
        result.action_process()
        self.assertEqual(result.state, "exception")
        self.assertTrue(result.missing_punch)
