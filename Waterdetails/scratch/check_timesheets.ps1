$linesJson = & .pg_framework\scripts\pg_odoo_query.ps1 -Model account.analytic.line -Domain '[["project_id","=",261]]' -Fields id,name,unit_amount,task_id,user_id,employee_id,date -Limit 5
$lines = $linesJson | ConvertFrom-Json
$lines | ForEach-Object { Write-Output "Line: $($_.id) | Date: $($_.date) | Hours: $($_.unit_amount) | Task: $($_.task_id) | User: $($_.user_id) | Emp: $($_.employee_id) | Name: $($_.name)" }
