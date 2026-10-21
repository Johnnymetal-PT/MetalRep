from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import re

_logger = logging.getLogger(__name__)

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    origin_bom_id = fields.Many2one(
        'mrp.bom',
        string='BOM Original',
        help='Refer�ncia � BOM original da qual esta BOM foi duplicada.',
        copy=False,
    )
    
    # NOVO CAMPO: Liga a BOM duplicada � Ordem de Fabrico espec�fica
    production_id = fields.Many2one(
        'mrp.production',
        string='Ordem de Fabrico Associada',
        help='Ordem de Fabrico para a qual esta BOM foi duplicada.',
        copy=False,
        ondelete='cascade', # Opcional: Apaga a BOM duplicada se a MO for apagada
    )
    

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    original_bom_id = fields.Many2one(
        'mrp.bom',
        string='BOM Original',
        help='BOM original antes da duplica��o'
    )
    
    fabric_consumption_info = fields.Text(
        string='Informa��es de Consumo de Tecido',
        help='Informa��es detalhadas sobre o consumo de tecido calculado'
    )
    
    @api.model
    def create(self, vals):
        """
        Sobrescreve o m�todo create para aplicar valida��o e l�gica de duplica��o da BOM.
        """
        # Primeiro cria a produ��o
        production = super(MrpProduction, self).create(vals)
        
        # Depois processa o consumo de tecido com valida��o
        self._process_fabric_consumption(production)
        return production
    
    def _process_fabric_consumption(self, production):
        """
        Processa o consumo de tecido: valida variantes, duplica a BOM e atualiza os tecidos.
        """
        _logger.info(f"Iniciando _process_fabric_consumption para MO: {production.name} (ID: {production.id})")
        try:
            if not production.bom_id or not production.bom_id.exists():
                _logger.warning(f"Ordem de fabrica��o {production.name} n�o tem BOM definida. Pulando processamento de tecido.")
                return
            
            # Salva a BOM original
            production.original_bom_id = production.bom_id.id
            _logger.info(f"BOM original para MO {production.name}: (ID: {production.original_bom_id.id})")
            
            # Verifica se h� tecidos na BOM
            fabric_lines = self._get_fabric_lines(production.bom_id)
            if not fabric_lines:
                _logger.info(f"Nenhum tecido marcado como '� Tecido?' encontrado na BOM da ordem de fabrica��o {production.name}. Pulando processamento de tecido.")
                return
            
            _logger.info(f"Tecidos encontrados na BOM original: {[line.product_id.name for line in fabric_lines]}")

            # Extrai informa��es das variantes da descri��o
            variant_info = self._extract_variant_info_v2(production, fabric_lines)
            if not variant_info:
                _logger.warning(f"Nenhuma informa��o de variante de tecido encontrada na descri��o da ordem de fabrica��o {production.name}. Pulando processamento de tecido.")
                return
            
            _logger.info(f"Informa��es de variante extra�das: {variant_info}")

            # NOVA VALIDA��O: Verifica se todas as variantes existem nas tabelas
            self._validate_fabric_variants(fabric_lines, variant_info, production)

            # Duplica a BOM mantendo a origem
            duplicated_bom = self._duplicate_bom_with_origin(production.bom_id, production)
            
            # Atribui a BOM duplicada � ordem de fabrica��o ANTES de manipular os movimentos
            production.write({'bom_id': duplicated_bom.id})
            _logger.info(f"BOM da ordem de fabrica��o {production.name} atualizada para (ID: {production.bom_id.id}) antes de manipular movimentos.")

            # Remove movimentos de mat�ria-prima existentes para evitar duplica��o
            if production.move_raw_ids:
                _logger.info(f"Removendo {len(production.move_raw_ids)} movimentos de mat�ria-prima existentes para {production.name}.")
                production.move_raw_ids.unlink()

            # Atualiza os tecidos na BOM duplicada (que agora � a BOM da produ��o)
            consumption_info = self._update_fabric_lines_v2(duplicated_bom, variant_info, production.product_qty, production)
            
            # Atualiza as informa��es de consumo na produ��o
            production.write({
                'bom_id': duplicated_bom.id,
                'fabric_consumption_info': consumption_info,
            })
            
            production.bom_id = duplicated_bom
            #production._onchange_bom_id()

            # Tenta regenerar os movimentos de estoque com a BOM j� atualizada e linhas corrigidas
            if hasattr(production, '_generate_moves'):
                _logger.info(f"Regenerando movimentos usando _generate_moves() para {production.name}.")
                production._generate_moves()
            elif hasattr(production, '_create_moves'):
                _logger.info(f"Regenerando movimentos usando _create_moves() para {production.name}.")
                production._create_moves()
            elif hasattr(production, '_action_confirm'):
                _logger.info(f"Regenerando movimentos usando _action_confirm() para {production.name}.")
                production._action_confirm()
            elif hasattr(production, 'button_plan'):
                _logger.info(f"Regenerando movimentos usando button_plan() para {production.name}.")
                production.button_plan()    
            else:
                _logger.warning(f"Nenhum m�todo conhecido dispon�vel para regenerar movimentos para {production.name}. Pode haver problemas de stock.")

            _logger.info(f"Processamento de consumo de tecido conclu�do para MO {production.name}. BOM duplicada e tecidos atualizados.")
            
        except ValidationError as ve:
            # Re-lan�a erros de valida��o para que sejam mostrados ao usu�rio
            _logger.error(f"Erro de valida��o ao processar consumo de tecido para {production.name}: {str(ve)}")
            raise ve
        except Exception as e:
            _logger.error(f"Erro ao processar consumo de tecido para {production.name}: {str(e)}", exc_info=True)
            raise UserError(_("Ocorreu um erro ao processar o consumo de tecido. Verifique os logs para mais detalhes."))
    
    def _validate_fabric_variants(self, fabric_lines, variant_info, production):
        """
        NOVA FUN��O: Valida se todas as variantes selecionadas existem nas tabelas de consumo.
        """
        missing_variants = []
        
        for line in fabric_lines:
            fabric_product_tmpl = line.product_id.product_tmpl_id
            fabric_identifier = fabric_product_tmpl.fabric_identifier_id

            if not fabric_identifier:
                missing_variants.append(f"Produto '{fabric_product_tmpl.name}' n�o tem 'Identificador de Tecido' definido")
                continue

            if fabric_identifier in variant_info:
                subvariant_data = variant_info[fabric_identifier]
                subvariant_name = subvariant_data['subvariant_name']

                # S� valida se n�o for "Nenhum"
                if subvariant_name != "Nenhum":
                    fabric_variant = self.env['fabric.variant'].search([
                        ('product_tmpl_id', '=', fabric_product_tmpl.id),
                        ('variant_id', '=', fabric_identifier),
                        ('subvariant_name', '=', subvariant_name)
                    ], limit=1)

                    if not fabric_variant:
                        missing_variants.append(f"Variante '{subvariant_name}' n�o encontrada na tabela do tecido '{fabric_product_tmpl.name}' (FABRIC {fabric_identifier})")
            else:
                missing_variants.append(f"Tecido '{fabric_product_tmpl.name}' (FABRIC {fabric_identifier}) n�o encontrado na descri��o da ordem")

        if missing_variants:
            error_message = "N�o � poss�vel gerar a ordem de fabrica��o. Variantes de tecido em falta:\n\n" + "\n".join([f" {msg}" for msg in missing_variants])
            error_message += "\n\nPor favor, configure as tabelas de consumo de tecido antes de continuar."
            raise ValidationError(error_message)
    
    
    def _get_fabric_lines(self, bom):
        """
        Retorna as linhas de tecido da BOM.
        """
        fabric_lines = []
        for line in bom.bom_line_ids:
            if line.product_id.product_tmpl_id.is_fabric:
                fabric_lines.append(line)
        return fabric_lines
    
    def _extract_variant_info_v2(self, production, fabric_lines):
        """
        FUNÇÃO MODIFICADA: Extrai informações de variantes e determina a origem do tecido.
        Armazena se é 'PRIVATE LABEL' ou 'CLIENT' para uso posterior.
        """
        description = production.product_description_variants or ''
        _logger.info(f"Descrio da ordem de fabricao para extrao de variantes: {description}")
        if not description:
            return {}

        variant_info = {}
        total_detected = False
        
        # Identifica primeiro quais tecidos são fornecidos pelo cliente
        client_supplied_fabrics = self._extract_client_supplied_fabrics_from_product_attributes_corrected(production)

        pattern = r'FABRIC USED IN\s*(\d+)\s*:\s*([^:\n\r]+)\s*:\s*([^\n\r]+)'
        matches = re.findall(pattern, description, re.IGNORECASE)

        for fabric_num_str, subvariant, label in matches:
            fabric_num = int(fabric_num_str)
            subvariant_clean = subvariant.strip()
            label_clean = label.strip()

            if fabric_num == 1 and subvariant_clean.lower() == "total":
                total_detected = True

            # NOVO: Determina a origem do tecido
            if fabric_num in client_supplied_fabrics:
                origin = "COM FABRIC SUPLIED BY THE CLIENT"
            else:
                origin = "FABRIC SUPLIED BY PRIVATE LABEL"

            variant_info[fabric_num] = {
                'subvariant_name': subvariant_clean,
                'label': label_clean if label_clean.lower() != 'nenhum' else ' ',
                'origin': origin  # Armazena a origem
            }
            _logger.info(f"Variante extrada: FABRIC {fabric_num} -> Subvariante: {subvariant_clean} / Origem: {origin}")

        # Lógica para "Total" e valores padrão permanece a mesma
        if total_detected:
            for i in range(1, 4):
                if i not in variant_info:
                    variant_info[i] = {
                        'subvariant_name': 'Nenhum',
                        'label': 'Mesmo',
                        'origin': 'N/A' # Origem não aplicável
                    }
        else:
            bom_fabric_identifiers = {line.product_id.product_tmpl_id.fabric_identifier_id for line in fabric_lines if line.product_id.product_tmpl_id.fabric_identifier_id}
            if 3 in bom_fabric_identifiers and 3 not in variant_info:
                variant_info[3] = {
                    'subvariant_name': 'Nenhum',
                    'label': 'Mesmo',
                    'origin': 'N/A'
                }

        return variant_info
    
    def _duplicate_bom_with_origin(self, original_bom, production): # Agora recebe o objeto 'production'
        """
        FUN��O MELHORADA: Duplica a BOM mantendo a refer�ncia � BOM original
        e � Ordem de Fabrico, sem usar o campo 'code' para identifica��o.
        """
        _logger.info(f"A duplicar BOM original: {original_bom.id} - {original_bom.code}")

        # Verifica se j� existe uma BOM duplicada para esta produ��o a partir desta BOM original
        existing_bom = self.env['mrp.bom'].search([
            ('origin_bom_id', '=', original_bom.id),
            ('production_id', '=', production.id) # Usa o novo campo para a verifica��o
        ], limit=1)

        if existing_bom:
            _logger.info(f"BOM duplicada j� existe para esta MO e BOM original: {existing_bom.id} reutilizando.")
            return existing_bom

        duplicated_bom = original_bom.copy({
            'code': False, # Define o campo 'code' como False (ou '')
            'active': True,
            'origin_bom_id': original_bom.id,
            'production_id': production.id, # Liga a BOM duplicada � Ordem de Fabrico atual
            'bom_line_ids': [(0, 0, line.copy_data()[0]) for line in original_bom.bom_line_ids],
        })

        _logger.info(f"BOM duplicada criada: {duplicated_bom.id} (Code: False)")
        return duplicated_bom
    
    def _get_main_product_name(self, production):
        """
        Obt�m o nome do produto principal dinamicamente.
        Remove sufixos de variantes para obter o nome base.
        """
        if not production.product_id:
            _logger.warning("Produto principal n�o encontrado na produ��o")
            return "PRODUTO"
        
        main_product_name = production.product_id.name
        
        # Remove sufixos comuns de variantes se existirem
        # Exemplo: "CADEIRA EXECUTIVA (FABRIC SUPLIED BY...)" -> "CADEIRA EXECUTIVA"
        if " (" in main_product_name:
            main_product_name = main_product_name.split(" (")[0]
        
        _logger.info(f"Nome do produto principal extra�do: {main_product_name}")
        return main_product_name.strip()
    
    def _build_detailed_description(self, variant_info, production, client_supplied_fabrics):
        """
        FUNÇÃO CORRIGIDA E SEGURA: Apenas constrói uma string de descrição detalhada.
        NÃO cria nem modifica o produto final.
        """
        try:
            # Obtém o nome base do produto original para usar na descrição.
            main_product_name = self._get_main_product_name(production)
            
            description_parts = [f"{main_product_name} ("]
            fabric_entries = []
            
            for fabric_num in sorted(variant_info.keys()):
                subvariant_data = variant_info[fabric_num]
                if subvariant_data['subvariant_name'].lower() == "nenhum":
                    continue
                
                origin = subvariant_data.get('origin', 'FABRIC SUPLIED BY PRIVATE LABEL')
                fabric_entries.append(origin)
                fabric_entries.append(subvariant_data['subvariant_name'])
            
            if fabric_entries:
                description_parts.append(", ".join(fabric_entries))
            description_parts.append(")")
            
            detailed_description = "".join(description_parts)
            _logger.info(f"Descrição detalhada construída para referência: {detailed_description}")
            return detailed_description

        except Exception as e:
            _logger.error(f"Erro ao construir a string de descrição detalhada: {str(e)}")
            return f"Erro na construção da descrição: {str(e)}"

        except Exception as e:
            _logger.error(f"Erro ao construir/criar produto final detalhado: {str(e)}")
            # Em caso de erro, retorna o produto original para não parar o processo
            return production.product_id
        

    def _extract_client_supplied_fabrics_from_product_attributes_corrected(self, production):
        """
        FUN��O CORRIGIDA: Extrai tecidos fornecidos pelo cliente a partir dos atributos 
        do produto configurado durante a venda.
        
        CORRE��O CR�TICA: Identifica apenas os valores SELECIONADOS pelo utilizador,
        n�o todas as op��es dispon�veis.
        """
        client_supplied_fabrics = set()
        
        _logger.info("Iniciando extra��o CORRIGIDA de tecidos CLIENT a partir dos atributos do produto")
        
        if not production.product_id:
            _logger.warning("Produto n�o encontrado na produ��o")
            return client_supplied_fabrics
        
        # M�TODO PRINCIPAL: Buscar nos valores SELECIONADOS do produto espec�fico
        try:
            if hasattr(production.product_id, 'product_template_attribute_value_ids'):
                # Dicion�rio para rastrear o �ltimo valor encontrado para cada fabric
                fabric_selections = {}
                
                for ptav in production.product_id.product_template_attribute_value_ids:
                    attribute_name = ptav.attribute_id.name if ptav.attribute_id else ""
                    value_name = ptav.product_attribute_value_id.name if ptav.product_attribute_value_id else ""
                    
                    _logger.info(f"Atributo SELECIONADO do produto: {attribute_name} = {value_name}")
                    
                    # Verifica se � um atributo de fabric supply (n�o FABRIC USED IN)
                    if ("fabric" in attribute_name.lower() and 
                        "used in" not in attribute_name.lower()):
                        
                        # Extrai o n�mero do fabric
                        fabric_match = re.search(r'fabric\s*(\d+)', attribute_name, re.IGNORECASE)
                        if fabric_match:
                            fabric_num = int(fabric_match.group(1))
                            
                            # Guarda a sele��o para este fabric (sobrescreve se houver m�ltiplas)
                            fabric_selections[fabric_num] = value_name
                            _logger.info(f"Sele��o registrada para FABRIC {fabric_num}: {value_name}")
                
                # Agora processa as sele��es finais
                for fabric_num, selected_value in fabric_selections.items():
                    if "client" in selected_value.lower() or "com fabric suplied by the client" in selected_value.lower():
                        client_supplied_fabrics.add(fabric_num)
                        _logger.info(f"FABRIC {fabric_num} CONFIRMADO como CLIENT: {selected_value}")
                    else:
                        _logger.info(f"FABRIC {fabric_num} CONFIRMADO como PRIVATE LABEL: {selected_value}")
        
        except Exception as e:
            _logger.warning(f"Erro ao buscar atributos selecionados do produto: {str(e)}")
        
        # M�TODO FALLBACK: Se n�o conseguir identificar via atributos selecionados
        if not fabric_selections:
            _logger.warning("Nenhuma sele��o de fabric encontrada nos atributos do produto")
            
            # Tenta m�todo alternativo: buscar no nome do produto
            try:
                product_name = production.product_id.name
                if "COM FABRIC SUPLIED BY THE CLIENT" in product_name:
                    main_product_name = self._get_main_product_name(production)
                    pattern = f"{re.escape(main_product_name)} \\("
                    
                    if re.search(pattern, product_name) and ")" in product_name:
                        match = re.search(f"{re.escape(main_product_name)} \\((.+)\\)", product_name)
                        if match:
                            content = match.group(1)
                            parts = [part.strip() for part in content.split(",")]
                            
                            i = 0
                            fabric_num = 1
                            while i < len(parts):
                                if i < len(parts):
                                    origin = parts[i]
                                    if "COM FABRIC SUPLIED BY THE CLIENT" in origin:
                                        client_supplied_fabrics.add(fabric_num)
                                        _logger.info(f"FABRIC {fabric_num} identificado como CLIENT via nome do produto (fallback)")
                                    else:
                                        _logger.info(f"FABRIC {fabric_num} identificado como PRIVATE LABEL via nome do produto (fallback)")
                                    
                                    i += 2  # origem + nome da pe�a
                                    fabric_num += 1
                                else:
                                    break
            
            except Exception as e:
                _logger.warning(f"Erro no m�todo fallback: {str(e)}")
        
        _logger.info(f"RESULTADO FINAL - Tecidos identificados como CLIENT: {client_supplied_fabrics}")
        return client_supplied_fabrics
    
    def _update_fabric_lines_v2(self, bom, variant_info, quantity, production):
        """
        FUNÇÃO CORRIGIDA FINAL: Garante que a pesquisa da tabela de consumo para
        produtos PRIVATE LABEL é feita no template original, assegurando que as
        quantidades são calculadas corretamente e as compras geradas.
        """
        # Mapear os produtos de tecido existentes na BOM duplicada para fácil acesso
        existing_fabric_bom_lines_map = {}
        for line in bom.bom_line_ids:
            if line.product_id.product_tmpl_id.is_fabric:
                fabric_identifier = line.product_id.product_tmpl_id.fabric_identifier_id
                if fabric_identifier:
                    existing_fabric_bom_lines_map[fabric_identifier] = line

        client_supplied_fabrics = self._extract_client_supplied_fabrics_from_product_attributes_corrected(production)
        consumption_info = []

        # Processar as novas/atualizadas linhas de tecido com base em variant_info
        for fabric_identifier, subvariant_data in variant_info.items():
            subvariant_name = subvariant_data["subvariant_name"]
            label = subvariant_data["label"]

            # Encontra o template de produto ORIGINAL correspondente ao FABRIC X
            original_fabric_product_tmpl = self.env["product.template"].search([
                ("fabric_identifier_id", "=", fabric_identifier),
                ("is_fabric", "=", True)
            ], limit=1)

            if not original_fabric_product_tmpl:
                _logger.warning(f"AVISO: Não foi possível encontrar o template de produto para o identificador de tecido {fabric_identifier}. Pulando.")
                consumption_info.append(f"AVISO: FABRIC {fabric_identifier} - Template de produto não encontrado. Pulando.")
                continue
            
            original_product = original_fabric_product_tmpl.product_variant_id

            _logger.info(f"DEBUG: Processing variant info for FABRIC {fabric_identifier}: Subvariant={subvariant_name}, Label={label}")

            # Caso 1: Subvariante "Nenhum" - Remove da BOM
            if subvariant_name.lower() == "nenhum":
                _logger.info(f"Subvariante {subvariant_name} marcada como 'Nenhum'. Removendo da BOM.")
                consumption_info.append(f"INFO: FABRIC {fabric_identifier} - Subvariante 'Nenhum' removida da BOM.")
                if fabric_identifier in existing_fabric_bom_lines_map:
                    existing_fabric_bom_lines_map[fabric_identifier].unlink()
                    _logger.info(f"Linha de BOM para FABRIC {fabric_identifier} removida porque a subvariante é 'Nenhum'.")
                continue

            # Criar o produto duplicado (esta parte está correta)
            new_name = f"{original_fabric_product_tmpl.name} - {subvariant_name}: {label}"
            updated_product = self._create_fabric_product_for_mo_safe(original_product, new_name, production.name, subvariant_name, label)
            
            # Determinar se o tecido é fornecido pelo cliente
            is_client_supplied = fabric_identifier in client_supplied_fabrics

            # Calcular consumo a partir da tabela de consumo para esta combinação
            _logger.info(
                f"Calculando consumo para FABRIC {fabric_identifier} ({updated_product.name}) – origem: {'CLIENT' if is_client_supplied else 'PRIVATE LABEL'}"
            )
            fabric_variant = self.env["fabric.variant"].search(
                [
                    ("product_tmpl_id", "=", original_fabric_product_tmpl.id),
                    ("variant_id", "=", fabric_identifier),
                    ("subvariant_name", "=", subvariant_name),
                ],
                limit=1,
            )
            if fabric_variant:
                _logger.info(
                    f"Tabela de consumo encontrada para '{subvariant_name}' no template original '{original_fabric_product_tmpl.name}'."
                )
                new_consumption = fabric_variant.get_consumption_for_quantity(int(quantity))
                _logger.info(f"Consumo calculado para {quantity} unidades: {new_consumption}m")
            else:
                _logger.warning(
                    f"CONFIGURAÇÃO EM FALTA: Nenhuma entrada de variante encontrada para o template '{original_fabric_product_tmpl.name}', variante {fabric_identifier}, subvariante '{subvariant_name}'. Definindo quantidade para 0."
                )
                new_consumption = 0.0

            # Se for tecido fornecido pelo cliente, criar recibo de consignação e registar
            if is_client_supplied:
                try:
                    # Criar uma recepção de consignação para a quantidade calculada
                    self._create_consignment_receipt(production, updated_product, new_consumption)
                    consumption_info.append(
                        f"CLIENT: FABRIC {fabric_identifier}: {updated_product.name} - {new_consumption} {updated_product.uom_id.name} (consignação)"
                    )

                    # --- Ajuste específico para tecidos fornecidos pelo cliente ---
                    # 1. Remover rotas MTO e de compra tanto no product.product como no product.template
                    route_mto = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)
                    route_buy = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)
                    for route in [route_mto, route_buy]:
                        if route:
                            # Remover do product (product.product)
                            if route in updated_product.route_ids:
                                updated_product.write({'route_ids': [(3, route.id, 0)]})
                                _logger.info(f"Removida rota {route.name} do produto {updated_product.display_name} por ser tecido CLIENTE.")
                            # Remover do template (product.template)
                            if route in updated_product.product_tmpl_id.route_ids:
                                updated_product.product_tmpl_id.write({'route_ids': [(3, route.id, 0)]})
                                _logger.info(f"Removida rota {route.name} do template de {updated_product.display_name} por ser tecido CLIENTE.")
                    # Desabilitar a flag purchase_ok tanto no produto quanto no template
                    if updated_product.purchase_ok:
                        updated_product.write({'purchase_ok': False})
                    if updated_product.product_tmpl_id.purchase_ok:
                        updated_product.product_tmpl_id.write({'purchase_ok': False})

                    # 2. Criar uma linha na ordem de venda para que o tecido apareça na entrega
                    try:
                        if production.origin:
                            sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
                            if sale_order:
                                self.env['sale.order.line'].create({
                                    'order_id': sale_order.id,
                                    'product_id': updated_product.id,
                                    'product_uom_qty': new_consumption,
                                    'product_uom': updated_product.uom_id.id,
                                    'price_unit': 0.0,
                                    'name': updated_product.display_name,
                                })
                                _logger.info(
                                    f"Linha de venda criada para {updated_product.display_name} (qtde {new_consumption}) na SO {sale_order.name} para entrega ao cliente."
                                )
                    except Exception as e:
                        _logger.warning(f"Não foi possível criar linha de SO para tecido cliente {updated_product.display_name}: {e}")
                    # --- Fim do ajuste específico ---
                except Exception as e:
                    _logger.error(
                        f"Erro ao criar recibo de consignação para FABRIC {fabric_identifier}: {str(e)}"
                    )
            else:
                # Tecido normal (private label) – apenas regista o consumo
                consumption_info.append(
                    f"PRIVATE: FABRIC {fabric_identifier}: {updated_product.name} - {new_consumption} {updated_product.uom_id.name}"
                )
            # Atualiza ou cria a linha na BOM com a quantidade correta
            if fabric_identifier in existing_fabric_bom_lines_map:
                existing_line = existing_fabric_bom_lines_map[fabric_identifier]
                existing_line.write({
                    "product_id": updated_product.id,
                    "product_qty": new_consumption,
                    "product_uom_id": updated_product.uom_id.id,
                })
                _logger.info(f"Linha de BOM existente para FABRIC {fabric_identifier} atualizada para {updated_product.name} com {new_consumption} {updated_product.uom_id.name}.")
            else:
                self.env["mrp.bom.line"].create({
                    "bom_id": bom.id,
                    "product_id": updated_product.id,
                    "product_qty": new_consumption,
                    "product_uom_id": updated_product.uom_id.id,
                })
                _logger.info(f"Nova linha de BOM criada para FABRIC {fabric_identifier}: {updated_product.name} - {new_consumption} {updated_product.uom_id.name}.")
        
        # Remover quaisquer linhas de tecido originais que não foram processadas
        unprocessed_lines = [
            line for fid, line in existing_fabric_bom_lines_map.items()
            if fid not in variant_info
        ]
        if unprocessed_lines:
            for line in unprocessed_lines:
                _logger.info(f"Linha de BOM para FABRIC {line.product_id.product_tmpl_id.fabric_identifier_id} removida porque não foi processada.")
                line.unlink()

        # Bloco para atualizar as descrições na MO para rastreabilidade (sem alterar dados mestre)
        try:
            detailed_description_string = self._build_detailed_description(variant_info, production, client_supplied_fabrics)
            
            new_description_parts = []
            original_description = production.product_description_variants or ''
            new_description_parts.append(original_description)
            new_description_parts.append("\n\n--- DETALHES DE CONSUMO PROCESSADO ---")

            for fabric_num in sorted(variant_info.keys()):
                data = variant_info[fabric_num]
                subvariant_name = data['subvariant_name']
                if subvariant_name.lower() == 'nenhum':
                    continue
                origin_text = data.get('origin', 'N/A')
                label = data['label']
                line = f"FABRIC USED IN {fabric_num}: {subvariant_name} ({origin_text}): {label}"
                new_description_parts.append(line)

            final_mo_description = "\n".join(new_description_parts)
            
            production.write({
                'product_description_variants': final_mo_description,
                'fabric_consumption_info': detailed_description_string,
            })
            _logger.info(f"Descrições da MO {production.name} atualizadas para rastreabilidade, sem alterar o produto final.")

        except Exception as e:
            _logger.error(f"Erro ao construir/atualizar descrição para rastreabilidade: {str(e)}")

        _logger.info(f"DEBUG: Final BOM lines in duplicated BOM: {[f'{l.product_id.name} (Qty: {l.product_qty})' for l in bom.bom_line_ids]}")
        return "\n".join(consumption_info)

    
    def _create_fabric_product_for_mo_safe(self, original_product, new_name, production_name, subvariant_name, label):
        """
        FUNÇÃO FINAL CORRIGIDA: Cria um novo produto de tecido de forma segura,
        garante que as rotas de compra estão definidas e copia os fornecedores do
        produto original para permitir a geração automática de Ordens de Compra.
        """
        _logger.info(f"DEBUG: Início da criação segura de produto para MO: {new_name}")

        original_product_tmpl = original_product.product_tmpl_id
        new_product_tmpl_name = f"{original_product_tmpl.name} - {subvariant_name}: {label}"

        # 1. Procura ou cria o TEMPLATE do produto
        # É mais seguro procurar pelo nome para reutilizar templates se a configuração for idêntica
        new_product_tmpl = self.env['product.template'].search([('name', '=', new_product_tmpl_name)], limit=1)

        if not new_product_tmpl:
            _logger.info(f"Template '{new_product_tmpl_name}' não encontrado. Criando um novo.")
            
            # Define as rotas 'Comprar' e 'MTO'
            route_mto = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)
            route_buy = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)
            routes_to_set = [route.id for route in [route_mto, route_buy] if route]

            new_product_tmpl_vals = {
                'name': new_product_tmpl_name,
                'active': True,
                'type': 'product',
                'purchase_ok': True,
                'sale_ok': False,
                'is_fabric': True,
                'fabric_identifier_id': original_product_tmpl.fabric_identifier_id,
                'uom_id': original_product_tmpl.uom_id.id,
                'uom_po_id': original_product_tmpl.uom_po_id.id,
                'route_ids': [(6, 0, routes_to_set)],
                'categ_id': original_product_tmpl.categ_id.id, # Herda a categoria do produto
            }
            new_product_tmpl = self.env['product.template'].create(new_product_tmpl_vals)

            # Copia as tabelas de consumo do template original
            new_fabric_variants = [
                (0, 0, fv.copy_data()[0]) for fv in original_product_tmpl.fabric_variant_ids
            ]
            if new_fabric_variants:
                new_product_tmpl.write({'fabric_variant_ids': new_fabric_variants})
                _logger.info(f"Copiadas {len(new_fabric_variants)} tabelas de consumo para o novo template.")
        else:
            _logger.info(f"Template '{new_product_tmpl_name}' já existente. Reutilizando.")

        # 2. Procura ou cria o PRODUTO (product.product) associado ao template
        # Usamos with_context(active_test=False) para encontrar produtos arquivados e reativá-los
        updated_product = self.env['product.product'].with_context(active_test=False).search([
            ('product_tmpl_id', '=', new_product_tmpl.id)
        ], limit=1)

        if not updated_product:
            updated_product = self.env['product.product'].create({'product_tmpl_id': new_product_tmpl.id})
            _logger.info(f"Novo product.product criado: {updated_product.name} (ID: {updated_product.id})")
        
        # Garante que o produto está ativo
        if not updated_product.active:
            updated_product.action_unarchive()

        # 3. Copia os fornecedores do produto original para o novo produto
        # Este é o passo que resolve o erro "Não há preço de fornecedor".
        self._copy_suppliers_to_product(original_product, updated_product)

        _logger.info(f"Produto de tecido '{updated_product.name}' (ID: {updated_product.id}) pronto para uso.")
        return updated_product


    def _copy_suppliers_to_product(self, source_product, target_product):
        """
        NOVA FUN��O: Copia fornecedores do produto original para o produto duplicado.
        """
        if not source_product.seller_ids:
            _logger.warning(f"Produto original {source_product.name} n�o tem fornecedores definidos")
            return
        
        for supplier in source_product.seller_ids:
            # Verifica se j� existe este fornecedor no produto de destino
            existing_supplier = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', target_product.product_tmpl_id.id),
                ('partner_id', '=', supplier.partner_id.id)
            ], limit=1)
            
            if not existing_supplier:
                supplier.copy({
                    'product_tmpl_id': target_product.product_tmpl_id.id,
                    'product_id': target_product.id,
                })
                _logger.info(f"Fornecedor {supplier.partner_id.name} copiado para produto {target_product.name}")

    def _create_consignment_receipt(self, production, product, quantity):
        """
        Cria uma recepção de consignação (stock.picking) para tecidos fornecidos pelo cliente.

        Esta rotina procura o local de destino "FABRIC COM" e um tipo de operação de Recepção
        (picking_type) adequado ao armazém da ordem de fabrico. Em seguida, cria um picking
        com uma linha de movimento para o tecido e quantidade especificados. O proprietário
        (owner_id) é definido com base no cliente associado à ordem de venda (quando possível).

        :param production: registo de mrp.production para o qual está a ser criado o recibo
        :param product: produto de tecido a ser movimentado
        :param quantity: quantidade a receber em consignação
        :return: o registo stock.picking criado
        """
        # Não criar movimentos para quantidades nulas ou negativas
        if not quantity or quantity <= 0:
            return False

        # Local de destino: procura pelo nome completo que contenha 'FABRIC COM'
        dest_loc = self.env['stock.location'].search([
            ('complete_name', 'ilike', 'FABRIC COM'),
            ('usage', '=', 'internal')
        ], limit=1)
        if not dest_loc:
            raise UserError(_("Local de destino para tecidos consignados ('FABRIC COM') não encontrado."))

        # Determinar o tipo de picking para recepção (incoming) no armazém da MO
        warehouse = False
        if getattr(production, 'picking_type_id', False):
            warehouse = production.picking_type_id.warehouse_id
        picking_type_domain = [('code', '=', 'incoming')]
        if warehouse:
            picking_type_domain.append(('warehouse_id', '=', warehouse.id))
        picking_type = self.env['stock.picking.type'].search(picking_type_domain, limit=1)
        if not picking_type:
            # fallback para qualquer tipo de recepção
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        if not picking_type:
            raise UserError(_("Tipo de recepção (incoming) não encontrado."))

        # Determinar o parceiro (owner) com base na origem da MO (nome da SO) se existir
        partner = False
        try:
            if production.origin:
                sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
                if sale_order:
                    partner = sale_order.partner_id
        except Exception:
            partner = False

        # Procurar um recibo existente para a mesma encomenda (sale.order) ou, em
        # última instância, para a mesma ordem de fabrico. O objectivo é agrupar
        # todos os tecidos fornecidos pelo cliente num único recebimento por
        # encomenda. Se existir uma origem de venda (production.origin), ela será
        # utilizada como chave para o recibo; caso contrário, recorre-se ao nome
        # da MO.
        origin_key = production.origin or production.name
        picking = self.env['stock.picking'].search([
            ('origin', '=', origin_key),
            ('location_dest_id', '=', dest_loc.id),
            ('picking_type_id', '=', picking_type.id),
        ], limit=1)

        if not picking:
            # Criar o picking de recepção se ainda não existir
            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': dest_loc.id,
                # A origem do picking será a encomenda (sale.order) se existir;
                # isto permite agrupar todos os tecidos CLIENTE por encomenda.
                'origin': origin_key,
            }
            # Define o owner apenas se houver parceiro
            if partner:
                picking_vals['owner_id'] = partner.id
                picking_vals['partner_id'] = partner.id
            picking = self.env['stock.picking'].create(picking_vals)

        # Criar movimento de stock
        move_vals = {
            'name': product.display_name,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product.uom_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': dest_loc.id,
            'picking_id': picking.id,
            # o campo owner_id não é suportado em algumas versões de stock.move; não o definimos aqui
        }
        # Criar movimento sem owner_id (evita erro Invalid field 'owner_id')
        self.env['stock.move'].create(move_vals)

        _logger.info(
            f"Recibo de consignação criado para {product.display_name} (Qty: {quantity}) no picking {picking.name if hasattr(picking, 'name') else picking.id}"
        )
        return picking

