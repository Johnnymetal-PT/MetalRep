# Email ao cliente — Comunicação de Inventário à AT

**Para:** Andreia Silva — Sofmovel | andreiasilva@sofmovel.pt
**Assunto:** Inventário em Excel — já sabemos o que se passa (e como resolver)

---

Olá Andreia, boa tarde 🙂

Obrigado pela paciência — fomos ver com calma o inventário que estava a tirar em Excel e já percebemos porque é que não batia certo com o "em mão".

Resumindo: o ecrã que estava a usar (*Inventário → Relatórios → Valorização → Valorização à Data*) mostra a **valorização contabilística do stock**, e não as quantidades físicas. São coisas diferentes, e na configuração atual não coincidem — daí os totais não fecharem. Nada que tenha feito de errado; é só que esse relatório serve para outra finalidade.

A boa notícia é que, para o **inventário anual das Finanças**, o Odoo tem uma ferramenta feita à medida:

> **Contabilidade → Relatórios → Portugal → Comunicação de Inventário**

É esta que gera o inventário à data que precisar (por ex. 31/12), já valorizado a custo e no formato que a AT aceita. Pode ainda tirá-lo em PDF ou Excel só para conferir antes.

Só um aviso útil: o ficheiro da AT **não aceita quantidades negativas**, e a própria ferramenta assinala esses casos. Vimos que há alguns produtos assim, por isso o melhor é darmos uma vista de olhos e acertar isso antes de gerar o ficheiro final — e nisso damos-lhe uma mãozinha.

Junto envio um **guia passo-a-passo** (PDF) para poder fazê-lo sozinha sempre que precisar.

Se quiser, marcamos uma call rápida (uns 30 min) para eu passar o guia consigo e combinarmos a correção daquelas quantidades — assim o próximo fecho fica bem mais simples. É só dizer-me quando lhe dá jeito.

Qualquer dúvida, estou por aqui.

Um abraço,

João Barros
Parâmetro Global
joao.barros@parametro.global

---

> **Notas internas (não enviar ao cliente):**
> - Causa-raiz técnica: custeio `standard` + valorização `manual_periodic` em 100% das categorias; a `stock.valuation.layer` está dessincronizada do stock físico (líquido valorizado ≈ −86.751 un vs stock físico ≈ +19,0 M un; entradas SVL 36.145 un vs saídas 122.896 un → stock inicial não valorizado em entradas). Ver `PG_CONTEXT.md` / tarefa 6456.
> - Prazo/obrigatoriedade legal da Comunicação de Inventário: `PONTO POR VALIDAR` com a contabilidade (regra geral: até final de janeiro, referente ao período anterior; obrigatório acima do limiar de volume de negócios legalmente definido).
> - Canal de submissão (Portal e-Fatura vs Dataport, módulo `ptplus_saft` instalado): `PONTO POR VALIDAR`.
