# Overall migration summary

## Estado atual

- Erros documentados: 8
- Versão origem: Odoo 17.0
- Versão destino do piloto: Odoo 18.0
- Instalação/update: todos os módulos instalaram com sucesso após as correções documentadas.
- Validação exploratória: Click Everywhere concluído sem novos erros após classificar a perda de imagem `MIG-0008`.
- Validação funcional específica: ainda recomendada para os fluxos custom críticos.

## Erros registados

- MIG-0001: `pg_sale_salesperson` e `pg_tecidos` apareciam presos em instalação; causa confirmada foi falta do caminho dos addons custom no `addons_path` do `odoo.conf`; reteste OK.
- MIG-0002: `odoo-bin` não estava disponível no `PATH` do servidor Linux; o comando real do serviço `odoo18` foi identificado.
- MIG-0003: registry falhava ao carregar `base_view_inheritance_extension` por falta da dependência Python `astor`; reteste OK.
- MIG-0004: warning `BD_Geral: not installable, skipped`.
- MIG-0005: instalação de `pg_packing_list_custom` falhava porque o XPath procurava `move_ids_without_package/tree`; corrigido para `move_ids_without_package/list`; reteste OK.
- MIG-0006: `pg_tecidos` gerava logs INFO repetidos em `stock.move.write` quando `partner_id` não mudava; corrigido para DEBUG.
- MIG-0007: instalação de `pg_multi_discount` falhava porque o XPath procurava `order_line/tree`; corrigido para `order_line/list` e aplicado também a faturas/vendas do módulo; reteste OK.
- MIG-0008: Click Everywhere encontrou `FileNotFoundError` ao carregar imagem de `product.template`; ficheiro confirmado como perdido e classificado como não bloqueante.

## Causas raiz

- RC-0001: `addons_path` do Odoo 18 não incluía o caminho dos addons custom.
- RC-0002: Odoo 18 corre via serviço systemd com comando explícito, sem `odoo-bin` no `PATH`.
- RC-0003: `astor` não estava instalado no venv do Odoo 18.
- RC-0004: módulo `BD_Geral` é referenciado, mas não há evidência de addon instalável no repositório piloto.
- RC-0005: subviews one2many em Odoo 18 usam `list` em vez de `tree`, quebrando XPaths herdados.
- RC-0006: condição normal em `stock.move.write` era registada como INFO em vez de DEBUG.
- RC-0007: BD migrada contém anexos de imagem para `product.template` 8639, mas pelo menos o ficheiro físico de `image_128` não existe no filestore restaurado.

## Próxima ação

Executar validações funcionais específicas dos fluxos custom mais críticos contra Odoo 17: packing list em transferências, descontos múltiplos em compras/faturas, fluxos de tecidos/produção e perfis de segurança.
