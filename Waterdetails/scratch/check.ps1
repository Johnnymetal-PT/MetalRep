param()

$ProjectKey = "odoo-waterdetails-virgin-details-lda"
$script = ".pg_framework\scripts\pg_odoo_client_query.ps1"

Write-Host "--- Move 2187 (FT O/00066) ---"
& powershell -NoProfile -ExecutionPolicy Bypass -File $script -ProjectKey $ProjectKey -Purpose production `
  -Model account.move -Method search_read -Domain '[["id","=",2187]]' `
  -Fields id,name,amount_total,amount_residual,payment_state,invoice_date,invoice_date_due,invoice_payment_term_id,company_id

Write-Host "`n--- Move Lines of Move 2187 ---"
& powershell -NoProfile -ExecutionPolicy Bypass -File $script -ProjectKey $ProjectKey -Purpose production `
  -Model account.move.line -Method search_read -Domain '[["move_id","=",2187]]' `
  -Fields id,name,account_id,debit,credit,amount_residual,reconciled,discount_date,discount_amount_currency

Write-Host "`n--- Bank Move 2540 Lines ---"
& powershell -NoProfile -ExecutionPolicy Bypass -File $script -ProjectKey $ProjectKey -Purpose production `
  -Model account.move.line -Method search_read -Domain '[["move_id","=",2540]]' `
  -Fields id,name,account_id,debit,credit,amount_residual,reconciled

Write-Host "`n--- Partial Reconciles on Move Line 5385 ---"
& powershell -NoProfile -ExecutionPolicy Bypass -File $script -ProjectKey $ProjectKey -Purpose production `
  -Model account.partial.reconcile -Method search_read -Domain '[["debit_move_id","=",5385]]' `
  -Fields id,debit_move_id,credit_move_id,amount,debit_amount_currency,credit_amount_currency
