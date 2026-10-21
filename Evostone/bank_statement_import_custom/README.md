# Bank Statement Import Custom

## Descrição
Módulo personalizado para importação automática de extratos bancários com formatação inteligente baseada no banco selecionado.

## Funcionalidades
✅ Interceptação do processo de importação padrão  
✅ Seleção de banco (BIM, BCI)  
✅ Parser automático para extratos BIM  
✅ Formatação automática de dados  
✅ Integração com fluxo padrão do Odoo  

## Como Funciona
1. Usuário clica em "Import records" na reconciliação bancária
2. Na tela de importação, clica em "Upload Data File"
3. Wizard personalizado abre com seleção de banco
4. Usuário seleciona banco (BIM/BCI) e faz upload do arquivo
5. Sistema formata automaticamente o arquivo
6. Continua com importação padrão do Odoo

## Bancos Suportados
- **BIM** (Millennium BIM) - ✅ Implementado
  - Remove cabeçalho (11 primeiras linhas)
  - Processa transações a partir da linha 12
  - Suporta XLSX, XLS e CSV
- **BCI** - 🚧 Em desenvolvimento

## Como Testar
1. Acesse http://localhost:8069 (admin/admin)
2. Vá para **Faturamento > Diários**
3. Selecione um diário bancário
4. Clique em **"Transactions"** ou **"Reconcile"**
5. Clique em **"Import records"**
6. Na tela de importação, clique em **"Upload Data File"**
7. Selecione o banco e faça upload do extrato

## Estrutura Principal
```
├── models/
│   ├── base_import.py         # Interceptação
│   └── bim_parser.py          # Parser BIM
├── wizard/
│   └── bank_statement_import_wizard.py  # Wizard principal
└── tests/
    └── sample_bim_statement.csv         # Arquivo exemplo
```

## Documentação Completa
Veja [DOCUMENTACAO_COMPLETA.md](DOCUMENTACAO_COMPLETA.md) para detalhes técnicos.

## Licença
LGPL-3