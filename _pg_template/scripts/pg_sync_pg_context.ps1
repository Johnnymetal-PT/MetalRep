param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,

  [string]$CommunityPath,

  [string]$EnterprisePath,

  [ValidateSet("community", "enterprise")]
  [string]$EditionHint
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Resolve-CommunityPath {
  param(
    [string]$RepositoryPath,
    [string]$ExplicitCommunityPath
  )

  if ($ExplicitCommunityPath) {
    return [System.IO.Path]::GetFullPath($ExplicitCommunityPath)
  }

  $repo = [System.IO.Path]::GetFullPath($RepositoryPath)
  $sourceClone = Join-Path $repo "vendor\odoo_src\community"
  if (Test-Path $sourceClone) {
    $canonicalFromLink = Resolve-OdooSourcePathFromLinkTarget -RepositoryPath $repo -RelativePath "community"
    if ($canonicalFromLink) {
      return $canonicalFromLink
    }

    return $sourceClone
  }

  return Join-Path $repo "vendor\odoo_core"
}

function Resolve-EnterprisePath {
  param(
    [string]$RepositoryPath,
    [string]$ExplicitEnterprisePath
  )

  if ($ExplicitEnterprisePath) {
    return [System.IO.Path]::GetFullPath($ExplicitEnterprisePath)
  }

  $repo = [System.IO.Path]::GetFullPath($RepositoryPath)
  $candidate = Join-Path $repo "vendor\odoo_src\enterprise"
  if (Test-Path $candidate) {
    $canonicalFromLink = Resolve-OdooSourcePathFromLinkTarget -RepositoryPath $repo -RelativePath "enterprise"
    if ($canonicalFromLink) {
      return $canonicalFromLink
    }

    return $candidate
  }

  return $null
}

function Resolve-OdooSourcePathFromLinkTarget {
  param(
    [string]$RepositoryPath,
    [string]$RelativePath
  )

  $sourceRootLink = Join-Path $RepositoryPath "vendor\odoo_src"
  if (-not (Test-Path $sourceRootLink)) {
    return $null
  }

  $item = Get-Item -LiteralPath $sourceRootLink -Force
  $isReparsePoint = (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
  if (-not $isReparsePoint) {
    return $null
  }

  $target = $item.Target
  if ($target -is [System.Array]) {
    $target = @($target | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })[0]
  }

  if ([string]::IsNullOrWhiteSpace([string]$target)) {
    return $null
  }

  $targetRoot = [System.IO.Path]::GetFullPath([string]$target)
  $candidate = Join-Path $targetRoot $RelativePath
  if (Test-Path $candidate) {
    return $candidate
  }

  return $null
}

function Get-OdooReleaseMetadata {
  param(
    [string]$CommunitySourcePath,
    [string]$EnterpriseSourcePath,
    [string]$EditionHint
  )

  $releasePath = Join-Path $CommunitySourcePath "odoo\release.py"
  if (-not (Test-Path $releasePath)) {
    throw "release.py nao encontrado em $releasePath"
  }

  $content = Read-Utf8TextFile -Path $releasePath
  $versionMatch = [regex]::Match($content, "version_info\s*=\s*\(\s*(\d+)\s*,\s*(\d+)")
  if (-not $versionMatch.Success) {
    throw "Nao foi possivel detetar a versao do Odoo em $releasePath"
  }

  $series = "{0}.{1}" -f $versionMatch.Groups[1].Value, $versionMatch.Groups[2].Value
  $edition = $null
  $editionEvidence = @()
  if ($EditionHint -eq "enterprise") {
    $editionEvidence += "hint explicito de edicao enterprise"
    $edition = "Enterprise"
  } elseif ($EditionHint -eq "community") {
    $editionEvidence += "hint explicito de edicao community"
    $edition = "Community"
  } elseif ($content -match "\+e(?:[-']|$)") {
    $editionEvidence += "release.py contem marcador +e"
    $edition = "Enterprise"
  } elseif ($content -match "repos_heads\s*=\s*\{[^}]*'enterprise'\s*:") {
    $editionEvidence += "release.py referencia repositorio enterprise"
    $edition = "Enterprise"
  } elseif ($EnterpriseSourcePath -and (Test-Path $EnterpriseSourcePath)) {
    $editionEvidence += "existe checkout enterprise em vendor/odoo_src/enterprise"
    $edition = "Enterprise"
  }

  return @{
    Series = $series
    Edition = $edition
    ReleasePath = $releasePath
    EditionEvidence = $editionEvidence
  }
}

$repoPath = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repoPath)) {
  throw "Repositorio nao encontrado: $repoPath"
}

$contextPath = Join-Path $repoPath "PG_CONTEXT.md"
if (-not (Test-Path $contextPath)) {
  throw "PG_CONTEXT.md nao encontrado em $contextPath"
}

$resolvedCommunityPath = Resolve-CommunityPath -RepositoryPath $repoPath -ExplicitCommunityPath $CommunityPath
if (-not (Test-Path $resolvedCommunityPath)) {
  throw "Source Community do Odoo nao encontrado em $resolvedCommunityPath"
}

$resolvedEnterprisePath = Resolve-EnterprisePath -RepositoryPath $repoPath -ExplicitEnterprisePath $EnterprisePath
$metadata = Get-OdooReleaseMetadata -CommunitySourcePath $resolvedCommunityPath -EnterpriseSourcePath $resolvedEnterprisePath -EditionHint $EditionHint
$docsBase = "https://www.odoo.com/documentation/$($metadata.Series)/"
$studioDocs = $docsBase + "applications/studio.html"
$developerDocs = $docsBase + "developer/reference.html"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

$original = Read-Utf8TextFile -Path $contextPath
$context = $original

# Ensure e nao Set, para a VERSAO e para a EDICAO.
#
# `Set-PgLabeledValue` e inocuo quando o rotulo nao existe -- e metade da frota nao o
# tem. `FACTO OBSERVADO` (2026-09-11): 16 de 32 repositorios sem o rotulo
# "Versao do Odoo:". Nesses, o preflight cai na governance do espelho, que em
# repositorio multi-projeto e resolvida pela ordem de travessia do disco: foi assim que
# o givachoice passou onze dias a citar documentacao de 17.0 correndo 19.0.
#
# Com o rotulo escrito -- e reescrito a cada ritual a partir do `release.py` do source --
# a resolucao deixa de depender de travessia nenhuma. E deixa de ser um rotulo MANUAL:
# era essa a armadilha seguinte, provada no Evostone, onde o valor foi corrigido na fonte
# a 27/08 e o rotulo escrito a mao continuou a declarar 19.0 por cima dele.
$context = Ensure-PgLabeledValue -Text $context -Label "Path do core:" -Value $resolvedCommunityPath -InsertAfterLabel "Ambiente:"
$context = Ensure-PgLabeledValue -Text $context -Label "Path source Enterprise:" -Value $(if ($resolvedEnterprisePath) { $resolvedEnterprisePath } else { "[NAO CONFIGURADO]" }) -InsertAfterLabel "Path do core:"
$context = Set-PgLabeledValue -Text $context -Label "Versao do Odoo:" -Value $metadata.Series
$context = Set-PgLabeledValue -Text $context -Label "Documentacao oficial base:" -Value $docsBase
$context = Set-PgLabeledValue -Text $context -Label "Documentacao Studio:" -Value $studioDocs
$context = Set-PgLabeledValue -Text $context -Label "Documentacao Developer:" -Value $developerDocs

if ($metadata.Edition) {
  $context = Set-PgLabeledValue -Text $context -Label "Edicao:" -Value $metadata.Edition
} else {
  $currentEdition = Get-PgLabeledValue -Text $context -Label "Edicao:"
  if (-not $currentEdition) {
    $context = Set-PgLabeledValue -Text $context -Label "Edicao:" -Value "[PONTO POR VALIDAR]"
  }
}

# Sem alteracao substantiva, NAO se escreve.
#
# Este script carimbava a hora a cada execucao, pelo que qualquer corrida produzia um
# diff. Isso bastava para o tornar impossivel de ligar ao ritual: um PG_CONTEXT.md sujo
# a cada arranque de sessao suja a arvore de trabalho de todos os projetos -- e foi
# precisamente um ficheiro sujo escrito pela propria framework (.pg/tokens/consumption.jsonl)
# que bloqueou o passo 1 do ritual no givachoice. A licao do AUD-04 e a mesma: um campo
# volatil num ficheiro versionado gera ruido permanente.
#
# A comparacao ignora o carimbo, que so e escrito quando algo de facto mudou.
$marcador = '[comparacao]'
$antes = Set-PgLabeledValue -Text $original -Label "Ultima sincronizacao automatica:" -Value $marcador
$depois = Set-PgLabeledValue -Text $context -Label "Ultima sincronizacao automatica:" -Value $marcador

if ($antes -ceq $depois) {
  Write-Host "OK: PG_CONTEXT.md ja coerente com o source Odoo (nada a escrever)"
  Write-Host "  Versao: $($metadata.Series)"
  exit 0
}

$context = Set-PgLabeledValue -Text $context -Label "Ultima sincronizacao automatica:" -Value $timestamp
Write-Utf8NoBomFile -Path $contextPath -Content $context

# Dizer O QUE mudou, e nao so que mudou: a versao declarada e a fonte de verdade n.1 do
# contrato, e uma alteracao silenciosa dela e o defeito que esta correccao existe para fechar.
$versaoAntes = Get-PgLabeledValue -Text $original -Label "Versao do Odoo:"
if ($versaoAntes -and $versaoAntes -ne $metadata.Series) {
  Write-Host "ATENCAO: versao declarada corrigida de '$versaoAntes' para '$($metadata.Series)', que e a serie do source."
}

Write-Host "OK: PG_CONTEXT.md atualizado com metadados do source Odoo"
Write-Host "  Versao: $($metadata.Series)"
Write-Host "  Community: $resolvedCommunityPath"
if ($resolvedEnterprisePath) {
  Write-Host "  Enterprise: $resolvedEnterprisePath"
}
Write-Host "  Docs: $docsBase"
if ($metadata.Edition) {
  Write-Host "  Edicao: $($metadata.Edition)"
} else {
  Write-Host "  Edicao: mantida sem conclusao automatica"
}
