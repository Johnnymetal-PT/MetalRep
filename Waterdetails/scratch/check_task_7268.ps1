$taskJson = & .pg_framework\scripts\pg_odoo_query.ps1 -Model project.task -Domain '[["id","=",7268]]' -Fields id,name,project_id,user_ids,partner_id
$task = $taskJson | ConvertFrom-Json
$task | ForEach-Object { Write-Output "Task: $($_.id) - $($_.name) | Project: $($_.project_id) | Partner: $($_.partner_id)" }
