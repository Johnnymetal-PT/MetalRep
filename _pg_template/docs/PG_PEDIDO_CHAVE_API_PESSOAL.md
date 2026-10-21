# Pedido à equipa — a chave de acesso ao Odoo passa a ser tua

> Para copiar e enviar. Tudo o que está aqui foi verificado no Odoo a 2026-09-28; nada é suposição.

---

Olá a todos,

A partir de hoje, a chave que os scripts usam para falar com o Odoo da Parâmetro Global é **pessoal**. Cada um tem a sua, e são precisos **dois minutos** de cada pessoa. Há uma coisa com prazo, no fim.

## Porquê

Até agora a equipa inteira partilhava a chave de um utilizador de serviço, guardada no repositório da framework. Duas consequências, e a segunda pesa mais:

**A chave estava no histórico do git.** Entrou lá a 9 de julho e lá continua: apagar o ficheiro não revoga nada. Quem saísse da equipa mantinha uma cópia válida no clone e no *reflog*. E essa conta tem **Administração** do Odoo — ou seja, o que andou em todos os clones não era uma credencial de leitura, era uma chave de administrador.

**Nada era atribuível.** Todas as escritas feitas pelos scripts apareciam como «Brodoo» — as ligações aos Odoo dos clientes, os artigos do Knowledge, as correções de dados. Não havia como saber quem tinha feito o quê. Com chave pessoal, o Odoo regista quem foi.

## O que fazer — dois passos

**1. Criar a tua chave no Odoo**

Nas tuas preferências: **Segurança da conta → Novas chaves API**. Dá-lhe um nome que reconheças (por exemplo `PG Framework`) e escolhe a duração **`Persistent Key`**.

Se a opção `Persistent Key` não aparecer na lista, falta-te a permissão — diz ao Bruno, é um clique. **Não escolhas «1 Day» para contornar**: a chave morre na manhã seguinte e vais perceber isso a meio de outra coisa.

**2. Configurar a tua máquina**

Em qualquer projeto com a framework:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1
```

**Atenção ao domínio do login.** Na nossa base há contas em `@parametro.global` e contas em `@parametro.pt` — o Cláudio, o Vitor e o Eduardo estão em `.pt`. Usa o mesmo login com que entras no Odoo; se te enganares, dá «Autenticação recusada» e não diz que o problema é o domínio.

Pede o login e a chave (a chave não aparece no ecrã), valida **antes** de guardar, e mostra o nome de quem autenticou. **Confere esse nome**: se aparecer o de outra pessoa, a chave está trocada — e é bem melhor descobri-lo aqui do que quando uma escrita aparecer assinada por ela.

Se o comando der «ficheiro não encontrado», é o teu clone do `_pg_template` que está atrasado: faz `git pull` nele e repete. Numa sessão normal o ritual de arranque já trata disso sozinho.

O ficheiro fica em `%USERPROFILE%\.pg\odoo_credentials.json`, **fora de qualquer repositório** — o comando recusa-se a escrever dentro de um, para que não possa ser commitado por engano.

Para conferir mais tarde, sem escrever nada:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1 -Verificar
```

## Os dois passos são mesmo dois

Criar a chave no Odoo **não** configura a máquina. Enquanto não correres o comando do passo 2, continuas a trabalhar pela chave partilhada — e o preflight vai avisar-te disso no arranque de cada sessão, com o comando para resolver.

## Miguel — uma com prazo

A chave que criaste hoje (`Testes`) **não é persistente: expira amanhã, dia 29, às 00:00**. Cria outra com `Persistent Key` e apaga essa, senão amanhã de manhã ficas sem acesso sem perceber porquê.

## Pedro — atenção antes de a antiga ser desligada

Tens uma chave emitida na conta de serviço, em nome teu (`PG AI Brodoo Consulting Pedro`), e ela ainda está em uso. Quando a conta for desativada, essa chave morre com ela. Passa para a tua própria antes disso — já criaste uma hoje, falta só o passo 2.

## O que acontece a seguir

Quando toda a gente estiver na sua chave, a conta de serviço é desativada e as chaves antigas revogadas. Só depois disso é que a chave que andou no histórico do git deixa mesmo de dar acesso — e essa verificação é feita pela negativa, a tentar usá-la e confirmar que é recusada.

Até lá nada pára: quem ainda não tiver configurado continua a trabalhar, apenas com um aviso.

Obrigado,
Bruno
