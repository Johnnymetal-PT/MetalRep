from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMMConnectSecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.group_employee = self.env.ref("mmconnect.group_mmconnect_employee")
        self.group_manager = self.env.ref("mmconnect.group_mmconnect_manager")
        self.group_supervisor = self.env.ref("mmconnect.group_mmconnect_supervisor")

        self.supervisor_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Supervisor User",
                "login": "supervisor.mmconnect@example.com",
                "email": "supervisor.mmconnect@example.com",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [self.group_supervisor.id])],
            }
        )
        self.employee_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Employee User",
                "login": "employee.mmconnect@example.com",
                "email": "employee.mmconnect@example.com",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )
        self.other_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Other User",
                "login": "other.mmconnect@example.com",
                "email": "other.mmconnect@example.com",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )

        self.supervisor_employee = self.env["hr.employee"].create(
            {"name": "Supervisor Emp", "company_id": self.company.id, "user_id": self.supervisor_user.id}
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee Emp",
                "company_id": self.company.id,
                "user_id": self.employee_user.id,
                "parent_id": self.supervisor_employee.id,
            }
        )
        self.other_employee = self.env["hr.employee"].create(
            {"name": "Other Emp", "company_id": self.company.id, "user_id": self.other_user.id}
        )
        service_type = self.env["mm.hr.external.service.type"].create(
            {"name": "External Task", "code": "EXT", "company_id": self.company.id}
        )
        self.own_request = self.env["mm.external.service.request"].create(
            {
                "employee_id": self.employee.id,
                "supervisor_id": self.supervisor_employee.id,
                "service_type_id": service_type.id,
                "start_datetime": "2026-01-25 09:00:00",
                "end_datetime": "2026-01-25 11:00:00",
            }
        )
        self.other_request = self.env["mm.external.service.request"].create(
            {
                "employee_id": self.other_employee.id,
                "service_type_id": service_type.id,
                "start_datetime": "2026-01-25 12:00:00",
                "end_datetime": "2026-01-25 13:00:00",
            }
        )

    def test_employee_and_supervisor_record_rules(self):
        employee_visible = self.env["mm.external.service.request"].with_user(self.employee_user).search([])
        supervisor_visible = self.env["mm.external.service.request"].with_user(self.supervisor_user).search([])

        self.assertEqual(employee_visible, self.own_request)
        self.assertIn(self.own_request, supervisor_visible)
        self.assertNotIn(self.other_request, supervisor_visible)

    def test_rgpd_and_consent_flow(self):
        consent = self.env["mm.rgpd.consent"].create(
            {"employee_id": self.employee.id, "date": date(2026, 1, 26), "state": "granted"}
        )
        request = self.env["mm.rgpd.request"].create(
            {"employee_id": self.employee.id, "request_type": "access", "request_date": date(2026, 1, 26)}
        )
        request.action_submit()
        request.action_done()
        self.assertEqual(consent.state, "granted")
        self.assertEqual(request.state, "done")

    def test_manager_group_implies_hr_access(self):
        manager_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Manager User",
                "login": "manager.mmconnect@example.com",
                "email": "manager.mmconnect@example.com",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [self.group_manager.id])],
            }
        )

        self.assertTrue(manager_user.has_group("mmconnect.group_mmconnect_manager"))
        self.assertTrue(manager_user.has_group("hr.group_hr_user"))

    def test_employee_menu_action_opens_list_first(self):
        action = self.env.ref("mmconnect.action_mm_hr_employee")
        self.assertEqual(action.res_model, "hr.employee")
        self.assertEqual(action.view_mode, "list,form")
