17.0.1 ( Date : 19 September 2023 )
-----------------------------------

- Initial Release

 (Date : 02 Oct 2023)
----------------------------
- [FIX] quotation report layout problem 
- [FIX] rfq report layout problem
- [FIX] draft invoice layout problem
- [Fix] sale order and invoice problem also this problem in purchase order line fix that also.
- [FIX] the DUP field that needed to be read only.

 (Date : 04 Oct 2023)
----------------------------
- [FIX] error when you don't write multi discount correctly.
- [FIX] standard discount amount field calculation problem.

17.0.2 (Date: 14th June 2024)
---------------------------------
[FIX] error were coming while opening the sale, purchase and invoice records without giving the security groups.

17.0.3 (Date: 28th June 2024)
---------------------------------
[UPDATE] added the multi discount fields into the optional with hide/show.
0.0.4 (Date: 1st October 2026) — Parametro Global
--------------------------------------------------
[UPDATE] multi discount ativo nas encomendas de COMPRA (vista + grupo).
[FIX] vista da fatura (cliente e fornecedor): retirados os `groups` com o xmlid inexistente
      `sh_multi_discount.group_...`, que escondiam os campos da cascata a todos os utilizadores.
[FIX] vista de compra: o readonly do desconto mantém a regra standard `qty_invoiced != 0`.
[NOTE] relatório PDF de compras continua desativado (relatórios refeitos no Studio).
