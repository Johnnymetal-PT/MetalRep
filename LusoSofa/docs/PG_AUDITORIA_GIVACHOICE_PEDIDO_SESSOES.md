# Pedido de extração de sessões — auditoria de desempenho da framework (givachoice)

Para: **Nuno Oliveira** e **José Couto**
Contexto: estamos a auditar como é que a framework se comportou no givachoice — o único projeto que a adotou a meio da execução. O objeto da auditoria é **a framework, não o vosso trabalho**. O que se procura é onde é que ela induziu em erro, se calou, ou custou sem dar valor.

Não é preciso enviar transcrições: são centenas de MB. Cada um corre a extração na sua máquina e envia **um ficheiro markdown**.

## Como fazer

Abrir o Claude Code **na pasta do repositório givachoice** e colar a prompt abaixo, tal como está.

Se o Claude pedir autorização para ler ficheiros fora do repositório (a pasta das transcrições), autorizar — é só leitura.

---

## PROMPT PARA COLAR

```
Preciso de uma extração factual das minhas sessões antigas neste projeto, para uma
auditoria interna à framework. É trabalho de leitura apenas: não alteres nada no
repositório, não commites, não faças push, não corras nada contra o Odoo.

PASSO 1 — Localizar as minhas transcrições
As sessões do Claude Code vivem em ~/.claude/projects/<slug>/*.jsonl, onde <slug> é o
caminho do repositório com as barras trocadas por hífenes. Encontra a pasta que
corresponde a ESTE repositório (givachoice) e diz-me quantos ficheiros tem e que
intervalo de datas cobrem.

PASSO 2 — Contar conversas, não ficheiros
Uma conversa retomada gera ficheiros novos com as mesmas mensagens repetidas. Agrupa
os ficheiros que partilham as mesmas mensagens iniciais com carimbos temporais
idênticos e trata cada grupo como UMA conversa. Diz-me quantas conversas distintas há.

PASSO 3 — Selecionar o período
Interessam as conversas entre 2026-04-27 e 2026-08-10, com prioridade máxima para:
  (a) 2026-08-05  — a alteração ao relatório "Ver Ordem" do pg_giva_pdf_reports
  (b) 2026-07-31 a 2026-08-04 — a migração do Odoo 17 para 19 e os dias seguintes
  (c) qualquer conversa entre 2026-04-27 e 2026-07-30
Se não houver nada nesse período, diz isso claramente em vez de alargares por tua
iniciativa — a ausência também é resultado.

PASSO 4 — Para CADA conversa selecionada, extrai
  1. data, hora de início e fim, e o nome do ficheiro
  2. o que eu pedi, nas minhas palavras (cita as minhas mensagens, encurtadas; não
     parafraseies)
  3. o que foi efetivamente alterado: ficheiros, módulos, patches, escritas no Odoo
  4. **antes de alterar código existente, o agente estabeleceu o que esse código já
     fazia?** Cita a passagem que o mostra, ou escreve "NÃO ENCONTRADO"
  5. **houve alguma verificação de que o comportamento anterior estava validado pelo
     cliente?** Cita, ou "NÃO ENCONTRADO"
  6. **que versão do Odoo é que o agente assumiu?** Cita qualquer menção a versão,
     a documentação oficial citada, ou ao preflight. Interessa-me em especial se
     alguma sessão trabalhou assumindo 17.0
  7. o ritual de arranque da framework correu? O que é que o preflight reportou?
     Alguma vez travou ou avisou de alguma coisa que tenha mudado a decisão?
  8. momentos em que eu corrigi o rumo, repeti um pedido, ou disse que algo estava
     errado — cita-os
  9. sinais de que a framework atrapalhou: passos que não serviram para nada,
     informação do espelho que estava errada ou desatualizada, regras que
     obrigaram a trabalho sem retorno

PASSO 5 — Escrever o resultado
Grava em `auditoria_framework_<oteunome>.md` na raiz deste repositório, com um
cabeçalho que diga: o teu nome, a máquina, o intervalo coberto, quantos ficheiros e
quantas conversas distintas.

REGRAS
- Cita em vez de resumires. Uma citação curta com data vale mais do que um parágrafo teu.
- Onde não houver evidência, escreve "NÃO ENCONTRADO". Não infiras.
- Não julgues o trabalho de ninguém. O objeto é a framework.
- Não incluas credenciais, chaves de API nem dados pessoais de clientes. Se um excerto
  os contiver, corta essa parte e assinala com [omitido].
- Não alteres, não commites e não publiques nada.
```

---

## Depois

Enviar o `auditoria_framework_<nome>.md` ao Bruno. **Não commitar o ficheiro** — fica fora do repositório.

Se a extração devolver "não há conversas nesse período", isso é um resultado útil e deve ser comunicado na mesma: quer dizer que o período de adoção da framework não tem rasto em máquina nenhuma, e essa é uma conclusão por si só.
