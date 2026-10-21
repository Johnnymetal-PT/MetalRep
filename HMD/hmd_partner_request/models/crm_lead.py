# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import Command, _, fields, models
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    hmd_is_account_request = fields.Boolean(
        string="Pedido de conta de parceiro",
        help="Marcado pelo formulario do website. Distingue os pedidos de "
        "conta dos restantes leads.",
        copy=False,
    )
    hmd_vat = fields.Char(
        string="NIF (pedido de conta)",
        help="Numero de contribuinte tal como foi escrito no formulario. Nao "
        "e validado: serve para encontrar ou criar o parceiro na aprovacao.",
        copy=False,
    )
    hmd_account_state = fields.Selection(
        selection=[
            ("pending", "Por tratar"),
            ("approved", "Aprovado"),
            ("refused", "Recusado"),
        ],
        string="Estado do pedido",
        default="pending",
        copy=False,
        tracking=True,
    )

    # -- aprovacao --------------------------------------------------------

    def _hmd_find_partner(self):
        """Procura um parceiro que ja represente quem esta a pedir conta.

        Primeiro pelo NIF, que e unico por empresa, e so depois pelo email.
        A ordem importa: duas pessoas da mesma empresa podem pedir conta com
        emails diferentes, e nesse caso e a empresa que ja existe que deve ser
        reutilizada em vez de nascer um duplicado.
        """
        self.ensure_one()
        Partner = self.env["res.partner"]
        if self.hmd_vat:
            partner = Partner.search([("vat", "=", self.hmd_vat)], limit=1)
            if partner:
                return partner
        if self.email_from:
            partner = Partner.search([("email", "=", self.email_from)], limit=1)
            if partner:
                return partner
        return Partner.browse()

    def _hmd_partner_values(self):
        self.ensure_one()
        return {
            "name": self.partner_name or self.contact_name or self.email_from,
            "company_type": "company",
            "email": self.email_from,
            "phone": self.phone,
            "vat": self.hmd_vat or False,
            "website": self.website,
            "street": self.street,
            "zip": self.zip,
            "city": self.city,
            "country_id": self.country_id.id,
            "customer_rank": 1,
        }

    def _hmd_grant_portal(self, partner):
        """Concede acesso ao portal e deixa o Odoo enviar o convite.

        Usa-se o assistente nativo (`portal.wizard`) em vez de criar o
        res.users a mao: e ele que gera o convite com a ligacao de definicao
        de palavra-passe, e que sabe tratar dos casos de fronteira.

        Em Odoo 18 quem concede e a LINHA do assistente
        (`portal.wizard.user.action_grant_access`), e nao o assistente. O
        `in_portal` de versoes anteriores ja nao existe. Confirmado em
        vendor/odoo_src/.../portal/wizard/portal_wizard.py (16/09/2026).

        :return: texto para o registo no lead, a dizer o que aconteceu
        """
        self.ensure_one()
        wizard = self.env["portal.wizard"].create({
            "partner_ids": [Command.set(partner.ids)],
        })
        linha = wizard.user_ids.filtered(lambda l: l.partner_id == partner)[:1]
        if not linha:
            return _("nao foi possivel preparar o convite — conceder a mao")
        if linha.is_internal:
            return _("ja e utilizador interno, nao precisa de acesso ao portal")
        if linha.is_portal:
            return _("ja tinha acesso ao portal")
        # Levanta UserError se o email colidir com outro utilizador. Deixa-se
        # subir: quem aprova ve a mensagem e decide, em vez de o pedido ficar
        # aprovado com o convite por enviar sem ninguem saber.
        linha.action_grant_access()
        return _("convite enviado")

    def action_hmd_approve_account(self):
        self.ensure_one()
        if not self.email_from:
            raise UserError(_(
                "O pedido nao tem email, e sem email nao ha convite para o "
                "portal. Preencha o email no pedido antes de aprovar."
            ))

        partner = self._hmd_find_partner()
        if partner:
            novo = False
            # Nao se sobrescreve o que ja existe: os dados do parceiro em
            # carteira valem mais do que os escritos num formulario publico.
            # So se preenche o que estiver em falta.
            faltas = {
                campo: valor
                for campo, valor in self._hmd_partner_values().items()
                if valor and not partner[campo]
            }
            if faltas:
                partner.write(faltas)
        else:
            novo = True
            partner = self.env["res.partner"].create(self._hmd_partner_values())

        self.partner_id = partner
        nota_portal = self._hmd_grant_portal(partner)
        self.hmd_account_state = "approved"

        # Markup e nao _(): uma string normal em message_post vai escapada e
        # o utilizador ve "&lt;br/&gt;" escrito na mensagem. O operador % do
        # Markup escapa os argumentos que nao sejam Markup, e o
        # _get_html_link() ja devolve Markup, por isso a ligacao passa
        # inteira.
        self.message_post(body=Markup("%s<br/>%s: %s (%s)<br/>%s: %s") % (
            _("Pedido de conta aprovado."),
            _("Parceiro"),
            partner._get_html_link(),
            _("criado agora") if novo else _("ja existia"),
            _("Acesso ao portal"),
            nota_portal,
        ))
        return True

    def action_hmd_refuse_account(self):
        """Recusa sem apagar: o registo de quem pediu e quando fica."""
        for lead in self:
            lead.hmd_account_state = "refused"
            lead.message_post(body=_("Pedido de conta recusado."))
        return True
