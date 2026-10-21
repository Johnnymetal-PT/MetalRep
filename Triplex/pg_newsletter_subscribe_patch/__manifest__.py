{
    'name': 'Newsletter subscribe patch',
    'version': '1.0',
    'summary': 'Sanitiza os pedidos de subscrição da newsletter (whitelist de campos)',
    'description': """
Newsletter subscribe patch
==========================

Objetivo de negócio / segurança
-------------------------------
O formulário público de subscrição da newsletter recebe dados do visitante. Sem controlo,
um pedido manipulado poderia tentar definir campos arbitrários no `mailing.contact`. Este
módulo restringe o que é aceite a uma lista branca de campos.

Pré-requisitos
--------------
- Módulos: `website_mass_mailing`.
- Campo Studio `x_studio_user_category` em `mailing.contact` (se for usado no formulário).
- O formulário do website tem de enviar apenas os campos permitidos; qualquer outro é descartado.

Como funciona
-------------
Estende o controller standard `/website_mass_mailing/subscribe`:
- Define os campos permitidos: `email`, `name`, `x_studio_user_category`, `country_id`.
- Constrói um dicionário "limpo" só com esses campos, normaliza `country_id` para inteiro
  e limpa também `request.params` e `request.jsonrequest` (usados pelo handler base).
- Delega no handler standard apenas com os argumentos seguros.
- Importa a classe base de forma tolerante a diferenças de nome entre versões do Odoo
  (`MassMailController` / `WebsiteMassMailingController`).

Passo a passo de utilização
---------------------------
1. Garantir o campo Studio `x_studio_user_category` (se quiser usá-lo).
2. Adicionar o snippet de subscrição da newsletter à página do website.
3. Os pedidos a `/website_mass_mailing/subscribe` ficam sanitizados — qualquer payload com
   chaves fora da whitelist é silenciosamente removido.

Exemplo prático
---------------
Pedido manipulado com `{"email":"x@y.com","is_admin":True,"vat":"SEMPRE"}` -> o módulo
descarta `is_admin` e `vat`, criando o `mailing.contact` apenas com `email` (e os outros
campos válidos da whitelist).

FAQ / Resolução de problemas
----------------------------
- P: Adicionei um campo novo ao formulário e não está a ser gravado.
  R: Adicionar à whitelist `allowed_fields` no controller.
- P: Erro de importação `MassMailController`.
  R: Versões mais antigas do Odoo usam `WebsiteMassMailingController`; o módulo já tenta os
     dois nomes — verificar se a versão do `website_mass_mailing` mudou novamente.
- P: O campo `country_id` chega como string.
  R: O módulo converte para inteiro; se vier inválido, é descartado em vez de gerar erro.

Pontos de atenção
-----------------
- O campo Studio `x_studio_user_category` é específico deste projeto.
- Mudanças do Odoo no `subscribe` (assinatura/args) podem exigir revisar este override.
""",
    'category': 'Website',
    'depends': ['website_mass_mailing'],
    'data': [],
    'installable': True,
}
