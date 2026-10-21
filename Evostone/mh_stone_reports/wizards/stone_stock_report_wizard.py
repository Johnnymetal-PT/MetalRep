# -*- coding: utf-8 -*-
import io
import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False


class StoneStockReportWizard(models.TransientModel):
    _name = 'stone.stock.report.wizard'
    _description = 'Wizard para Listagem de Stock de Pedras'

    # ========================================
    # FILTROS
    # ========================================

    product_ids = fields.Many2many(
        'product.product',
        string='Produtos',
        domain="[('product_form', '!=', 'none')]",
        help='Filtrar por produtos específicos. Deixe vazio para todos.'
    )

    product_form = fields.Selection([
        ('all', 'Todas as Formas'),
        ('block', 'Blocos'),
        ('slab', 'Placas'),
        ('strip', 'Bandas'),
        ('tiles', 'Ladrilhos'),
    ], string='Forma do Produto', default='all', required=True)

    location_ids = fields.Many2many(
        'stock.location',
        string='Localizações',
        domain="[('usage', '=', 'internal')]",
        help='Filtrar por localizações. Deixe vazio para todas.'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        required=True
    )

    # ========================================
    # OPÇÃO DE DETALHE
    # ========================================

    show_detail = fields.Boolean(
        string='Mostrar Detalhe (S/N individuais)',
        default=False,
        help='Se marcado, mostra os números de série individuais abaixo de cada produto.'
    )

    # ========================================
    # FORMATO DE SAÍDA
    # ========================================

    output_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ], string='Formato', default='pdf', required=True)

    # Campo para download do Excel
    excel_file = fields.Binary(string='Ficheiro Excel', readonly=True)
    excel_filename = fields.Char(string='Nome do Ficheiro', readonly=True)

    # ========================================
    # MÉTODOS
    # ========================================

    def _get_domain(self):
        """Construir domínio de pesquisa baseado nos filtros"""
        self.ensure_one()
        _logger.info(f"=== Construindo domínio para empresa: {self.company_id.name} (ID: {self.company_id.id}) ===")
        _logger.info(f"Filtros - Forma: {self.product_form}, Produtos: {self.product_ids.ids}, Localizações: {self.location_ids.ids}")

        # Filtro de empresa: incluir registos da empresa OU sem empresa definida
        domain = [
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
            ('state', '=', 'available'),  # Sempre disponível
            ('product_form', 'not in', ['none', False]),  # Excluir forma 'none' e False
        ]

        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))

        if self.product_form != 'all':
            domain.append(('product_form', '=', self.product_form))

        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))

        return domain

    def _get_stock_data(self):
        """Obter dados de stock agrupados por produto"""
        self.ensure_one()
        domain = self._get_domain()
        _logger.info(f"=== Stock Report Domain: {domain} ===")

        StoneStock = self.env['stone.stock'].sudo()

        # Verificar quantos registros existem sem filtro de estado
        all_records = StoneStock.search_count([('company_id', '=', self.company_id.id)])
        available_records = StoneStock.search_count([('company_id', '=', self.company_id.id), ('state', '=', 'available')])
        _logger.info(f"Total registros na empresa: {all_records}, Disponíveis: {available_records}")

        records = StoneStock.search(domain, order='product_id, base_lot_name, code')
        _logger.info(f"Registros encontrados com filtros: {len(records)}")

        # Agrupar por produto
        grouped = {}
        for rec in records:
            key = rec.product_id.id
            if key not in grouped:
                grouped[key] = {
                    'product_id': rec.product_id,
                    'product_name': rec.product_id.display_name,  # Nome completo com referência
                    'product_form': rec.product_form,
                    'count': 0,
                    'qty_available': 0,
                    'area': 0,
                    'volume': 0,
                    'details': [],  # Lista de S/N individuais
                }
            grouped[key]['count'] += 1
            grouped[key]['qty_available'] += rec.qty_available
            grouped[key]['area'] += rec.area
            grouped[key]['volume'] += rec.volume

            # Adicionar detalhe do S/N
            grouped[key]['details'].append({
                'name': rec.name,
                'code': rec.code,
                'length': rec.length,
                'width': rec.width,
                'thickness': rec.thickness,
                'area': rec.area,
                'volume': rec.volume,
                'qty_available': rec.qty_available,
                'peso': rec.peso,
                'location': rec.location_id.display_name if rec.location_id else '',
                'pcmp': rec.pcmp,
                'margin': rec.margin,
                'list_price': rec.list_price,
            })

        return {
            'records': list(grouped.values()),
            'show_detail': self.show_detail,
        }

    def _get_report_title(self):
        """Gerar título do relatório"""
        title = "Listagem de Stock"
        if self.product_form != 'all':
            form_labels = {
                'block': 'Blocos',
                'slab': 'Placas',
                'strip': 'Bandas',
                'tiles': 'Ladrilhos',
            }
            title += f" - {form_labels.get(self.product_form, '')}"
        return title

    def action_generate_report(self):
        """Gerar relatório"""
        self.ensure_one()

        if self.output_format == 'pdf':
            return self._generate_pdf()
        else:
            return self._generate_excel()

    def _generate_pdf(self):
        """Gerar relatório PDF"""
        return self.env.ref('mh_stone_reports.action_report_stone_stock_listing').report_action(self.ids)

    def _generate_excel(self):
        """Gerar relatório Excel"""
        if not XLSXWRITER_AVAILABLE:
            raise UserError(_('A biblioteca xlsxwriter não está instalada. Por favor instale: pip install xlsxwriter'))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Stock de Pedras')

        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4a86c7',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        header2_format = workbook.add_format({
            'bold': True,
            'bg_color': '#87CEEB',
            'font_color': 'black',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
        })
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
        })
        text_format = workbook.add_format({
            'border': 1,
        })
        product_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f0f0f0',
            'border': 1,
        })
        detail_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        detail_number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
            'font_size': 9,
        })
        # Formato para dimensões (3 casas decimais)
        detail_number_format_3 = workbook.add_format({
            'num_format': '#,##0.000',
            'border': 1,
            'font_size': 9,
        })
        # Formato para área/volume/disponível (4 casas decimais)
        detail_number_format_4 = workbook.add_format({
            'num_format': '#,##0.0000',
            'border': 1,
            'font_size': 9,
        })
        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#e0e0e0',
            'border': 1,
            'num_format': '#,##0.00',
        })

        # Título
        row = 0
        worksheet.merge_range(row, 0, row, 11, self._get_report_title(), title_format)
        row += 1
        worksheet.write(row, 0, f"Data: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}")
        row += 2

        # Cabeçalhos principais
        headers = [
            ('Produto', 35),
            ('Forma', 12),
            ('Stock Pedra', 12),
            ('Área (m²)', 12),
            ('Volume (m³)', 12),
        ]

        for i, (header, width) in enumerate(headers):
            worksheet.write(row, i, header, header_format)
            worksheet.set_column(i, i, width)

        row += 1

        data = self._get_stock_data()
        form_labels = {'block': 'Bloco', 'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos', 'none': '-'}

        # Totais
        total_count = 0
        total_area = 0
        total_volume = 0

        for rec in data['records']:
            # Linha do produto
            worksheet.write(row, 0, rec['product_name'] or '', product_format)
            worksheet.write(row, 1, form_labels.get(rec['product_form'], '-'), product_format)
            worksheet.write(row, 2, f"{rec['count']} Unidades", product_format)
            worksheet.write(row, 3, rec['area'], workbook.add_format({'bold': True, 'bg_color': '#f0f0f0', 'border': 1, 'num_format': '#,##0.0000'}))
            worksheet.write(row, 4, rec['volume'], workbook.add_format({'bold': True, 'bg_color': '#f0f0f0', 'border': 1, 'num_format': '#,##0.0000'}))
            row += 1

            total_count += rec['count']
            total_area += rec['area']
            total_volume += rec['volume']

            # Detalhes (S/N individuais)
            if self.show_detail and rec['details']:
                # Cabeçalho de detalhe
                detail_headers = ['S/N', 'Comp.', 'Larg.', 'Esp.', 'Área (m²)', 'Volume (m³)', 'Disp.', 'Peso', 'Local', 'PCMP', 'Margem', 'Preço Unit.']
                for i, h in enumerate(detail_headers):
                    worksheet.write(row, i, h, header2_format)
                    if i == 0:
                        worksheet.set_column(i, i, 25)
                    elif i == 8:
                        worksheet.set_column(i, i, 15)
                    else:
                        worksheet.set_column(i, i, 10)
                row += 1

                for detail in rec['details']:
                    worksheet.write(row, 0, detail['name'] or '', detail_format)
                    worksheet.write(row, 1, detail['length'], detail_number_format_3)  # 3 casas
                    worksheet.write(row, 2, detail['width'], detail_number_format_3)   # 3 casas
                    worksheet.write(row, 3, detail['thickness'], detail_number_format_3)  # 3 casas
                    worksheet.write(row, 4, detail['area'], detail_number_format_4)    # 4 casas
                    worksheet.write(row, 5, detail['volume'], detail_number_format_4)  # 4 casas
                    worksheet.write(row, 6, detail['qty_available'], detail_number_format_4)  # 4 casas
                    worksheet.write(row, 7, detail['peso'], detail_number_format)
                    worksheet.write(row, 8, detail['location'] or '', detail_format)
                    worksheet.write(row, 9, detail['pcmp'], detail_number_format)
                    worksheet.write(row, 10, detail['margin'], detail_number_format)
                    worksheet.write(row, 11, detail['list_price'], detail_number_format)
                    row += 1

                row += 1  # Espaço entre produtos

        # Linha de totais
        row += 1
        worksheet.write(row, 0, 'TOTAIS', total_format)
        worksheet.write(row, 1, '', total_format)
        worksheet.write(row, 2, f"{total_count} Unidades", total_format)
        worksheet.write(row, 3, total_area, total_format)
        worksheet.write(row, 4, total_volume, total_format)

        workbook.close()
        output.seek(0)

        # Guardar ficheiro
        filename = f"stock_pedras_{fields.Date.today().strftime('%Y%m%d')}.xlsx"
        self.write({
            'excel_file': base64.b64encode(output.read()),
            'excel_filename': filename,
        })

        # Retornar acção de download
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/excel_file/{filename}?download=true',
            'target': 'self',
        }
