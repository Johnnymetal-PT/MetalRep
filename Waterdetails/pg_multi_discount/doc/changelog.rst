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

19.0.1.0.2 (Date: 22nd May 2026)
---------------------------------
[FIX] persist the derived unit total/discount values on manually created lines even when no multi-discount is filled in.
[UPDATE] completed Portuguese translations for the multi-discount labels shown in sales, purchases and invoices.

19.0.1.0.5 (Date: 8th October 2026)
---------------------------------
[REMOVE] invoice PDF report layout override (account.report_invoice_document): the printed invoice is the standard Odoo layout again. Fields, form views and sale/purchase propagation to invoices are kept.
