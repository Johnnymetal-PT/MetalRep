$ErrorActionPreference = 'Stop'
$queryScript = 'C:\Users\Utilizador\Desktop\Repos\Chapatim\.pg_framework\scripts\pg_odoo_query.ps1'
& $queryScript -Model 'account.analytic.line' -Method 'read' -ArgsJson '[[44041],["id","name","date","unit_amount","employee_id","user_id","project_id","task_id","account_id","company_id"]]'
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect reference timesheet.' }
& $queryScript -Model 'account.analytic.line' -Method 'search_read' -ArgsJson '[[["task_id","=",7584],["date","=","2026-10-02"]],["id","name","date","unit_amount","employee_id","user_id","project_id","task_id"]]'
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect task timesheets.' }
