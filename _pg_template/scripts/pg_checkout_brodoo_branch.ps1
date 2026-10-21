param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

$repoPath = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repoPath)) {
    throw "Repositorio nao encontrado: $repoPath"
}

function Get-DeclaredBrodooBranches {
    # Devolve TODAS as branches declaradas, sem escolher nenhuma.
    #
    # A versao anterior fazia `Select-Object -First 1` sobre .pg/projects e ficava com a
    # declaracao do primeiro projeto que a travessia encontrasse -- num repositorio
    # multi-projeto isso e escolher ao acaso. `FACTO OBSERVADO` (givachoice): dois projetos
    # espelhados, `givachoice-fase-3-audit` a declarar `audit` e o legacy da raiz a declarar
    # `main`. Quem escolhe e quem chama, com a informacao toda a vista.
    param([string]$path)

    $encontradas = @()

    $projectsDir = Join-Path $path ".pg\projects"
    if (Test-Path $projectsDir) {
        foreach ($dir in (Get-ChildItem $projectsDir -Directory -ErrorAction SilentlyContinue)) {
            $pj = Join-Path $dir.FullName "project\project.json"
            if (-not (Test-Path $pj)) { continue }
            try {
                $branch = (Read-Utf8JsonFile -Path $pj).project.repository_branch
                if ($branch) {
                    $encontradas += [pscustomobject]@{ Branch = [string]$branch; Origem = $dir.Name }
                }
            } catch {}
        }
    }

    # O legacy .pg/project/project.json so conta quando nao ha estrutura namespaced: costuma
    # estar desatualizado (no givachoice diz `main`, que e producao do cliente).
    if ($encontradas.Count -eq 0) {
        $old = Join-Path $path ".pg\project\project.json"
        if (Test-Path $old) {
            try {
                $branch = (Read-Utf8JsonFile -Path $old).project.repository_branch
                if ($branch) {
                    $encontradas += [pscustomobject]@{ Branch = [string]$branch; Origem = 'legacy' }
                }
            } catch {}
        }
    }

    return $encontradas
}

function Get-BrodoBranchFromLocal {
    # Compatibilidade: uma unica branch declarada, ou $null se nao houver ou for ambigua.
    param([string]$path)

    $distintas = @(Get-DeclaredBrodooBranches -path $path | Select-Object -ExpandProperty Branch -Unique)
    if ($distintas.Count -eq 1) { return $distintas[0] }
    return $null
}

function Get-BrodoBranchFromRemote {
    param([string]$path)

    # Enumerar as branches remotas REAIS (em vez de uma lista fixa que falha ex.: "audit", "brodoo").
    # A branch Brodoo e a que e AUTO-CONSISTENTE: repository_branch (no project.json dessa branch)
    # == nome da branch. Verificar o namespaced primeiro (fonte atual) e o legacy so como fallback.
    $heads = @()
    $raw = git -C $path ls-remote --heads origin 2>$null
    foreach ($line in ($raw -split "`n")) {
        if ($line -match 'refs/heads/(.+)$') { $heads += $Matches[1].Trim() }
    }

    # Standard: a branch Brodoo chama-se 'brodoo'. Se existir e for auto-consistente, tem
    # PRECEDENCIA sobre outras branches Brodoo antigas (ex.: Teste) que fiquem a coexistir
    # durante a migracao. Ordenar 'brodoo' primeiro resolve a ambiguidade de forma determinista.
    $heads = @($heads | Sort-Object @{ Expression = { if ($_ -eq 'brodoo') { 0 } else { 1 } } }, @{ Expression = { $_ } })

    foreach ($b in $heads) {
        # Namespaced (fonte atual)
        $dirs = git -C $path ls-tree --name-only "origin/${b}:.pg/projects" 2>$null
        if ($dirs) {
            foreach ($d in ($dirs -split "`n" | Where-Object { $_ -ne "" })) {
                $jsonRaw = git -C $path show "origin/${b}:.pg/projects/$d/project/project.json" 2>$null
                if ($jsonRaw) {
                    try {
                        if ((($jsonRaw | ConvertFrom-Json).project.repository_branch) -eq $b) { return $b }
                    } catch {}
                }
            }
        }

        # Legacy (fallback)
        $jsonRaw2 = git -C $path show "origin/${b}:.pg/project/project.json" 2>$null
        if ($jsonRaw2) {
            try {
                if ((($jsonRaw2 | ConvertFrom-Json).project.repository_branch) -eq $b) { return $b }
            } catch {}
        }
    }

    return $null
}

# --- Início da execução ---
#
# STANDARD: a branch Brodoo chama-se 'brodoo', e é aí que os agentes trabalham. Assim
# garante-se que nenhum commit de framework/mirror cai em 'main' (produção do cliente).
#
# MAS A DECLARAÇÃO DO PROJETO MANDA SOBRE O STANDARD. Até 2026-09-11 este script tinha
# 'brodoo' fixo no código e só consultava o project.json quando 'brodoo' NÃO existia.
# `FACTO OBSERVADO` (givachoice): o projeto declara `audit`, a branch `brodoo` existe como
# linhagem antiga, e o ritual levava a sessão para uma branch que diverge em 1698 commits,
# sem os dados do projeto e com outra árvore de addons. Produziu pelo menos uma conclusão
# factual errada (06/08/2026). O `pg_align_fleet_framework.ps1` já respeitava a declaração:
# eram dois scripts da mesma framework a discordar um do outro.
# Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, achado D2.

function Get-CurrentBranchName {
    # `symbolic-ref` e nao `rev-parse --abbrev-ref HEAD`: num repositorio acabado de clonar
    # de um remoto vazio nao ha commits, e o rev-parse falha com "ambiguous argument 'HEAD'"
    # -- que, debaixo do Stop, rebentava o ritual no passo 1 antes de dizer o que fosse.
    $eap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $nome = (git -C $repoPath symbolic-ref --short -q HEAD 2>$null | Out-String).Trim()
        if (-not $nome) { $nome = (git -C $repoPath rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim() }
        return $nome
    }
    finally { $ErrorActionPreference = $eap }
}

$savedEAPInicio = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$temCommits = [bool]((git -C $repoPath rev-parse --verify -q HEAD 2>$null | Out-String).Trim())
$ErrorActionPreference = $savedEAPInicio

$currentBranch = Get-CurrentBranchName
$producao = @('main', 'master')

$targetBranch = 'brodoo'
$declaradas = @(Get-DeclaredBrodooBranches -path $repoPath)
$distintas = @($declaradas | Select-Object -ExpandProperty Branch -Unique)
$candidatas = @($distintas | Where-Object { $producao -notcontains $_ })

if ($distintas.Count -eq 0) {
    Write-Host "Nenhuma branch Brodoo declarada; a usar o standard '$targetBranch'."
}
elseif ($candidatas.Count -eq 0) {
    # Declaração aponta para produção do cliente. Não se obedece: é para isto que o
    # standard existe. O sítio para corrigir é o Odoo (repository_branch).
    # A declaracao lida aqui vem do ESPELHO LOCAL, que pode estar desactualizado -- nao
    # do Odoo. Mandar "corrigir no Odoo" quando o Odoo ja esta certo faz perder tempo a
    # procurar um erro que nao existe: aconteceu no ancoravip a 2026-09-11, em que o Odoo
    # ja declarava 'brodoo' e era o espelho local que estava velho.
    Write-Host "AVISO: o espelho local declara '$($distintas -join ", ")' (producao do cliente). A usar o standard '$targetBranch'."
    Write-Host "       Confirmar qual esta velho: se o Odoo ja declarar '$targetBranch', basta re-sincronizar o espelho (pg_ensure_framework_current.ps1); se nao, corrigir o repository_branch no Odoo."
}
elseif ($candidatas.Count -eq 1) {
    $targetBranch = $candidatas[0]
    if ($targetBranch -ne 'brodoo') {
        Write-Host "Branch Brodoo declarada pelo projeto: '$targetBranch' (a declaracao manda sobre o standard)."
    }
}
else {
    # Várias declarações em desacordo. Não se adivinha: se a branch actual for uma delas,
    # respeita-se; senão pára, porque escolher uma ao acaso foi o defeito que se corrigiu.
    if ($candidatas -contains $currentBranch) {
        $targetBranch = $currentBranch
        Write-Host "AVISO: declaracoes em desacordo ($($candidatas -join ", ")); a manter a branch actual '$currentBranch', que e uma delas."
    }
    else {
        throw "Branches Brodoo declaradas em desacordo: $($candidatas -join ', '). A branch actual ('$currentBranch') nao e nenhuma delas. Alinhar o repository_branch no Odoo, ou fazer checkout manual da correcta antes de repetir o ritual."
    }
}

# Fetch silencioso para ter refs remotas actualizadas
git -C $repoPath fetch --all --quiet 2>$null | Out-Null

$savedEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"

$localHasBrodoo = [bool](git -C $repoPath branch --list $targetBranch 2>$null)
$remoteHasBrodoo = [bool](git -C $repoPath ls-remote --heads origin $targetBranch 2>$null)

# A saida do checkout e GUARDADA, nao deitada fora: quando o checkout falha, a razao
# esta la e e accionavel ("untracked working tree files would be overwritten", com os
# nomes). Ate 2026-09-11 ia toda para Out-Null e o erro final dizia apenas "nao foi
# possivel ficar na branch", que nao diz a ninguem o que fazer a seguir.
$saidaCheckout = $null
if ($localHasBrodoo) {
    Write-Host "A garantir a branch '$targetBranch' (existe localmente)..."
    $saidaCheckout = git -C $repoPath checkout $targetBranch 2>&1
}
elseif ($remoteHasBrodoo) {
    Write-Host "A garantir a branch '$targetBranch' (a partir de origin/$targetBranch)..."
    $saidaCheckout = git -C $repoPath checkout -B $targetBranch "origin/$targetBranch" 2>&1
}
elseif (-not $temCommits) {
    # Repositorio sem commits nenhum (clone de um remoto vazio, ou `git init`): nao ha de
    # onde criar a branch, e nao e preciso. Aponta-se o HEAD para ela; nasce no primeiro
    # commit, e so entao se publica. `FACTO OBSERVADO` (2026-09-28): era aqui que o ritual
    # parava na primeira sessao de um repositorio novo, depois do auto-bootstrap.
    git -C $repoPath symbolic-ref HEAD "refs/heads/$targetBranch" 2>&1 | Out-Null
    Write-Host "Repositorio sem commits: HEAD passa a apontar para '$targetBranch'. A branch nasce no primeiro commit; publicar entao com: git push -u origin $targetBranch"
}
else {
    # 'brodoo' ainda nao existe: criar a partir da branch Brodoo atual (framework+mirror+codigo).
    $base = Get-BrodoBranchFromLocal -path $repoPath
    if (-not $base) { $base = Get-BrodoBranchFromRemote -path $repoPath }
    if (-not $base) { $base = $currentBranch }
    Write-Host "Branch '$targetBranch' inexistente. A criar a partir de '$base'..."
    if (git -C $repoPath ls-remote --heads origin $base 2>$null) {
        git -C $repoPath checkout -B $targetBranch "origin/$base" 2>&1 | Out-Null
    }
    else {
        git -C $repoPath checkout -B $targetBranch $base 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        # Publicar para o remote (persistir para a equipa/mirror). Nao-fatal se falhar.
        $pushOut = git -C $repoPath push -u origin $targetBranch 2>&1
        if ($LASTEXITCODE -eq 0) { Write-Host "OK: branch '$targetBranch' criada a partir de '$base' e publicada." }
        else { Write-Host "AVISO: '$targetBranch' criada localmente mas o push falhou (trabalhar local); detalhe: $($pushOut | Select-Object -Last 1)" }
    }
}

$newBranch = Get-CurrentBranchName
$ErrorActionPreference = $savedEAP

if ($newBranch -ne $targetBranch) {
    $detalhe = ($saidaCheckout | ForEach-Object { "$_" }) -join "`n"
    $mensagem = "Nao foi possivel ficar na branch '$targetBranch' (branch actual: $newBranch)."
    if ($detalhe) { $mensagem += "`nO git recusou com:`n$detalhe" }
    # A causa mais comum tem remediacao propria, e vale a pena nomea-la: ficheiros nao
    # rastreados na branch actual que existem versionados na branch de destino. Antes de
    # os apagar, comparar (`git hash-object <f>` vs `git rev-parse origin/<branch>:<f>`)
    # -- se forem iguais, apagar nao perde nada; se diferirem, ha trabalho local por
    # guardar. Foi o caso do ancoravip a 2026-09-11: dois ficheiros identicos byte a byte
    # aos ja versionados bloqueavam o checkout, e a mensagem nao os nomeava.
    if ($detalhe -match 'untracked working tree files would be overwritten') {
        $mensagem += "`nRemediacao: os ficheiros acima nao estao rastreados nesta branch mas existem em '$targetBranch'."
        $mensagem += "`n  Comparar antes de apagar:  git hash-object <ficheiro>  vs  git rev-parse origin/$targetBranch`:<ficheiro>"
        $mensagem += "`n  Iguais -> apagar o local nao perde nada. Diferentes -> guardar o local primeiro."
    }
    throw $mensagem
}
$origem = if ($distintas -contains $targetBranch) { 'declarada pelo projeto' } else { 'standard da framework' }
Write-Host "OK: na branch '$targetBranch' ($origem)."

# git pull na 'brodoo' se existir no remote (mensagens 'From https://...' no stderr sao informativas)
if ($remoteHasBrodoo) {
    Write-Host "A fazer git pull na branch $targetBranch..."
    $ErrorActionPreference = "Continue"
    $pullOut = git -C $repoPath pull origin $targetBranch 2>&1
    $ErrorActionPreference = $savedEAP
    $pullOut | Where-Object { $_ -notmatch "^From https?://" } | ForEach-Object { Write-Host $_ }
}

Write-Host "OK: pg_checkout_brodoo_branch concluido (branch: $targetBranch)."
