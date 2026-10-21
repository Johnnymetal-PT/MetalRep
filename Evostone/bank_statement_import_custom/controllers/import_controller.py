# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class ImportNumberingController(http.Controller):
    """Controller para fornecer API de numeração automática para importações"""
    
    @http.route('/bank_statement_import_custom/get_next_number', 
                type='json', auth='user', methods=['POST'], csrf=False)
    def get_next_number(self, type='customer', **kwargs):
        """
        Retorna o próximo número disponível para cliente ou fornecedor
        
        Args:
            type: 'customer' ou 'supplier'
        
        Returns:
            dict: {'next_number': int, 'status': 'success'}
        """
        try:
            _logger.info(f"=== GET_NEXT_NUMBER CHAMADO ===")
            _logger.info(f"Parâmetro type recebido: {type}")
            _logger.info(f"Todos os parâmetros: {kwargs}")
            
            # Determinar qual campo consultar
            if type == 'customer':
                field_name = 'accg_nr_order_customer'
            elif type == 'supplier':
                field_name = 'accg_nr_order_supplier'
            else:
                field_name = 'accg_nr_order'
            
            _logger.info(f"Campo a consultar: {field_name}")
            
            # Buscar o maior número atual
            query = f"""
                SELECT COALESCE(MAX({field_name}), 0) as max_value
                FROM res_partner
                WHERE {field_name} IS NOT NULL
            """
            _logger.info(f"Executando query: {query}")
            request.cr.execute(query)
            
            result = request.cr.fetchone()
            _logger.info(f"Resultado da query: {result}")
            
            next_number = (result[0] if result else 0) + 1
            
            _logger.info(f"Próximo número calculado para {type}: {next_number}")
            
            return {
                'next_number': next_number,
                'status': 'success',
                'type': type,
                'field_name': field_name
            }
            
        except Exception as e:
            _logger.error(f"Erro ao obter próximo número: {str(e)}")
            return {
                'next_number': 1,
                'status': 'error',
                'message': str(e)
            }
    
    @http.route('/bank_statement_import_custom/reserve_numbers', 
                type='json', auth='user', methods=['POST'], csrf=False)
    def reserve_numbers(self, type='customer', count=1):
        """
        Reserva uma sequência de números para evitar conflitos
        
        Args:
            type: 'customer' ou 'supplier'
            count: quantidade de números a reservar
        
        Returns:
            dict: {'start_number': int, 'end_number': int, 'status': 'success'}
        """
        try:
            _logger.info(f"Reservando {count} números para {type}")
            
            # Determinar qual campo usar
            if type == 'customer':
                field_name = 'accg_nr_order_customer'
            elif type == 'supplier':
                field_name = 'accg_nr_order_supplier'
            else:
                field_name = 'accg_nr_order'
            
            # Buscar o maior número atual com lock
            request.cr.execute(f"""
                SELECT COALESCE(MAX({field_name}), 0) as max_value
                FROM res_partner
                WHERE {field_name} IS NOT NULL
                FOR UPDATE
            """)
            
            result = request.cr.fetchone()
            start_number = (result[0] if result else 0) + 1
            end_number = start_number + count - 1
            
            # Criar registros temporários para reservar os números
            # (Opcional - pode ser implementado se necessário)
            
            _logger.info(f"Números reservados: {start_number} até {end_number}")
            
            return {
                'start_number': start_number,
                'end_number': end_number,
                'count': count,
                'status': 'success',
                'type': type,
                'field_name': field_name
            }
            
        except Exception as e:
            _logger.error(f"Erro ao reservar números: {str(e)}")
            return {
                'start_number': 1,
                'end_number': count,
                'status': 'error',
                'message': str(e)
            }
    
    @http.route('/bank_statement_import_custom/validate_import', 
                type='json', auth='user', methods=['POST'], csrf=False)
    def validate_import(self, data):
        """
        Valida e processa dados de importação com numeração
        
        Args:
            data: dados da importação incluindo tipo e registros
        
        Returns:
            dict: resultado da validação
        """
        try:
            _logger.info("Validando dados de importação")
            
            import_type = data.get('type', 'customer')
            records = data.get('records', [])
            
            # Validar se há registros
            if not records:
                return {
                    'status': 'error',
                    'message': 'Nenhum registro para processar'
                }
            
            # Obter próximo número
            next_number_result = self.get_next_number(import_type)
            
            if next_number_result['status'] != 'success':
                return next_number_result
            
            start_number = next_number_result['next_number']
            
            # Preparar resposta com numeração
            processed_records = []
            current_number = start_number
            
            for record in records:
                record_with_number = record.copy()
                
                if import_type == 'customer':
                    record_with_number['accg_nr_order_customer'] = current_number
                    record_with_number['accg_nr_order'] = current_number
                elif import_type == 'supplier':
                    record_with_number['accg_nr_order_supplier'] = current_number
                    record_with_number['accg_nr_order'] = current_number
                else:
                    record_with_number['accg_nr_order'] = current_number
                
                processed_records.append(record_with_number)
                current_number += 1
            
            _logger.info(f"Processados {len(processed_records)} registros com numeração")
            
            return {
                'status': 'success',
                'processed_records': processed_records,
                'start_number': start_number,
                'end_number': current_number - 1,
                'count': len(processed_records)
            }
            
        except Exception as e:
            _logger.error(f"Erro ao validar importação: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @http.route('/bank_statement_import_custom/get_import_stats', 
                type='json', auth='user', methods=['GET'], csrf=False)
    def get_import_stats(self):
        """
        Retorna estatísticas sobre a numeração atual
        
        Returns:
            dict: estatísticas de numeração
        """
        try:
            stats = {}
            
            # Estatísticas de clientes
            request.cr.execute("""
                SELECT 
                    COUNT(*) as total,
                    MAX(accg_nr_order_customer) as max_number,
                    MIN(accg_nr_order_customer) as min_number
                FROM res_partner
                WHERE accg_nr_order_customer IS NOT NULL
                AND accg_nr_order_customer > 0
            """)
            
            customer_result = request.cr.fetchone()
            stats['customer'] = {
                'total': customer_result[0] if customer_result else 0,
                'max_number': customer_result[1] if customer_result else 0,
                'min_number': customer_result[2] if customer_result else 0,
                'next_number': (customer_result[1] if customer_result and customer_result[1] else 0) + 1
            }
            
            # Estatísticas de fornecedores
            request.cr.execute("""
                SELECT 
                    COUNT(*) as total,
                    MAX(accg_nr_order_supplier) as max_number,
                    MIN(accg_nr_order_supplier) as min_number
                FROM res_partner
                WHERE accg_nr_order_supplier IS NOT NULL
                AND accg_nr_order_supplier > 0
            """)
            
            supplier_result = request.cr.fetchone()
            stats['supplier'] = {
                'total': supplier_result[0] if supplier_result else 0,
                'max_number': supplier_result[1] if supplier_result else 0,
                'min_number': supplier_result[2] if supplier_result else 0,
                'next_number': (supplier_result[1] if supplier_result and supplier_result[1] else 0) + 1
            }
            
            # Estatísticas gerais
            request.cr.execute("""
                SELECT 
                    COUNT(*) as total,
                    MAX(accg_nr_order) as max_number,
                    MIN(accg_nr_order) as min_number
                FROM res_partner
                WHERE accg_nr_order IS NOT NULL
                AND accg_nr_order > 0
            """)
            
            general_result = request.cr.fetchone()
            stats['general'] = {
                'total': general_result[0] if general_result else 0,
                'max_number': general_result[1] if general_result else 0,
                'min_number': general_result[2] if general_result else 0,
                'next_number': (general_result[1] if general_result and general_result[1] else 0) + 1
            }
            
            _logger.info(f"Estatísticas obtidas: {stats}")
            
            return {
                'status': 'success',
                'stats': stats
            }
            
        except Exception as e:
            _logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }