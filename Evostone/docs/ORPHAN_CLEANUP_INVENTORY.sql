-- EVOSTONE staging: read-only inventory for modules absent from the repository.
-- Run this before designing an uninstall/cleanup migration. It intentionally
-- excludes studio_customization, which is installed and holds Studio metadata.
\pset pager off

WITH target(module) AS (
    VALUES ('auto_database_backup'), ('mh_licenses'), ('mh_subscription')
)
SELECT d.module, d.model, count(*) AS external_ids
FROM ir_model_data d
JOIN target t ON t.module = d.module
GROUP BY d.module, d.model
ORDER BY d.module, external_ids DESC, d.model;

WITH target(module) AS (
    VALUES ('auto_database_backup'), ('mh_licenses'), ('mh_subscription')
)
SELECT d.module, m.model AS technical_model, m.name AS model_name, m.transient
FROM ir_model_data d
JOIN target t ON t.module = d.module
JOIN ir_model m ON m.id = d.res_id
WHERE d.model = 'ir.model'
ORDER BY d.module, m.model;

WITH target(module) AS (
    VALUES ('auto_database_backup'), ('mh_licenses'), ('mh_subscription')
)
SELECT d.module, c.id AS cron_id, c.active, s.name, left(s.code, 180) AS code
FROM ir_model_data d
JOIN target t ON t.module = d.module
JOIN ir_cron c ON d.model = 'ir.cron' AND d.res_id = c.id
JOIN ir_act_server s ON s.id = c.ir_actions_server_id
ORDER BY d.module, c.id;

WITH target(module) AS (
    VALUES ('auto_database_backup'), ('mh_licenses'), ('mh_subscription')
)
SELECT m.name AS module, m.state, d.name AS dependency
FROM ir_module_module m
JOIN target t ON t.module = m.name
LEFT JOIN ir_module_module_dependency d ON d.module_id = m.id
ORDER BY m.name, d.name;
