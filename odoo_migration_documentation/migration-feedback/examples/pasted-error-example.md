# Exemplo de feedback colado no agente

```text
Estou a testar a instalação/migração de addons customizados Odoo 17 em Odoo 18.

Módulo testado:
custom_sale_margin

Fase:
instalação módulo

Comando executado:
odoo-bin -d teste18 -i custom_sale_margin --stop-after-init

Erro completo:
Element '<xpath expr="//field[@name='amount_total']">' cannot be located in parent view

Contexto funcional:
Tentativa de instalar o módulo custom de margem em vendas.

Resultado esperado:
O módulo deveria instalar e a view de venda deveria abrir normalmente.

Resultado obtido:
A instalação falha no carregamento da view herdada.

Pedido ao agente:
Documenta este erro seguindo AGENTS.md.
Não alteres código dos addons.
Atualiza apenas migration-docs/.
Se a causa raiz não for certa, marca como provável ou desconhecida.
Verifica se é duplicado de erro já existente.
No final, indica o MIG-XXXX criado/atualizado, severidade, camada técnica provável e próxima ação recomendada.
```
