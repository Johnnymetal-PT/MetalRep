from datetime import date, datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMMConnectOperations(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.employee = self.env["hr.employee"].create({"name": "Employee Ops", "company_id": self.company.id})
        self.supervisor = self.env["hr.employee"].create({"name": "Supervisor Ops", "company_id": self.company.id})
        self.work_code = self.env["mm.hr.work.code"].create(
            {"name": "Work A", "code": "WK-A", "company_id": self.company.id}
        )
        self.cost_center = self.env["mm.hr.cost.center"].create(
            {"name": "CC Ops", "code": "CC-OPS", "company_id": self.company.id}
        )
        self.location = self.env["mm.hr.location"].create(
            {"name": "Loc Ops", "code": "LOC-OPS", "company_id": self.company.id}
        )

    def test_time_distribution_visit_and_booking_flow(self):
        sheet = self.env["mm.time.distribution.sheet"].create(
            {
                "employee_id": self.employee.id,
                "supervisor_id": self.supervisor.id,
                "date": date(2026, 1, 20),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "description": "Morning work",
                            "work_code_id": self.work_code.id,
                            "cost_center_id": self.cost_center.id,
                            "location_id": self.location.id,
                            "hours": 8.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(sheet.total_hours, 8.0)
        sheet.action_submit()
        sheet.action_approve()
        self.assertEqual(sheet.state, "approved")

        visitor_company = self.env["mm.visitor.company"].create({"name": "Visitor Company"})
        visitor = self.env["mm.visitor"].create({"name": "Visitor A", "company_id": visitor_company.id})
        visit_type = self.env["mm.visit.type"].create({"name": "External"})
        visit = self.env["mm.visit"].create(
            {
                "employee_id": self.employee.id,
                "visitor_id": visitor.id,
                "visit_type_id": visit_type.id,
                "location_id": self.location.id,
                "scheduled_start": "2026-01-20 09:00:00",
                "scheduled_end": "2026-01-20 10:00:00",
            }
        )
        visit.action_approve()
        visit.action_check_in()
        visit.action_check_out()
        self.assertEqual(visit.state, "done")

        room = self.env["mm.room"].create({"name": "Room A", "code": "RM-A", "location_id": self.location.id})
        booking = self.env["mm.room.booking"].create(
            {
                "name": "Room Booking A",
                "employee_id": self.employee.id,
                "room_id": room.id,
                "visit_id": visit.id,
                "start_datetime": "2026-01-20 09:00:00",
                "end_datetime": "2026-01-20 10:00:00",
            }
        )
        booking.action_confirm()
        self.assertEqual(booking.state, "confirmed")

        with self.assertRaises(ValidationError):
            self.env["mm.room.booking"].create(
                {
                    "name": "Room Booking Conflict",
                    "employee_id": self.employee.id,
                    "room_id": room.id,
                    "start_datetime": "2026-01-20 09:30:00",
                    "end_datetime": "2026-01-20 10:30:00",
                }
            )

    def test_vehicle_booking_task_and_import_flow(self):
        brand = self.env["fleet.vehicle.model.brand"].create({"name": "Brand X"})
        model = self.env["fleet.vehicle.model"].create({"name": "Model X", "brand_id": brand.id})
        vehicle = self.env["fleet.vehicle"].create({"model_id": model.id, "license_plate": "AA-00-BB"})
        vehicle_booking = self.env["mm.vehicle.booking"].create(
            {
                "name": "Vehicle Booking A",
                "employee_id": self.employee.id,
                "vehicle_id": vehicle.id,
                "destination": "Lisbon",
                "start_datetime": "2026-01-21 08:00:00",
                "end_datetime": "2026-01-21 12:00:00",
            }
        )
        vehicle_booking.action_confirm()
        vehicle_booking.action_done()
        self.assertEqual(vehicle_booking.state, "done")

        task_location = self.env["mm.task.location"].create({"name": "Task Point", "code": "TP-1"})
        task = self.env["mm.task"].create(
            {
                "employee_id": self.employee.id,
                "location_id": task_location.id,
                "scheduled_start": "2026-01-22 08:00:00",
                "scheduled_end": "2026-01-22 10:00:00",
            }
        )
        task.action_start()
        task.action_done()
        self.assertEqual(task.state, "done")

        profile = self.env["mm.import.profile"].create({"name": "Primavera Import", "source_type": "file"})
        job = self.env["mm.import.job"].create(
            {
                "profile_id": profile.id,
                "line_ids": [(0, 0, {"model_name": "hr.employee", "external_key": "EMP001", "status": "pending"})],
            }
        )
        job.action_start()
        job.action_done()
        self.assertEqual(job.state, "done")
        self.assertTrue(job.started_at)
        self.assertTrue(job.finished_at)
