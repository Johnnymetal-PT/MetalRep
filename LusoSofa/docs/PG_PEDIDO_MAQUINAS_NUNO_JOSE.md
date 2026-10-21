# Pedido ao Nuno Oliveira e ao José Couto — duas coisas nas vossas máquinas

> Para copiar e enviar. Tudo o que está aqui foi verificado a 2026-09-11; nada é suposição.

---

Olá Nuno, olá José,

Há duas coisas que só se resolvem nas vossas máquinas, e ambas são rápidas. A primeira é a mais importante.

## 1. Declarar as pastas de trabalho fora dos repositórios

**O problema, com números.** Nas 46 conversas do givachoice, o agente procurou o `AGENTS.md` nas pastas de servidor **7 vezes**. Não encontrou nada em nenhuma, respondeu «não existe, continuo», e seguiu sem os factos do projeto. O resultado foram **seis incidentes de confusão entre Odoo 17, 18 e 19** — incluindo um deploy de código v17 sobre o servidor de testes v19, que só se recuperou por haver um backup manual feito por sorte minutos antes.

Isto não foi distração de ninguém. As duas migrações completas da base de produção e o desenvolvimento dos módulos custom aconteceram em pastas como `C:\Odoo\PGAddons`, `C:\Odoo19\pgmodules` e `MIGRV18` — pastas sem `.pg`, sem espelho, sem `AGENTS.md`. A framework não as conhecia.

**A framework passou a ter onde guardar esses factos, mas não os adivinha.** Declarar é um ato humano, uma vez por pasta, e só quem lá trabalha sabe qual é a versão, o servidor e a base.

Em cada pasta de trabalho recorrente, correr uma vez:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\<voce>\Desktop\Repos\_pg_template\scripts\pg_init_work_folder.ps1 `
  -Path <pasta> `
  -OdooSourcePath <caminho do source Odoo dessa versao> `
  -Servidor <servidor> `
  -BaseDados <base>
```

Três coisas que vale a pena saber antes:

- **a versão é confirmada contra o source, não aceite de boa fé.** Com `-OdooSourcePath`, é lida do `release.py`. Declarar uma versão que o source contradiz **falha e não escreve nada** — é exatamente o erro que custou o deploy de v17 sobre v19;
- **o que já lá estiver sobrevive.** O bloco é delimitado; tudo o que estiver fora dos marcadores é vosso e resiste a qualquer reexecução;
- **o script recusa-se a correr** numa pasta que já seja repositório da framework.

Depois disto, uma sessão que abra nessa pasta encontra os factos e usa-os — e recusa quando o que está declarado contradiz o source.

**Se não souberem ao certo a versão de uma pasta, digam-me antes de declarar.** Uma declaração errada é pior do que nenhuma, porque passa a ser acreditada.

## 2. Instalar as dependências Python da framework

A framework passou a gerar PDF a partir de Markdown, e isso trouxe dependências que **nunca estiveram declaradas em lado nenhum** — até agora descobria-se por erro de import.

Uma vez por máquina, na pasta do `_pg_template`:

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

**O segundo comando é obrigatório e não vem no primeiro.** O `playwright` instala a biblioteca, não o browser. São cerca de 150 MB de binários, uma vez só. Sem ele, a geração de PDF falha — falha a dizer o comando que resolve, mas falha.

## Porque é que isto vos chega agora

Veio da auditoria de desempenho da framework no givachoice, feita com as extrações que vocês mandaram. A conclusão foi que a framework não correu mal por ser pesada: **correu mal por ser rígida onde estava presente, e por estar ausente onde o trabalho realmente acontecia.**

A parte da rigidez foi corrigida — o sync já não apaga os vossos overrides locais, o ritual já respeita a branch declarada pelo projeto, e a versão do Odoo já é cruzada contra o source.

A parte da ausência é esta. É a única que não se corrige do lado da framework, porque depende de alguém dizer o que só quem trabalha na pasta sabe.

Obrigado,
Bruno
