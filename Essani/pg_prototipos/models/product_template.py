# -*- coding: utf-8 -*-
"""Circuito de alterações: uma mudança nas especificações de um protótipo tem de
chegar a quem gere a produção, e ficar registada."""

from odoo import _, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        """Avisa os projetos ligados quando as especificações do protótipo mudam.

        Porque é um override de `write` e não uma regra de automatização: o código
        vive no repositório, é revisto antes de correr e não depende de uma ação de
        servidor guardada na base de dados, que se perde numa restauração e que só
        se descobre partida quando alguém falha a gravar um artigo.
        """
        resultado = super().write(vals)
        if "product_properties" not in vals:
            return resultado

        for produto in self:
            projetos = self.env["project.project"].search(
                [("pg_artigo_prototipo", "=", produto.id)])
            if not projetos:
                continue
            resumo = produto._pg_resumo_especificacoes()
            for projeto in projetos:
                projeto.message_post(
                    body=_("As especificações do artigo %(artigo)s foram alteradas. "
                           "%(resumo)s",
                           artigo=produto.display_name, resumo=resumo),
                    subtype_xmlid="mail.mt_note",
                )
                for gestor in projeto._pg_gestores():
                    projeto.activity_schedule(
                        "mail.mail_activity_data_todo",
                        user_id=gestor.id,
                        summary=_("Especificações alteradas"),
                        note=_("As especificações de %s mudaram. Rever o impacto na "
                               "produção do protótipo.", produto.display_name),
                    )
        return resultado

    def _pg_resumo_especificacoes(self):
        """Especificações preenchidas, numa linha.

        Vai numa linha só, com separador, e não em HTML: o `message_post` de corpo
        em texto simples envolve tudo em `<p>` e escapa etiquetas, mas não converte
        quebras de linha. Etiquetas apareciam literais, `\\n` desaparecia.
        """
        self.ensure_one()
        linhas = []
        for prop in self.read(["product_properties"])[0].get("product_properties") or []:
            if not isinstance(prop, dict) or prop.get("type") == "separator":
                continue
            valor = prop.get("value")
            if valor not in (None, False, "", 0, 0.0):
                linhas.append("%s: %s" % (prop.get("string"), valor))
        return " · ".join(linhas) or _("(sem valores preenchidos)")
