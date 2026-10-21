#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar a estrutura do arquivo BIM Excel
"""

import openpyxl
from datetime import datetime

def analyze_bim_file(file_path):
    """Analisa o arquivo BIM para identificar campos importantes"""
    
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    
    print("="*60)
    print("ANÁLISE DO ARQUIVO BIM")
    print("="*60)
    
    # Mostra as primeiras 20 linhas para entender o cabeçalho
    print("\n[CABEÇALHO - Primeiras 20 linhas]")
    print("-"*60)
    for row_num, row in enumerate(sheet.iter_rows(min_row=1, max_row=20, values_only=True), 1):
        # Filtra células vazias para melhor visualização
        non_empty = [str(cell) if cell is not None else '' for cell in row[:8]]
        if any(non_empty):  # Só mostra linhas que têm conteúdo
            print(f"Linha {row_num:2}: {non_empty}")
    
    # Procura por saldo inicial
    print("\n[PROCURANDO SALDO INICIAL]")
    print("-"*60)
    for row_num, row in enumerate(sheet.iter_rows(min_row=1, max_row=15, values_only=True), 1):
        for col_num, cell in enumerate(row[:8], 1):
            if cell and isinstance(cell, str):
                if 'saldo' in cell.lower() and 'inicial' in cell.lower():
                    print(f"Encontrado 'Saldo Inicial' na linha {row_num}, coluna {col_num}")
                    # Procura o valor na mesma linha
                    for i, val in enumerate(row[col_num:], col_num+1):
                        if val and (isinstance(val, (int, float)) or (isinstance(val, str) and any(c.isdigit() for c in val))):
                            print(f"  Valor possível: {val} na coluna {i}")
                elif 'opening' in cell.lower() or 'abertura' in cell.lower():
                    print(f"Encontrado possível saldo inicial: '{cell}' na linha {row_num}, coluna {col_num}")
    
    # Identifica onde começam as transações
    print("\n[IDENTIFICANDO INÍCIO DAS TRANSAÇÕES]")
    print("-"*60)
    header_keywords = ['data', 'date', 'descrição', 'description', 'débito', 'debit', 'crédito', 'credit', 'saldo', 'balance']
    for row_num, row in enumerate(sheet.iter_rows(min_row=1, max_row=20, values_only=True), 1):
        if row and row[0]:
            row_str = ' '.join(str(cell).lower() for cell in row[:8] if cell)
            if any(keyword in row_str for keyword in header_keywords):
                print(f"Possível cabeçalho de transações na linha {row_num}:")
                print(f"  Colunas: {[str(cell) for cell in row[:8] if cell]}")
                
                # Mostra a primeira transação
                next_row = sheet[row_num + 1]
                first_trans = [cell.value for cell in next_row[:8]]
                print(f"  Primeira transação (linha {row_num + 1}): {first_trans}")
                break
    
    # Identifica a última transação
    print("\n[ÚLTIMA TRANSAÇÃO]")
    print("-"*60)
    last_data_row = None
    for row_num, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if row and row[0]:  # Se a primeira coluna tem dados
            # Verifica se parece com uma data
            if isinstance(row[0], datetime) or (isinstance(row[0], str) and '/' in str(row[0])):
                last_data_row = (row_num, row)
    
    if last_data_row:
        print(f"Última transação encontrada na linha {last_data_row[0]}:")
        print(f"  Dados: {[str(cell) for cell in last_data_row[1][:8] if cell]}")
    
    # Procura saldo final
    print("\n[PROCURANDO SALDO FINAL]")
    print("-"*60)
    if last_data_row:
        # Verifica nas últimas colunas da última transação (geralmente coluna de saldo)
        for i, cell in enumerate(last_data_row[1][3:8], 4):  # Começa da coluna 4
            if cell and isinstance(cell, (int, float)):
                print(f"Possível saldo final na coluna {i}: {cell}")
    
    # Mostra resumo da estrutura
    print("\n[RESUMO DA ESTRUTURA]")
    print("-"*60)
    print(f"Total de linhas: {sheet.max_row}")
    print(f"Total de colunas: {sheet.max_column}")
    
    wb.close()

if __name__ == "__main__":
    file_path = r"C:\Users\custodio.massingue\Downloads\docs\co.xlsx"
    analyze_bim_file(file_path)