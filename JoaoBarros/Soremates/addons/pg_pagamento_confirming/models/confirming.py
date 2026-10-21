from odoo import models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_criar_pagamento_confirming(self):
        for move in self:
            if move.move_type != 'in_invoice':
                raise UserError("Apenas faturas de fornecedor são elegíveis para confirming.")
            if not move.x_studio_transferir_para_confirming:
                raise UserError("A opção 'Transferir para Confirming' deve estar selecionada.")
            if move.state != 'posted':
                raise UserError("A fatura deve estar publicada antes de gerar os lançamentos de diário.")

            if not move.x_studio_data_pagamento_confirming:
                raise UserError("Deve definir a 'Data Confirming' (data prevista de pagamento ao banco).")

            if move.payment_state != 'paid':
                raise UserError("A fatura ainda não foi paga. O processo de Confirming só pode ser iniciado após a reconciliação bancária.")

            partner = move.partner_id
            amount = sum(move.line_ids.filtered(lambda l: l.account_id.code == '221').mapped('credit'))

            if amount <= 0:
                raise UserError("O valor da fatura não é válido para confirming.")

            # Diário
            journal = self.env['account.journal'].search([('name', '=', 'Operações Confirming')], limit=1)
            if not journal:
                raise UserError("Diário 'Operações Confirming' não encontrado.")

            # Contas
            conta_221 = self.env['account.account'].search([('code', '=', '221')], limit=1)
            conta_2212 = self.env['account.account'].search([('code', '=', '2212')], limit=1)
            conta_1211 = self.env['account.account'].search([('code', '=', '12103')], limit=1)
            conta_12102 = self.env['account.account'].search([('code', '=', '12102')], limit=1)

            if not all([conta_221, conta_2212, conta_1211, conta_12102]):
                raise UserError("As contas 221, 2212, 1211 e 12102 devem estar configuradas.")

            # 1. Fornecedores → Fornecedores Confirming
            referencia = f"Transferência p/ Confirming - {move.name}"
            existe = self.env['account.move'].search([
                ('ref', '=', referencia),
                ('journal_id', '=', journal.id),
                ('move_type', '=', 'entry'),
            ], limit=1)

            if existe:
                raise UserError("Já existe um lançamento de transferência para Confirming associado a esta fatura.")

            move_1 = self.env['account.move'].create({
                'move_type': 'entry',
                'ref': referencia,
                'journal_id': journal.id,
                'date': move.date,
                'line_ids': [
                    (0, 0, {
                        'name': 'Transferência de Fornecedores para Confirming',
                        'debit': 0.0,
                        'credit': amount,
                        'account_id': conta_221.id,
                        'partner_id': partner.id,
                    }),
                    (0, 0, {
                        'name': 'Entrada em Fornecedores Confirming',
                        'debit': amount,
                        'credit': 0.0,
                        'account_id': conta_2212.id,
                        'partner_id': partner.id,
                    }),
                ]
            })
            move_1.action_post()

            # 2. Fornecedores Confirming → Banco Confirming
            # Usar a data do pagamento original da fatura (última linha reconciliada com conta 221)
            pagamento_lines = self.env['account.move.line'].search([
                ('account_id', '=', conta_221.id),
                ('matched_debit_ids.credit_move_id.move_id', '=', move.id),
            ], limit=1)
            data_pagamento_fatura = pagamento_lines.date or move.date

            move_2 = self.env['account.move'].create({
                'move_type': 'entry',
                'ref': f"Pagamento Confirming Banco - {move.name}",
                'journal_id': journal.id,
                'date': data_pagamento_fatura,
                'line_ids': [
                    (0, 0, {
                        'name': 'Pagamento Confirming para Banco',
                        'debit': 0.0,
                        'credit': amount,
                        'account_id': conta_2212.id,
                        'partner_id': partner.id,
                    }),
                    (0, 0, {
                        'name': 'Entrada no Banco Confirming',
                        'debit': amount,
                        'credit': 0.0,
                        'account_id': conta_1211.id,
                        'partner_id': partner.id,
                    }),
                ]
            })
            move_2.action_post()

            # 3. Banco Confirming → Banco CGD (em draft)
            move_3 = self.env['account.move'].create({
                'move_type': 'entry',
                'ref': f"Transferência Banco Confirming → CGD - {move.name}",
                'journal_id': journal.id,
                'date': move.x_studio_data_pagamento_confirming,
                'line_ids': [
                    (0, 0, {
                        'name': 'Transferência p/ Banco CGD',
                        'debit': 0.0,
                        'credit': amount,
                        'account_id': conta_1211.id,
                        'partner_id': partner.id,
                    }),
                    (0, 0, {
                        'name': 'Entrada no Banco CGD',
                        'debit': amount,
                        'credit': 0.0,
                        'account_id': conta_12102.id,
                        'partner_id': partner.id,
                    }),
                ]
            })
            # Não publicar ainda — fica em rascunho

            return {
                'name': 'Transferência Confirming Concluída',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': move_3.id,
                'view_mode': 'form',
                'target': 'current',
            }
                      

    def has_confirming_button(self):
        for rec in self:
            return rec.move_type == 'in_invoice' and rec.state == 'posted' and rec.x_studio_transferir_para_confirming

