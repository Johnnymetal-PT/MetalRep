# Sessão 2 — Artigos e CRM

**Cliente:** JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA · **Projeto:** Implementação Odoo · **Data:** 10/2026 · **Formadora:** Lara Cunha (Parâmetro Global)

> A interface do Odoo está em português do Brasil. Os nomes de menus e botões aparecem **a negrito, exatamente como no ecrã**.

## O que se vai ver e porquê

Os **artigos** (produtos e serviços) são a base de tudo: aparecem nos orçamentos, nas compras e nas faturas. O **CRM** é onde se acompanha cada potencial cliente, desde o primeiro contacto até à decisão — para nenhum pedido ficar esquecido.

## Antes → depois

| Hoje | No Odoo |
|---|---|
| Preços e fornecedores em listas separadas | Cada artigo tem preço de venda, custo e fornecedor habitual |
| Pedidos de clientes em emails e notas | Cada pedido é uma oportunidade com fase, valor esperado e próxima ação |

## Parte A — Criar um artigo

Menu: **Vendas › Produtos › Produtos** → **Novo**.

1. **Nome** — como deve aparecer no orçamento ao cliente (ex.: «Sofá 3 lugares — linho natural»).
2. Marcar **Vendas** (pode ser vendido) e/ou **Compras** (pode ser comprado).
3. Separador **Informações gerais** → **Tipo de produto**:
   - **Mercadorias** — mobiliário, iluminação, materiais. Ativar **Rastrear inventário** só se quiserem controlar stock em armazém.
   - **Serviço** — projeto de design, desenho técnico, 3D, acompanhamento, montagem.
4. **Preços de venda** (sem IVA) e **Custo**.
5. **Categoria de produtos**: Mercadorias, Serviços ou Despesas.
6. **Unidade**: Unidades, m², m, Horas, …
7. **Referência interna** (código do artigo), opcional.
8. Separador **Compras** → adicionar o fornecedor habitual e o preço dele.

**Serviços que criam projeto:** num artigo **Serviço**, o campo **Criar no pedido** define o que acontece ao confirmar o orçamento. Já existe o serviço **«Projeto de design de interiores»**, configurado para criar automaticamente o projeto do cliente a partir do modelo **«Geral»** (com as fases da empresa).

## Parte B — Acompanhar oportunidades no CRM

Menu: **CRM › Vendas › Meu funil**. Cada coluna é uma fase: **Novo → Qualificado → Proposta → Ganho**.

1. **Novo** → nome (ex.: «Remodelação sala — Maria Silva»), **Contato**, **Receita esperada**.
2. Abrir o cartão e completar: **Vendedor**, **Fechamento esperado**, **Prioridade** (estrelas), notas do que o cliente pediu.
3. Agendar a próxima ação (ícone do relógio): visita, chamada, reunião.
4. Arrastar o cartão de fase à medida que avança.
5. Para propor: **Nova cotação** — o orçamento fica ligado à oportunidade (sessão 3).
6. No fim: **Ganho** ou **Perdido** (com o motivo).

## Exercício

1. Abrir o artigo de serviço «Projeto de design de interiores» e ver o campo **Criar no pedido** e o **Modelo de projeto**.
2. Criar um artigo de mercadoria com fornecedor.
3. Abrir a **«Oportunidade da Adélia Reis»** (já existe), preencher a **Receita esperada** e agendar a próxima ação.

## O que o Odoo passa a dar

- Funil com o valor das propostas em curso (**Relatórios › Funil de vendas** e **Previsão**).
- Histórico de todas as conversas com cada cliente.
- Preços e fornecedores propostos automaticamente nos orçamentos e compras.

## O que fica fora e o que falta decidir

- `[POR VALIDAR]` Categorias de artigos: a base tem Mercadorias, Serviços e Despesas; subcategorias (ex.: Iluminação, Têxteis) a decidir.
- Os artigos e contactos do inventário serão importados pela Parâmetro Global a partir dos ficheiros enviados.

## Próximos passos

1. Enviar o inventário de artigos e os contactos para importação.
2. Registar no CRM todos os pedidos novos a partir desta semana.
