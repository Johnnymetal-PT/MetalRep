# Guiões de diagnóstico e prova — EVOSTONE

Guiões usados entre 14 e 16 de setembro de 2026. Estavam só numa máquina; vieram
para aqui para a passagem ao Pedro fazer sentido fora dela.

O raciocínio de cada um está no cabeçalho do próprio ficheiro, e o contexto todo
no `PG_CONTEXT.md` da raiz, entradas de 14 a 16 de setembro.

---

## Como se corre

Os dois `.ps1` são os invólucros. Nada corre sem eles.

```powershell
# Leitura. Só SQL, e em transacção só-de-leitura.
powershell -NoProfile -ExecutionPolicy Bypass -File guioes\evo_ler.ps1 `
  -Alvo <id>@parametroglobaladmin-evostone.odoo.com `
  -Consulta "select count(*) from res_users"

# Python, em ensaio (não escreve nada)
powershell -NoProfile -ExecutionPolicy Bypass -File guioes\evo_agir.ps1 `
  -Alvo <id>@parametroglobaladmin-evostone.odoo.com `
  -Guiao guioes\evo_validar.py -Producao

# Python, a escrever em produção
... -Guiao guioes\<ficheiro>.py -Fase aplicar -Escrever -Producao -Confirmado "<quem autorizou>"
```

`-Confirmado` regista **quem autorizou a escrita**. Não é campo de preenchimento
automático: é o rasto de quem mandou mexer em produção.

O `-Alvo` leva o id do build no nome, e **o id muda a cada publicação no
Odoo.sh**. Quando o host deixar de resolver, é preciso ir buscar o novo à
interface do Odoo.sh — não é avaria.

---

## O que cada um faz

### Validação — corre estes primeiro

| guião | o que responde |
|---|---|
| `evo_validar.py` | 21 verificações do estado: correio, modelos de impressão, valorização, áreas de atuação, site, impostos dos artigos, efeitos colaterais. Deve dar **21/21**. |
| `evo_prova_documentos.py` | Renderiza os relatórios de compras, vendas, faturas, entregas e pagamentos. Deve dar **25 imprimem, 0 rebentam**. |
| `evo_prova_documentos2.py` | Os restantes 43 modelos. Os 7 que acusa **não são defeitos** — ver o cabeçalho. |

### Provas de cadeia

| guião | o que responde |
|---|---|
| `evo_prova_factura.py` | A cadeia de faturação de venda e de compra, com os lançamentos que produziria. |
| `evo_prova_isencao.py` | O imposto que sai conforme a origem do fornecedor: Turquia `0% EX`, Espanha `23% EU G`, Portugal `23%`. |
| `evo_prova_lotes.py` | Que um nome de lote gera várias chapas numeradas. É a demonstração para a sessão com a Maria. |
| `evo_recepcao_com_lote.py` | Receção completa da P00002 real. |
| `evo_prova_correccao_svl.py` | Corre a receção **sem** e **com** a correção do SVL, para mostrar que o problema era mesmo aquele. |
| `evo_prova_iban.py` | Que o IBAN sai impresso na ordem de compra e na fatura. |

Todos revertem a transação no fim. Nada fica gravado.

### Escrita

| guião | estado |
|---|---|
| `evo_impostos_encomendas.py` | **POR APLICAR.** Põe `0% EX` e `23% EU G` nas linhas da P00002 e P00001. Os totais não mudam — 33.863,04 € e 97,80 € — e o guião recusa-se a gravar se algum mudar. |
| `evo_contas_transferencia.py` | **POR APLICAR.** Repõe as contas do módulo `internal_transfer`, que apontam para o plano de contas antigo e fazem as Definições rebentar com «O registo não existe ou foi apagado». Reproduz o erro antes, e recusa-se a gravar se as Definições não abrirem depois. |
| `evo_categorias_custeio.py` | **POR APLICAR.** Tira o `pcmp` das categorias de artigo conforme o combinado na reunião de 16/09 — `Amostras` a custo médio, `Imobilizado` a preço padrão. Só corre enquanto houver 0 camadas de valorização e 0 existências; depois disso já não é um acerto de configuração. Exige `-Confirmado`. |
| `evo_impostos_artigos.py` | Já aplicado. Atribuiu o imposto de compra a 24 artigos, lendo-o dos defeitos da empresa. |
| `evo_iban.py` | Já aplicado. Criou a conta bancária, com três validações antes de escrever. |
| `evo_relatorios.py` | Atualiza os módulos de relatórios e prova a renderização. O Odoo.sh **não** atualiza módulos ao publicar: alterações de XML exigem isto, as de Python bastam-se com o reinício. |
| `evo_campos_factura.py` | Diagnóstico. Que campos os modelos de faturação pedem e não existem. |

---

## O que ficou de fora, de propósito

Os guiões de limpeza de dados de demonstração — `evo_limpar_demo_total.py` e
`evo_limpar_demo_final.py` — **não vieram**. Retiram as guardas de integridade
fiscal do `mh_base` e têm escrito no cabeçalho que nunca devem correr sobre
dados reais. Num repositório partilhado ficariam ao alcance de quem não sabe
disso. Continuam na máquina onde foram usados.

---

## Duas coisas que estes guiões me ensinaram, e que poupam tempo

**A contagem não prova; o documento prova.** A bateria deu 19/19 sobre uma base
onde a fatura de compra saía sem IVA. Foi a prova ponta-a-ponta que apanhou.

**Provar um documento não prova os outros.** A identidade dos modelos foi provada
numa ordem de compra, e três documentos de faturação não imprimiam de todo.
