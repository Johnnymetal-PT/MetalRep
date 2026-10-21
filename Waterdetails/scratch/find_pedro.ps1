$usersJson = & .pg_framework\scripts\pg_odoo_query.ps1 -Model res.users -Domain '[["name","ilike","Pedro Coelho"]]' -Fields id,name,login
$users = $usersJson | ConvertFrom-Json
$users | ForEach-Object { Write-Output "User: $($_.id) - $($_.name) ($($_.login))" }

$empJson = & .pg_framework\scripts\pg_odoo_query.ps1 -Model hr.employee -Domain '[["name","ilike","Pedro Coelho"]]' -Fields id,name,user_id
$emps = $empJson | ConvertFrom-Json
$emps | ForEach-Object { Write-Output "Emp: $($_.id) - $($_.name) - user: $($_.user_id)" }
