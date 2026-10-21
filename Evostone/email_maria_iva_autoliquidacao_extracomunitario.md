---
assunto: Confirmação necessária — IVA de autoliquidação extracomunitário — EVOSTONE
para: Maria Dias — financeiro@evostone.eu
---

Exma. Sra. Dra. Maria Dias,

No seguimento da vossa questão sobre a fatura de um serviço com IVA de autoliquidação, verificámos que o Odoo da EVOSTONE não tem hoje um imposto próprio para serviços prestados a clientes empresariais fora da União Europeia.

**Situação atual**

Os impostos de IVA a 0% disponíveis para vendas são estes:

| Imposto | Região | Código | Utilização prevista |
|---|---|---|---|
| IVA 0% INTRAC. (OBS) | Intracomunitária | M40 | Serviços a empresas da UE |
| IVA 0% EXTRAC. (OBS, Imob., Exist.) | Extracomunitária | M05 | Exportação de bens |

Um serviço a uma empresa fora da UE não encaixa bem em nenhum dos dois. O M05 destina-se a exportações de bens. O M40 existente está configurado como intracomunitário, pelo que a operação seria associada ao quadro da declaração periódica das operações intracomunitárias, e não ao das extracomunitárias.

**A nossa sugestão**

Sugerimos criar um novo imposto, com a designação "IVA 0% EXTRAC. (OBS) (M40)", com as seguintes características:

- região extracomunitária;
- motivo de isenção M40 (autoliquidação);
- associação ao quadro das operações extracomunitárias da declaração periódica (Q06-C8), tal como já acontece com os restantes impostos extracomunitários.

**O que precisamos de vós**

Esta é apenas uma sugestão nossa. A Parametro Global é responsável pela configuração do Odoo, mas não presta aconselhamento fiscal ou contabilístico, e o enquadramento de IVA correto para cada operação é uma decisão da EVOSTONE. Por isso, não avançamos sem a vossa validação: só criaremos este imposto depois de recebermos, por escrito, a vossa confirmação de que é isso mesmo que pretendem.

Pedimos-vos, por favor, que respondam a este email a confirmar:

1. que o código M40 é o correto para os serviços prestados a empresas fora da UE que pretendem faturar;
2. que a região extracomunitária e a associação ao quadro Q06-C8 estão corretas, ou qual a associação que devem ter;
3. que querem que criemos o imposto com as características acima.

Se o enquadramento correto for outro, indiquem-nos qual, e configuramos conforme as vossas instruções.

Até recebermos esta confirmação, não alteramos a configuração de impostos em produção.
