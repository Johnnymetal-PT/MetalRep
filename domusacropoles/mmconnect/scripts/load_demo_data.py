"""Load reusable MMConnect demo data in an Odoo shell.

Usage on Odoo.sh:
    odoo-bin shell -d <db_name> < /home/odoo/src/user/mmconnect/scripts/load_demo_data.py
"""

from datetime import datetime, time, timedelta

from odoo import fields


company = env.company
today = fields.Date.to_date(fields.Date.context_today(env.user))
demo_date = today - timedelta(days=today.weekday())
demo_date_2 = demo_date + timedelta(days=1)


def ensure(model_name, domain, values):
    record = env[model_name].search(domain, limit=1)
    if record:
        return record, False
    return env[model_name].create(values), True


def ensure_user(login, name, group_xmlids):
    group_ids = [env.ref(xmlid).id for xmlid in group_xmlids]
    user = env["res.users"].search([("login", "=", login)], limit=1)
    if user:
        user.write({"groups_id": [(4, gid) for gid in group_ids]})
        return user, False
    values = {
        "name": name,
        "login": login,
        "email": login,
        "password": "MMConnect.2026!",
        "company_id": company.id,
        "company_ids": [(6, 0, [company.id])],
        "groups_id": [(6, 0, group_ids)],
    }
    user = env["res.users"].with_context(no_reset_password=True).create(values)
    return user, True


def ensure_employee(user, name, parent=None, **extra_vals):
    domain = [("user_id", "=", user.id)]
    values = {"name": name, "company_id": company.id, "user_id": user.id}
    if parent:
        values["parent_id"] = parent.id
    values.update(extra_vals)
    return ensure("hr.employee", domain, values)


def ensure_geo_points(area):
    if area.point_ids:
        return False
    env["mm.geo.area.point"].create(
        [
            {"area_id": area.id, "sequence": 10, "latitude": 38.7223, "longitude": -9.1393},
            {"area_id": area.id, "sequence": 20, "latitude": 38.7230, "longitude": -9.1378},
            {"area_id": area.id, "sequence": 30, "latitude": 38.7216, "longitude": -9.1372},
        ]
    )
    return True


created = []


def track(label, record, was_created):
    status = "created" if was_created else "existing"
    created.append((label, status, record.display_name))
    return record


manager_group = env.ref("mmconnect.group_mmconnect_manager")
if manager_group not in env.user.groups_id:
    env.user.write({"groups_id": [(4, manager_group.id)]})

entity = track(
    "HR Entity",
    *ensure(
        "mm.hr.entity",
        [("code", "=", "DEMO"), ("company_id", "=", company.id)],
        {"name": "MMConnect Demo Entity", "code": "DEMO", "company_id": company.id},
    ),
)
cost_center = track(
    "Cost Center",
    *ensure(
        "mm.hr.cost.center",
        [("code", "=", "DEMO-CC"), ("company_id", "=", company.id)],
        {
            "name": "MMConnect Demo Cost Center",
            "code": "DEMO-CC",
            "company_id": company.id,
            "entity_id": entity.id,
        },
    ),
)
location = track(
    "Location",
    *ensure(
        "mm.hr.location",
        [("code", "=", "DEMO-LOC"), ("company_id", "=", company.id)],
        {
            "name": "MMConnect Demo Location",
            "code": "DEMO-LOC",
            "company_id": company.id,
            "entity_id": entity.id,
            "cost_center_id": cost_center.id,
            "address": "Lisbon Demo Office",
        },
    ),
)
profile = track(
    "Employee Profile",
    *ensure(
        "mm.hr.employee.profile",
        [("code", "=", "DEMO-PROFILE"), ("company_id", "=", company.id)],
        {
            "name": "MMConnect Demo Profile",
            "code": "DEMO-PROFILE",
            "company_id": company.id,
        },
    ),
)
external_service_type = track(
    "External Service Type",
    *ensure(
        "mm.hr.external.service.type",
        [("code", "=", "EXT-DEMO"), ("company_id", "=", company.id)],
        {
            "name": "Client Visit",
            "code": "EXT-DEMO",
            "company_id": company.id,
            "requires_document": True,
        },
    ),
)
work_code = track(
    "Work Code",
    *ensure(
        "mm.hr.work.code",
        [("code", "=", "WORK-DEMO"), ("company_id", "=", company.id)],
        {"name": "Demo Work", "code": "WORK-DEMO", "company_id": company.id},
    ),
)
absence_code = track(
    "Absence Code",
    *ensure(
        "mm.hr.absence.code",
        [("code", "=", "ABS-DEMO"), ("company_id", "=", company.id)],
        {
            "name": "Demo Absence",
            "code": "ABS-DEMO",
            "company_id": company.id,
            "deduct_bank_hours": True,
        },
    ),
)
track(
    "Disciplinary Reason",
    *ensure(
        "mm.hr.disciplinary.reason",
        [("code", "=", "DISC-DEMO"), ("company_id", "=", company.id)],
        {"name": "Late Arrival", "code": "DISC-DEMO", "company_id": company.id},
    ),
)

supervisor_user = track(
    "Supervisor User",
    *ensure_user(
        "mm.supervisor.demo@example.com",
        "MMConnect Supervisor Demo",
        ["mmconnect.group_mmconnect_supervisor"],
    ),
)
employee_a_user = track(
    "Employee A User",
    *ensure_user(
        "mm.employee.a.demo@example.com",
        "MMConnect Employee A Demo",
        ["mmconnect.group_mmconnect_employee"],
    ),
)
employee_b_user = track(
    "Employee B User",
    *ensure_user(
        "mm.employee.b.demo@example.com",
        "MMConnect Employee B Demo",
        ["mmconnect.group_mmconnect_employee"],
    ),
)

supervisor_employee = track(
    "Supervisor Employee",
    *ensure_employee(
        supervisor_user,
        "MMConnect Supervisor",
        mm_entity_id=entity.id,
        mm_profile_id=profile.id,
        mm_cost_center_id=cost_center.id,
        mm_location_id=location.id,
    ),
)
employee_a = track(
    "Employee A",
    *ensure_employee(
        employee_a_user,
        "MMConnect Employee A",
        parent=supervisor_employee,
        mm_entity_id=entity.id,
        mm_profile_id=profile.id,
        mm_cost_center_id=cost_center.id,
        mm_location_id=location.id,
        mm_external_code="EMP-A",
        mm_card_number="100001",
    ),
)
employee_b = track(
    "Employee B",
    *ensure_employee(
        employee_b_user,
        "MMConnect Employee B",
        parent=supervisor_employee,
        mm_entity_id=entity.id,
        mm_profile_id=profile.id,
        mm_cost_center_id=cost_center.id,
        mm_location_id=location.id,
        mm_external_code="EMP-B",
        mm_card_number="100002",
    ),
)

track(
    "Employee Child",
    *ensure(
        "mm.hr.employee.child",
        [("employee_id", "=", employee_a.id), ("name", "=", "Demo Child A")],
        {"employee_id": employee_a.id, "name": "Demo Child A", "relationship": "child"},
    ),
)

project = track(
    "Project",
    *ensure(
        "project.project",
        [("name", "=", "MMConnect Demo Project")],
        {"name": "MMConnect Demo Project"},
    ),
)
brand = track(
    "Vehicle Brand",
    *ensure("fleet.vehicle.model.brand", [("name", "=", "MMConnect")], {"name": "MMConnect"}),
)
vehicle_model = track(
    "Vehicle Model",
    *ensure(
        "fleet.vehicle.model",
        [("name", "=", "Demo Van"), ("brand_id", "=", brand.id)],
        {"name": "Demo Van", "brand_id": brand.id},
    ),
)
vehicle = track(
    "Vehicle",
    *ensure(
        "fleet.vehicle",
        [("license_plate", "=", "MM-00-01")],
        {"model_id": vehicle_model.id, "license_plate": "MM-00-01"},
    ),
)

track(
    "Attendance Event In",
    *ensure(
        "mm.att.raw.event",
        [("employee_id", "=", employee_a.id), ("event_datetime", "=", fields.Datetime.to_string(datetime.combine(demo_date, time(9, 0))))],
        {
            "employee_id": employee_a.id,
            "event_datetime": fields.Datetime.to_string(datetime.combine(demo_date, time(9, 0))),
            "event_type": "check_in",
            "source": "terminal",
        },
    ),
)
track(
    "Attendance Event Out",
    *ensure(
        "mm.att.raw.event",
        [("employee_id", "=", employee_a.id), ("event_datetime", "=", fields.Datetime.to_string(datetime.combine(demo_date, time(18, 0))))],
        {
            "employee_id": employee_a.id,
            "event_datetime": fields.Datetime.to_string(datetime.combine(demo_date, time(18, 0))),
            "event_type": "check_out",
            "source": "terminal",
        },
    ),
)
track(
    "Missing Punch Event",
    *ensure(
        "mm.att.raw.event",
        [("employee_id", "=", employee_b.id), ("event_datetime", "=", fields.Datetime.to_string(datetime.combine(demo_date, time(9, 30))))],
        {
            "employee_id": employee_b.id,
            "event_datetime": fields.Datetime.to_string(datetime.combine(demo_date, time(9, 30))),
            "event_type": "check_in",
            "source": "portal",
        },
    ),
)

attendance_result = track(
    "Attendance Result",
    *ensure(
        "mm.att.result",
        [("employee_id", "=", employee_a.id), ("date", "=", demo_date)],
        {"employee_id": employee_a.id, "date": demo_date, "scheduled_hours": 8.0},
    ),
)
attendance_result.action_process()
attendance_result.action_close()

missing_result = track(
    "Attendance Result Missing",
    *ensure(
        "mm.att.result",
        [("employee_id", "=", employee_b.id), ("date", "=", demo_date)],
        {"employee_id": employee_b.id, "date": demo_date, "scheduled_hours": 8.0},
    ),
)
missing_result.action_process()

track(
    "Missing Punch Request",
    *ensure(
        "mm.att.missing.punch",
        [("employee_id", "=", employee_b.id), ("date", "=", demo_date)],
        {"employee_id": employee_b.id, "date": demo_date, "note": "Demo missing punch request"},
    ),
)

external_request = track(
    "External Service Request",
    *ensure(
        "mm.external.service.request",
        [("employee_id", "=", employee_a.id), ("start_datetime", "=", fields.Datetime.to_string(datetime.combine(demo_date_2, time(10, 0))))],
        {
            "employee_id": employee_a.id,
            "supervisor_id": supervisor_employee.id,
            "service_type_id": external_service_type.id,
            "start_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(10, 0))),
            "end_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(12, 30))),
            "cost_center_id": cost_center.id,
            "location_id": location.id,
        },
    ),
)
if external_request.state == "draft":
    external_request.action_submit()
    external_request.action_approve()

shift_template = track(
    "Shift Template",
    *ensure(
        "mm.shift.template",
        [("code", "=", "SHIFT-DEMO"), ("company_id", "=", company.id)],
        {
            "name": "Demo Day Shift",
            "code": "SHIFT-DEMO",
            "company_id": company.id,
            "start_hour": 9.0,
            "end_hour": 18.0,
            "break_hours": 1.0,
        },
    ),
)
shift_service = track(
    "Shift Service",
    *ensure(
        "mm.shift.service",
        [("code", "=", "SERVICE-DEMO"), ("company_id", "=", company.id)],
        {"name": "Demo Service", "code": "SERVICE-DEMO", "company_id": company.id},
    ),
)
shift_group = track(
    "Shift Group",
    *ensure(
        "mm.shift.group",
        [("code", "=", "GROUP-DEMO"), ("company_id", "=", company.id)],
        {"name": "Demo Team", "code": "GROUP-DEMO", "company_id": company.id},
    ),
)
shift_group.write({"employee_ids": [(4, employee_a.id), (4, employee_b.id)]})
shift_plan = track(
    "Shift Plan",
    *ensure(
        "mm.shift.plan",
        [("name", "=", "Demo Weekly Plan"), ("date_start", "=", demo_date)],
        {
            "name": "Demo Weekly Plan",
            "group_id": shift_group.id,
            "template_id": shift_template.id,
            "service_id": shift_service.id,
            "date_start": demo_date,
            "date_end": demo_date + timedelta(days=4),
            "employee_ids": [(6, 0, [employee_a.id, employee_b.id])],
        },
    ),
)
if shift_plan.state == "draft":
    shift_plan.action_publish()

sheet, sheet_created = ensure(
    "mm.time.distribution.sheet",
    [("employee_id", "=", employee_a.id), ("date", "=", demo_date)],
    {
        "employee_id": employee_a.id,
        "supervisor_id": supervisor_employee.id,
        "date": demo_date,
        "line_ids": [
            (
                0,
                0,
                {
                    "description": "Demo allocation",
                    "work_code_id": work_code.id,
                    "cost_center_id": cost_center.id,
                    "location_id": location.id,
                    "project_id": project.id,
                    "hours": 8.0,
                },
            )
        ],
    },
)
track("Time Distribution Sheet", sheet, sheet_created)
if sheet.state == "draft":
    sheet.action_submit()

visitor_company = track(
    "Visitor Company",
    *ensure("mm.visitor.company", [("name", "=", "Demo Visitor Company")], {"name": "Demo Visitor Company"}),
)
visitor = track(
    "Visitor",
    *ensure(
        "mm.visitor",
        [("name", "=", "Demo Visitor"), ("company_id", "=", visitor_company.id)],
        {"name": "Demo Visitor", "company_id": visitor_company.id, "email": "visitor@example.com"},
    ),
)
visit_type = track(
    "Visit Type",
    *ensure("mm.visit.type", [("name", "=", "Demo Visit Type")], {"name": "Demo Visit Type"}),
)
visit = track(
    "Visit",
    *ensure(
        "mm.visit",
        [("employee_id", "=", employee_a.id), ("scheduled_start", "=", fields.Datetime.to_string(datetime.combine(demo_date_2, time(14, 0))))],
        {
            "employee_id": employee_a.id,
            "visitor_id": visitor.id,
            "visit_type_id": visit_type.id,
            "scheduled_start": fields.Datetime.to_string(datetime.combine(demo_date_2, time(14, 0))),
            "scheduled_end": fields.Datetime.to_string(datetime.combine(demo_date_2, time(15, 0))),
            "location_id": location.id,
        },
    ),
)
if visit.state == "draft":
    visit.action_approve()

room = track(
    "Room",
    *ensure(
        "mm.room",
        [("code", "=", "ROOM-DEMO")],
        {"name": "Demo Room", "code": "ROOM-DEMO", "location_id": location.id, "capacity": 8},
    ),
)
room_booking = track(
    "Room Booking",
    *ensure(
        "mm.room.booking",
        [("name", "=", "Demo Room Booking")],
        {
            "name": "Demo Room Booking",
            "employee_id": employee_a.id,
            "room_id": room.id,
            "visit_id": visit.id,
            "start_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(14, 0))),
            "end_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(15, 0))),
        },
    ),
)
if room_booking.state == "draft":
    room_booking.action_confirm()

expense_code = track(
    "Expense Code",
    *ensure(
        "mm.expense.code",
        [("code", "=", "EXP-DEMO"), ("company_id", "=", company.id)],
        {"name": "Mileage", "code": "EXP-DEMO", "company_id": company.id},
    ),
)
per_diem_rule = track(
    "Per Diem Rule",
    *ensure(
        "mm.per.diem.rule",
        [("name", "=", "Demo Daily Allowance")],
        {
            "name": "Demo Daily Allowance",
            "code": "PER-DEMO",
            "amount": 35.0,
            "currency_id": company.currency_id.id,
            "company_id": company.id,
        },
    ),
)
track(
    "Per Diem Entry",
    *ensure(
        "mm.per.diem.entry",
        [("employee_id", "=", employee_a.id), ("date", "=", demo_date_2)],
        {
            "employee_id": employee_a.id,
            "rule_id": per_diem_rule.id,
            "date": demo_date_2,
            "amount": 35.0,
            "currency_id": company.currency_id.id,
        },
    ),
)

vehicle_booking = track(
    "Vehicle Booking",
    *ensure(
        "mm.vehicle.booking",
        [("name", "=", "Demo Vehicle Booking")],
        {
            "name": "Demo Vehicle Booking",
            "employee_id": employee_a.id,
            "vehicle_id": vehicle.id,
            "destination": "Client Site",
            "start_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(8, 30))),
            "end_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(12, 30))),
        },
    ),
)
if vehicle_booking.state == "draft":
    vehicle_booking.action_confirm()

device_profile = track(
    "Device Profile",
    *ensure(
        "mm.device.profile",
        [("code", "=", "DEVICE-DEMO")],
        {"name": "Demo Terminal Profile", "code": "DEVICE-DEMO", "protocol": "rest"},
    ),
)
device = track(
    "Device",
    *ensure(
        "mm.device",
        [("code", "=", "TERM-DEMO"), ("company_id", "=", company.id)],
        {
            "name": "Demo Terminal",
            "code": "TERM-DEMO",
            "profile_id": device_profile.id,
            "location_id": location.id,
            "company_id": company.id,
            "host": "10.0.0.10",
            "port": 4370,
            "serial_number": "DEMO-TERM-001",
            "employee_ids": [(6, 0, [employee_a.id, employee_b.id])],
        },
    ),
)
device_command = track(
    "Device Command",
    *ensure(
        "mm.device.command",
        [("device_id", "=", device.id), ("command_type", "=", "pull_events")],
        {"device_id": device.id, "command_type": "pull_events", "employee_ids": [(6, 0, [employee_a.id])]},
    ),
)
if device_command.state == "draft":
    device_command.action_queue()
    device_command.action_send()
    device_command.action_done()

track(
    "Biometric Template",
    *ensure(
        "mm.biometric.template",
        [("employee_id", "=", employee_a.id), ("device_id", "=", device.id), ("template_type", "=", "fingerprint")],
        {
            "employee_id": employee_a.id,
            "device_id": device.id,
            "template_type": "fingerprint",
            "template_data": "DEMO-FINGERPRINT-TEMPLATE",
        },
    ),
)
access_zone = track(
    "Access Zone",
    *ensure(
        "mm.access.zone",
        [("code", "=", "ZONE-DEMO")],
        {"name": "Demo Warehouse", "code": "ZONE-DEMO", "location_id": location.id},
    ),
)
track(
    "Access Door",
    *ensure(
        "mm.access.door",
        [("name", "=", "Demo Main Door"), ("zone_id", "=", access_zone.id)],
        {"name": "Demo Main Door", "zone_id": access_zone.id, "device_id": device.id},
    ),
)
track(
    "Access Permission",
    *ensure(
        "mm.access.permission",
        [("employee_id", "=", employee_a.id), ("zone_id", "=", access_zone.id)],
        {
            "employee_id": employee_a.id,
            "zone_id": access_zone.id,
            "date_start": demo_date,
            "date_end": demo_date + timedelta(days=30),
        },
    ),
)
geo_area = track(
    "Geo Area",
    *ensure(
        "mm.geo.area",
        [("code", "=", "GEO-DEMO")],
        {
            "name": "Demo Geo Area",
            "code": "GEO-DEMO",
            "location_id": location.id,
            "cost_center_id": cost_center.id,
        },
    ),
)
if ensure_geo_points(geo_area):
    created.append(("Geo Area Points", "created", geo_area.display_name))

lpr_camera = track(
    "LPR Camera",
    *ensure(
        "mm.lpr.camera",
        [("code", "=", "LPR-DEMO")],
        {"name": "Demo LPR Camera", "code": "LPR-DEMO", "device_id": device.id, "location_id": location.id},
    ),
)
track(
    "LPR Event",
    *ensure(
        "mm.lpr.event",
        [("camera_id", "=", lpr_camera.id), ("license_plate", "=", "MM-00-01")],
        {
            "camera_id": lpr_camera.id,
            "vehicle_id": vehicle.id,
            "license_plate": "MM-00-01",
            "event_datetime": fields.Datetime.to_string(datetime.combine(demo_date_2, time(8, 25))),
            "event_type": "entry",
        },
    ),
)
track(
    "LPR Vehicle Booking",
    *ensure(
        "mm.lpr.vehicle.booking",
        [("vehicle_booking_id", "=", vehicle_booking.id)],
        {
            "vehicle_booking_id": vehicle_booking.id,
            "license_plate": "MM-00-01",
            "start_datetime": vehicle_booking.start_datetime,
            "end_datetime": vehicle_booking.end_datetime,
        },
    ),
)

track(
    "RGPD Consent",
    *ensure(
        "mm.rgpd.consent",
        [("employee_id", "=", employee_a.id), ("date", "=", demo_date)],
        {"employee_id": employee_a.id, "date": demo_date, "state": "granted"},
    ),
)
rgpd_request = track(
    "RGPD Request",
    *ensure(
        "mm.rgpd.request",
        [("employee_id", "=", employee_a.id), ("request_date", "=", demo_date_2)],
        {"employee_id": employee_a.id, "request_type": "access", "request_date": demo_date_2},
    ),
)
if rgpd_request.state == "draft":
    rgpd_request.action_submit()

track(
    "RGPD Retention Rule",
    *ensure(
        "mm.rgpd.retention.rule",
        [("name", "=", "Demo Employee Retention")],
        {"name": "Demo Employee Retention", "model_name": "hr.employee", "retention_days": 3650},
    ),
)
track(
    "RGPD Audit Log",
    *ensure(
        "mm.rgpd.audit.log",
        [("model_name", "=", "hr.employee"), ("res_id", "=", employee_a.id), ("event_type", "=", "read")],
        {"model_name": "hr.employee", "res_id": employee_a.id, "event_type": "read", "note": "Demo audit log entry"},
    ),
)

import_profile = track(
    "Import Profile",
    *ensure(
        "mm.import.profile",
        [("name", "=", "Demo Import Profile")],
        {"name": "Demo Import Profile", "code": "IMPORT-DEMO", "source_type": "file"},
    ),
)
import_job, import_job_created = ensure(
    "mm.import.job",
    [("profile_id", "=", import_profile.id), ("name", "=", "Demo Import Job")],
    {
        "name": "Demo Import Job",
        "profile_id": import_profile.id,
        "line_ids": [(0, 0, {"model_name": "hr.employee", "external_key": "EMP-A", "status": "pending"})],
    },
)
track("Import Job", import_job, import_job_created)
if import_job.state == "draft":
    import_job.action_start()
    import_job.action_done()
if not import_job.error_ids:
    env["mm.import.error"].create(
        {"job_id": import_job.id, "model_name": "hr.employee", "external_key": "EMP-X", "message": "Demo import warning"}
    )

obra = track(
    "Obra",
    *ensure(
        "mm.obra",
        [("code", "=", "OBRA-DEMO")],
        {
            "name": "Demo Construction Site",
            "code": "OBRA-DEMO",
            "cost_center_id": cost_center.id,
            "location_id": location.id,
        },
    ),
)
task_location = track(
    "Task Location",
    *ensure(
        "mm.task.location",
        [("code", "=", "TASK-LOC-DEMO")],
        {"name": "Demo Task Point", "code": "TASK-LOC-DEMO", "location_id": location.id},
    ),
)
task_route = track(
    "Task Route",
    *ensure(
        "mm.task.route",
        [("code", "=", "TASK-ROUTE-DEMO")],
        {"name": "Demo Route", "code": "TASK-ROUTE-DEMO", "task_location_ids": [(6, 0, [task_location.id])]},
    ),
)
task = track(
    "Task",
    *ensure(
        "mm.task",
        [("employee_id", "=", employee_a.id), ("scheduled_start", "=", fields.Datetime.to_string(datetime.combine(demo_date_2, time(16, 0))))],
        {
            "employee_id": employee_a.id,
            "route_id": task_route.id,
            "location_id": task_location.id,
            "scheduled_start": fields.Datetime.to_string(datetime.combine(demo_date_2, time(16, 0))),
            "scheduled_end": fields.Datetime.to_string(datetime.combine(demo_date_2, time(17, 0))),
        },
    ),
)
if task.state == "draft":
    task.action_start()
track(
    "Task GPS Event",
    *ensure(
        "mm.task.gps.event",
        [("task_id", "=", task.id), ("employee_id", "=", employee_a.id)],
        {"task_id": task.id, "employee_id": employee_a.id, "latitude": 38.7223, "longitude": -9.1393},
    ),
)

agro_campaign = track(
    "Agro Campaign",
    *ensure(
        "mm.agro.campaign",
        [("name", "=", "Demo Agro Campaign")],
        {"name": "Demo Agro Campaign", "code": "AGRO-DEMO", "date_start": demo_date, "date_end": demo_date + timedelta(days=30)},
    ),
)
agro_project = track(
    "Agro Project",
    *ensure(
        "mm.agro.project",
        [("name", "=", "Demo Agro Project")],
        {"name": "Demo Agro Project", "code": "AGRO-PROJ", "campaign_id": agro_campaign.id},
    ),
)
track(
    "Agro Subproject",
    *ensure(
        "mm.agro.subproject",
        [("name", "=", "Demo Agro Subproject"), ("project_id", "=", agro_project.id)],
        {"name": "Demo Agro Subproject", "code": "AGRO-SUB", "project_id": agro_project.id},
    ),
)
waste_container = track(
    "Waste Container",
    *ensure(
        "mm.waste.container",
        [("code", "=", "WASTE-DEMO")],
        {"name": "Demo Container", "code": "WASTE-DEMO", "location_id": location.id},
    ),
)
track(
    "Waste Route",
    *ensure(
        "mm.waste.route",
        [("name", "=", "Demo Waste Route")],
        {"name": "Demo Waste Route", "code": "WASTE-ROUTE", "container_ids": [(6, 0, [waste_container.id])]},
    ),
)

track(
    "Shift Swap",
    *ensure(
        "mm.shift.swap",
        [("employee_id", "=", employee_a.id), ("requested_employee_id", "=", employee_b.id), ("request_date", "=", demo_date_2)],
        {"employee_id": employee_a.id, "requested_employee_id": employee_b.id, "request_date": demo_date_2},
    ),
)
track(
    "Shift Note",
    *ensure(
        "mm.shift.note",
        [("employee_id", "=", employee_a.id), ("date", "=", demo_date)],
        {"employee_id": employee_a.id, "plan_id": shift_plan.id, "date": demo_date, "note": "Demo note for the weekly plan"},
    ),
)
track(
    "Supervisor Dashboard Cache",
    *ensure(
        "mm.supervisor.dashboard.cache",
        [("supervisor_id", "=", supervisor_employee.id), ("snapshot_date", "=", today)],
        {
            "supervisor_id": supervisor_employee.id,
            "snapshot_date": today,
            "team_size": 2,
            "present_count": 1,
            "absent_count": 1,
            "pending_approvals": 2,
        },
    ),
)

env.cr.commit()

print("")
print("MMConnect demo data loaded successfully.")
print(f"Database company: {company.display_name}")
print("Current user was added to MMConnect Manager.")
print("")
print("Demo credentials:")
print("  Supervisor: mm.supervisor.demo@example.com / MMConnect.2026!")
print("  Employee A: mm.employee.a.demo@example.com / MMConnect.2026!")
print("  Employee B: mm.employee.b.demo@example.com / MMConnect.2026!")
print("")
print("Loaded records:")
for label, status, name in created:
    print(f"  - {label}: {status} ({name})")
