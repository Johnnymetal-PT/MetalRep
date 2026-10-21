# TPL_JANELA_MANUTENCAO

Guião de uma janela de manutenção: implantar código ou configuração num servidor de cliente, com travão antes, prova depois e caminho de volta.

Cumpre a regra obrigatória "Implantar código no servidor de um cliente" do `AGENTS_SHARED.md`. Cada secção abaixo é um dos passos dessa regra; nenhuma é opcional.

Origem: promovido a 2026-09-11 a partir dos guiões reais do givachoice, que já usavam esta estrutura. Não foi desenhado de raiz.

---

## 1. O que muda

Um bloco por patch. Para cada um:

- **o módulo e o ficheiro** que muda;
- **o comportamento antes** e **o comportamento depois**, em linguagem de quem usa;
- **quem pediu**. Se não se encontrou origem, escrever que não se encontrou — nunca assumir que não existe. É o passo 1 da regra "Antes de alterar o que já funciona";
- **classificação**: defeito / decisão do cliente / decisão nossa por documentar.

> Uma correção que ninguém pediu passa uma barra **mais alta**, não mais baixa por ser pequena.

## 2. Linha de base — o travão

Antes de tocar em nada, registar o estado exacto do destino. É isto que impede sobrepor trabalho que outra pessoa publicou entretanto.

| | valor |
|---|---|
| série do Odoo no destino | (do módulo `base`, lida do próprio destino) |
| md5 de cada ficheiro a substituir | |
| versão em disco de cada módulo | |
| contagens relevantes (`ir.model.data`, vistas, campos) | |
| módulos pendentes de atualização | |

**Se qualquer md5 não bater no momento da execução, abortar sem copiar nada.**

A série confirma-se contra o próprio destino, nunca contra o que se julga:

```powershell
py .pg_framework\scripts\pg_compare_client_addons.py --project-key <key> --purpose <purpose> --serie-esperada <serie>
```

`FACTO OBSERVADO` (givachoice): foi a ausência deste travão que pôs código v17 sobre um servidor v19, recuperado por um backup manual feito por sorte.

## 3. Reversão — escrita antes, não depois

O caminho de volta escreve-se **antes** de abrir a janela, não quando for preciso.

- **ficheiros**: cópia do que vai ser substituído, com data no nome;
- **registos**: um `REVERTER_<assunto>_<data>.json` com o estado anterior de cada registo tocado, suficiente para o repor sem depender de memória;
- **nunca apagar** camadas anteriores — desactivar, que é reversível.

## 4. Os passos

Numerados, na ordem de execução, cada um com o comando exacto. Um passo por acção; sem "e depois ajusta-se o resto".

Marcar quais são reversíveis sozinhos e quais exigem a reversão da secção 3.

## 5. Verificação, no fim

O que transforma «aplicado com sucesso» de afirmação em facto.

- **o código que ficou lá é o que se julga ter posto?** A versão do manifest **não prova** — no GBUK a mesma versão nomeou dois códigos diferentes. Provar por impressão digital do módulo instalado, ou por espelho do código vivo (`--ref`);
- **as contagens da secção 2** batem com o esperado;
- **o comportamento** que motivou a janela faz agora o que devia, verificado no ecrã e não no log.

Se não houver meio de provar o código, declarar `PONTO POR VALIDAR` — nunca «verificado».

> **Nunca escrever «validado».** Implantar prova que o código lá está; validar é o cliente dizer que faz o que ele quer.

## 6. O que este guião NÃO leva, e é deliberado

A secção que evita arrastar o que ninguém pediu. Para cada coisa deixada de fora, dizer **o quê** e **porquê**.

Casos típicos: alterações de outra pessoa por publicar, ficheiros que divergiram mas são de outro âmbito, o segundo patch que podia ir junto mas não foi pedido.

Sem esta secção, o que fica de fora parece esquecimento em vez de decisão.

## 7. Antes de abrir a janela

- **quem avisar**, e porquê. Se o módulo é território de outra pessoa, avisar mesmo que o travão do passo 2 proteja — o travão protege os dados, não a relação;
- **janela acordada** com quem usa o sistema;
- **produção exige confirmação explícita** para aquela execução concreta. Uma autorização dada uma vez não cobre a execução seguinte;
- **dry-run feito e revisto**.
