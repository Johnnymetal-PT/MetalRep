# Aviso à equipa — um `git pull` único, para a framework voltar a atualizar-se

> Para copiar e enviar. O comando foi verificado hoje, 2026-09-29.

---

Olá a todos,

É um comando só, uma vez, em cada máquina. Vale a pena perceber porquê, porque o motivo é pouco intuitivo.

## O que estava a acontecer

O passo 2 do ritual de arranque — o `pg_ensure_framework_current.ps1`, aquele que garante a framework atualizada — **nunca puxava nada quando havia alguma coisa para puxar**.

O `git` escreve o `From https://github.com/...` no *stderr*, e em PowerShell isso vira erro terminante. O script morria aí e escrevia `AVISO: pg_ensure_framework_current nao concluiu (From ...); a sessao continua`. Como o aborto acontecia no primeiro passo, **a re-sincronização do projeto também não corria** — o projeto ficava desalinhado da framework, em silêncio.

O que o escondeu foi a assimetria: sem nada para puxar, o `git` não escreve no *stderr*, o script chega ao fim e diz `OK: framework ja estava atualizado`. Falhava só quando tinha trabalho para fazer, e dizia «OK» exatamente quando não tinha nenhum.

Obrigado ao **Miguel**, que o reportou hoje depois de comparar o `template_git_head` com o HEAD e de ter tido de contornar com `-SkipPull`.

## Porque é preciso fazer isto à mão

Está corrigido e já está na `main` da framework. Mas **a correção não se consegue entregar a si própria**: enquanto a tua cópia do `_pg_template` estiver atrasada, o script antigo aborta no `pull` — que é o defeito — e por isso nunca chega à versão corrigida. Fica em ciclo fechado até alguém o abrir de fora.

## O comando

No teu clone do `_pg_template` (Windows, macOS ou Linux, é o mesmo):

```
git -C C:\CAMINHO\PARA\_pg_template pull
```

Se der `Your local changes ... would be overwritten`, tens alterações por commitar nessa pasta: vê com `git -C <caminho> status` e trata delas primeiro. É o segundo defeito que foi corrigido — o script recusava o `pull` só por haver alterações locais, mesmo quando nenhuma delas colidia com o que vinha de fora.

## Como confirmas que ficou bom

Na sessão seguinte, em qualquer projeto, o passo 2 passa a escrever `OK: framework atualizado ao origin` ou `OK: framework ja estava atualizado` — e deixa de aparecer o `nao concluiu`. A partir daí o mecanismo volta a alimentar-se sozinho e não precisas de repetir nada.

Obrigado,
Bruno
