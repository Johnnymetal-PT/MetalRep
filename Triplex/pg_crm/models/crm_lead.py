# -*- coding: utf-8 -*-
"""Limpeza de orçamentos/documentos quando um lead é dado como perdido.

ATENÇÃO: este código APAGA dados reais (incl. faturas) — ver o aviso no __manifest__.py
antes de o alterar ou ativar em produção.
"""
from odoo import models, api


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def write(self, vals):
        # Arquivar o lead (active=False) é o gatilho que dispara toda a limpeza abaixo.
        if "active" in vals and not vals["active"]:
            for lead in self:
                # Find related quotations (sale.orders)
                quotations = self.env["sale.order"].search([("opportunity_id", "=", lead.id)])
                for quotation in quotations:
                    # If the quotation is confirmed (state='sale'), revert to draft
                    if quotation.state == "sale":
                        quotation.action_unlock()  # Unlock the order for changes
                        quotation.action_cancel()  # Cancel the sale order
                        quotation.state = "draft"  # Revert to draft
                        # Delete related records like invoices, pickings, MOs, POs
                        self._delete_related_records(quotation)
                    # Delete the quotation
                    quotation.unlink()
        return super(CrmLead, self).write(vals)

    def _delete_related_records(self, order):
        """Apaga/cancela os documentos gerados por um orçamento confirmado.

        Abrange faturas, entregas, ordens de fabrico e (apenas) as linhas de compra
        ligadas à venda. Cada passo é envolvido em try/except e registado em ir.logging
        para não falhar a operação toda por causa de um documento problemático.
        """
        # Faturas com origem neste orçamento.
        invoices = self.env["account.move"].search([("invoice_origin", "=", order.name)])
        for invoice in invoices:
            try:
                invoice.unlink()
                self.env["ir.logging"].create({
                    "name": "Invoice Deletion",
                    "type": "server",
                    "level": "info",
                    "message": f"Deleted invoice {invoice.name} linked to sale order {order.name}.",
                })
            except Exception as e:
                self.env["ir.logging"].create({
                    "name": "Invoice Deletion Error",
                    "type": "server",
                    "level": "error",
                    "message": f"Failed to delete invoice {invoice.name}: {str(e)}.",
                })

        # Delete related stock pickings (deliveries)
        pickings = self.env["stock.picking"].search([("origin", "=", order.name)])
        for picking in pickings:
            try:
                if picking.state != "cancel":
                    picking.action_cancel()
                picking.unlink()
            except Exception as e:
                self.env["ir.logging"].create({
                    "name": "Stock Picking Deletion Error",
                    "type": "server",
                    "level": "error",
                    "message": f"Failed to delete stock picking {picking.name}: {str(e)}.",
                })

        # Delete related manufacturing orders
        mos = self.env["mrp.production"].search([("origin", "=", order.name)])
        for mo in mos:
            try:
                if mo.state not in ["cancel", "done"]:
                    mo.action_cancel()
                mo.unlink()
            except Exception as e:
                self.env["ir.logging"].create({
                    "name": "MRP Deletion Error",
                    "type": "server",
                    "level": "error",
                    "message": f"Failed to delete MRP {mo.name}: {str(e)}.",
                })

        # Process related purchase orders
        pos = self.env["purchase.order"].search([("origin", "=", order.name)])
        for po in pos:
            try:
                # Log the state of the PO before processing
                self.env["ir.logging"].create({
                    "name": "PO State Before Processing",
                    "type": "server",
                    "level": "info",
                    "message": f"Processing PO {po.name} in state {po.state}.",
                })

                # Numa PO podem existir linhas de várias vendas; só se apagam as desta.
                related_lines = po.order_line.filtered(lambda line: line.sale_order_id == order)
                if related_lines:
                    # Log which lines are being deleted
                    for line in related_lines:
                        self.env["ir.logging"].create({
                            "name": "PO Line Deletion",
                            "type": "server",
                            "level": "info",
                            "message": f"Deleting line {line.name} from PO {po.name}.",
                        })
                    related_lines.unlink()

                # If no lines remain, cancel and delete the PO
                if not po.order_line:
                    if po.state not in ["cancel", "done"]:
                        po.button_cancel()
                    po.unlink()
                    self.env["ir.logging"].create({
                        "name": "PO Deletion",
                        "type": "server",
                        "level": "info",
                        "message": f"Deleted PO {po.name} after removing related lines.",
                    })
                else:
                    self.env["ir.logging"].create({
                        "name": "PO Lines Remaining",
                        "type": "server",
                        "level": "info",
                        "message": f"PO {po.name} has remaining lines after processing.",
                    })
            except Exception as e:
                self.env["ir.logging"].create({
                    "name": "PO Deletion Error",
                    "type": "server",
                    "level": "error",
                    "message": f"Failed to process PO {po.name}: {str(e)}.",
                })


