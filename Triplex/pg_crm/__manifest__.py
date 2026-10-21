{
    "name": "CRM Lead Quotation Cleanup",
    "version": "1.0",
    "summary": "Ao marcar um lead como perdido, apaga os orçamentos e documentos associados (AÇÃO DESTRUTIVA)",
    "description": """
CRM Lead Quotation Cleanup
==========================

AVISO IMPORTANTE (AÇÃO DESTRUTIVA E IRREVERSÍVEL)
-------------------------------------------------
Este módulo APAGA dados reais (faturas, entregas, OFs, linhas de compra) ao arquivar um lead.
Apagar faturas tem implicações legais/contabilísticas SÉRIAS. Não há confirmação ao
utilizador — basta arquivar o lead. Classificação consultiva: alto risco. Considerar
alternativas (cancelar em vez de apagar, restringir a rascunhos).

Objetivo de negócio
-------------------
Quando uma oportunidade (lead) é dada como perdida/arquivada, limpar automaticamente os
documentos comerciais que dela resultaram, para não ficarem orçamentos/documentos órfãos.

Pré-requisitos
--------------
- Módulos: `crm`, `sale`.
- Ler atentamente o AVISO acima ANTES de instalar em produção.
- Recomendado: ambiente de teste com cópia de dados reais; documentar processo com
  utilizadores; ter rotina de backup recente antes da arquivagem.
- Para evitar problemas legais com faturas já publicadas, considerar fortemente DESINSTALAR
  ou restringir o âmbito do método `_delete_related_records`.

Como funciona
-------------
Estende `crm.lead` e faz override do `write()`:
- Quando `active` passa a False (lead marcado como perdido), procura as `sale.order` ligadas
  (`opportunity_id`) e, para cada uma:
    * se estiver confirmada (state='sale'): desbloqueia, cancela, volta a rascunho e apaga
      os documentos relacionados via `_delete_related_records`;
    * apaga (unlink) o próprio orçamento.
- `_delete_related_records` apaga/cancela: faturas (account.move por `invoice_origin`),
  entregas (stock.picking por `origin`), ordens de fabrico (mrp.production por `origin`) e,
  nas compras (purchase.order por `origin`), apenas as LINHAS ligadas à venda (e a PO
  inteira se ficar sem linhas). Regista tudo em `ir.logging`.

Passo a passo de utilização
---------------------------
1. (Antes) Garantir backup recente e ler o aviso acima.
2. No CRM, marcar a oportunidade como perdida ou arquivá-la (active=False).
3. O sistema, sem confirmação, apaga TODOS os documentos derivados (orçamentos, faturas,
   entregas, OFs, linhas de PO).
4. Consultar `ir.logging` para auditoria do que foi apagado.

Exemplo prático
---------------
Lead "Oportunidade X" com orçamento confirmado SO/0010 (com fatura, picking e MO criados):
ao arquivar a oportunidade, o orçamento volta a rascunho, é cancelado e apagado; a fatura,
o picking e a MO são também apagados; as linhas da PO ligadas à venda são removidas (a PO
fica sem essas linhas, sendo apagada se ficar vazia).

FAQ / Resolução de problemas
----------------------------
- P: Posso recuperar o que foi apagado?
  R: Não, é irreversível. Restaurar de backup.
- P: Algumas faturas não foram apagadas.
  R: Algumas têm restrições legais/contabilísticas no Odoo (não permite unlink). O módulo
     captura exceções e regista em `ir.logging`.
- P: Quero só cancelar (não apagar).
  R: Adaptar/desligar o método `_delete_related_records` para apenas cancelar.

Pontos de atenção
-----------------
- Ação destrutiva sem confirmação no UI.
- Apagar faturas pode violar requisitos legais (SAF-T, AT em Portugal).
- Recomendado validar com contabilidade antes de ativar em produção.
""",
    "depends": ["crm", "sale"],
    "data": [],
    "installable": True,
    "application": False,
}
