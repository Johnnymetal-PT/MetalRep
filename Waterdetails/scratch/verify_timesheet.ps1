$tsJson = & .pg_framework\scripts\pg_odoo_query.ps1 -Model account.analytic.line -Domain '[["id","=",40084]]' -Fields id,name,unit_amount,task_id,project_id,user_id,employee_id,date
$ts = $tsJson | ConvertFrom-Json
$ts | ForEach-Object { Write-Output "ID: $($_.id) | Date: $($_.date) | Hours: $($_.unit_amount)h | Task: $($_.task_id[1]) (ID: $($_.task_id[0])) | User: $($_.user_id[1]) | Description: $($_.name)" }
