from odoo import api, fields, models


class PgOdooConnection(models.Model):
    _name = 'pg.odoo.connection'
    _description = 'PG Ligacao Odoo do Cliente (por repositorio)'
    _order = 'repository_id, purpose'

    repository_id = fields.Many2one(
        'pg.ai.repository',
        string='Repositorio',
        required=True,
        ondelete='cascade',
        index=True,
    )
    purpose = fields.Selection(
        [
            ('production', 'Produção do cliente (adoção)'),
            ('brodoo_dev', 'Brodoo / Desenvolvimento (Staging)'),
            ('client_test', 'Testes / Validação do cliente'),
        ],
        string='Finalidade',
        required=True,
        help=(
            "production: Odoo de produção do cliente - análise de adoção.\n"
            "brodoo_dev: Odoo da branch 'brodoo' (build Staging Odoo.sh) - desenvolvimento.\n"
            "client_test: base de testes/validação do cliente - destino da promoção "
            "de dados vinda do brodoo_dev, antes de produção.\n\n"
            "A finalidade é o que autoriza a escrita nas migrações de dados: "
            "brodoo_dev e client_test aceitam escrita; production exige escalamento "
            "explícito (ver pg_odoo_migration_guard.py no _pg_template)."
        ),
    )
    name = fields.Char(string='Nome', compute='_compute_name', store=False)
    base_url = fields.Char(string='Odoo Base URL', help="Sem o sufixo /odoo. Ex.: https://cliente.odoo.com")
    database = fields.Char(string='Odoo Database')
    login = fields.Char(string='Odoo Login')
    api_key = fields.Char(string='Odoo API Key')
    active = fields.Boolean(string='Ativo', default=True)
    last_check_at = fields.Datetime(string='Ultima Verificacao', readonly=True)
    last_check_status = fields.Char(string='Estado Ultima Verificacao', readonly=True)

    # Odoo 19 deixou de suportar `_sql_constraints`: a restricao nao chegava a ser
    # criada na base e duas ligacoes com a mesma finalidade para o mesmo repositorio
    # passavam sem erro (o helper de consulta escolheria uma arbitrariamente).
    _pg_odoo_connection_repository_purpose_uniq = models.Constraint(
        'unique(repository_id, purpose)',
        'Ja existe uma ligacao Odoo com esta finalidade para este repositorio.',
    )

    @api.depends('purpose', 'base_url')
    def _compute_name(self):
        labels = dict(self._fields['purpose'].selection)
        for record in self:
            purpose_label = labels.get(record.purpose, record.purpose or '')
            record.name = ('%s - %s' % (purpose_label, record.base_url or '')).strip(' -')
