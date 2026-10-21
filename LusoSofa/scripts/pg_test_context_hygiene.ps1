param()

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Assert-True {
  param(
    [bool]$Condition,
    [string]$Message
  )

  if (-not $Condition) {
    throw $Message
  }
}

function Assert-False {
  param(
    [bool]$Condition,
    [string]$Message
  )

  if ($Condition) {
    throw $Message
  }
}

function Assert-Contains {
  param(
    [string]$Text,
    [string]$Expected,
    [string]$Message
  )

  $haystack = if ($null -eq $Text) { '' } else { $Text }
  if (-not $haystack.Contains($Expected)) {
    throw $Message
  }
}

function Assert-NotContains {
  param(
    [string]$Text,
    [string]$Unexpected,
    [string]$Message
  )

  $haystack = if ($null -eq $Text) { '' } else { $Text }
  if ($haystack.Contains($Unexpected)) {
    throw $Message
  }
}

function Get-MarkedBlock {
  param(
    [string]$Text,
    [string]$Marker
  )

  $pattern = "(?s)<!-- PG_AUTO:$Marker`:START -->\s*(.*?)\s*<!-- PG_AUTO:$Marker`:END -->"
  $match = [regex]::Match($Text, $pattern)
  if (-not $match.Success) {
    throw "Marcadores nao encontrados para $Marker"
  }

  return $match.Groups[1].Value
}

function Join-Chars {
  param([int[]]$Codes)

  return ([string]::Concat(@($Codes | ForEach-Object { [char]$_ })))
}

function New-FixtureRepo {
  param(
    [string]$RootPath,
    [string]$Name,
    [switch]$DirtySnapshots
  )

  $repo = Join-Path $RootPath $Name
  New-Item -ItemType Directory -Path $repo -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg_framework\scripts') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg_framework\templates') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $repo '.github\workflows') -Force | Out-Null

  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) '.editorconfig') -Destination (Join-Path $repo '.editorconfig') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) '.gitignore') -Destination (Join-Path $repo '.gitignore') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) '.gitattributes') -Destination (Join-Path $repo '.gitattributes') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'config.toml') -Destination (Join-Path $repo 'config.toml') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\AGENTS.md') -Destination (Join-Path $repo 'AGENTS.md') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\CLAUDE.md') -Destination (Join-Path $repo 'CLAUDE.md') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\PG_CONTEXT.md') -Destination (Join-Path $repo 'PG_CONTEXT.md') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\PG_SCOPE_INTAKE.yaml') -Destination (Join-Path $repo 'PG_SCOPE_INTAKE.yaml') -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\AGENTS_SHARED.md') -Destination (Join-Path $repo '.pg_framework\templates\AGENTS_SHARED.md') -Force
  Copy-Item -Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\.pg\*.json') -Destination (Join-Path $repo '.pg') -Force
  Copy-Item -Path (Join-Path $PSScriptRoot '*.ps1') -Destination (Join-Path $repo '.pg_framework\scripts') -Force

  # doc_templates: o smoke test trata a ausencia de MANIFEST.json como ERRO, logo
  # sem isto o fixture nunca poderia passar. Chegam o manifesto e os TPL_*.md --
  # a verificacao de integridade so compara esses hashes (assets/ fica de fora
  # para o fixture nao arrastar dezenas de MB por repo).
  $docTemplatesFixture = Join-Path $repo 'doc_templates'
  New-Item -ItemType Directory -Path $docTemplatesFixture -Force | Out-Null
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'doc_templates\MANIFEST.json') -Destination $docTemplatesFixture -Force
  Copy-Item -Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'doc_templates\TPL_*.md') -Destination $docTemplatesFixture -Force
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\.github\workflows\pg_refresh_pg_context.yml') -Destination (Join-Path $repo '.github\workflows\pg_refresh_pg_context.yml') -Force

  if ($DirtySnapshots) {
    $mojibakeCao = Join-Chars -Codes @(0x00C3, 0x00A7, 0x00C3, 0x00A3)
    $scopeSummary = "Integra${mojibakeCao}o de faturacao pronta para produ${mojibakeCao}o.`nBest regards,"
    $currentRequest = "Cliente pediu integra${mojibakeCao}o de faturacao com o ERP.`nOn Tue, 2 Apr 2026 at 10:00, Customer wrote:`n> Podem avancar."
    $acceptance = @('[PONTO POR VALIDAR]', 'Validar webhook GitHub', 'Validar webhook GitHub')
  }
  else {
    $scopeSummary = "Integracao de faturacao pronta para producao."
    $currentRequest = "Cliente pediu integracao de faturacao com o ERP."
    $acceptance = @('Validar webhook GitHub')
  }

  $scopePayload = [ordered]@{
    schema_version = '1.0'
    project_name = 'Projeto Hygiene'
    project_id = 99
    client_unit = 'Consulting'
    repository_summary = 'Repositorio piloto para validar higiene textual.'
    project_phase = 'delivery'
    odoo_version = '19.0'
    odoo_edition = 'community'
    odoo_environment = 'on_premise'
    restrictions = [ordered]@{
      standard_allowed = 'yes'
      additional_modules_allowed = 'yes'
      studio_allowed = 'yes'
      custom_allowed = 'yes'
      additional_contract_restrictions = @('Sem restricoes extra')
    }
    scope_overview = [ordered]@{
      business_goal = 'Automatizar faturacao.'
      current_request = $currentRequest
      current_process = 'Processo atual com validacao manual.'
      problem_or_need = 'Evitar retrabalho e ruido operacional.'
      business_impact = 'Menos erro manual e mais previsibilidade.'
      trigger = 'Pedido do cliente'
      frequency = 'Diaria'
      volumes = '50'
      urgency = 'high'
      acceptance_criteria = $acceptance
    }
    project_lists = [ordered]@{
      users_and_roles = @('PM', 'Consultor')
      known_exceptions = @('Sem excecoes')
      approvals = @('Aprovacao do cliente')
      documents = @('Documento funcional')
      integrations = @('GitHub')
      reporting_needs = @('Dashboard operacional')
      standard_attempted_or_validated = @('Configuracao standard revista')
      why_standard_was_insufficient = @('Necessidade de integracao externa')
    }
    scope_items = @(
      [ordered]@{
        task_id = 101
        task_name = 'Integracao faturacao'
        task_stage = 'Em Progresso'
        task_priority = '1'
        task_tags = @('integration')
        scope_track = 'approved_scope'
        scope_state = 'validated'
        scope_kind = 'integration'
        scope_sequence = 10
        scope_summary = $scopeSummary
        acceptance_criteria = $acceptance
        assigned_users = @('PM', 'PM')
        last_task_update_at = '2026-04-13 10:00:00'
        source_url = 'https://example.test/web#id=101&model=project.task'
      }
    )
    scope_summary = [ordered]@{
      active_scope_item_count = 1
      validated_scope_item_count = 1
      proposed_scope_item_count = 0
      deferred_scope_item_count = 0
      last_scope_change_at = '2026-04-13 10:00:00'
    }
    source_metadata = [ordered]@{
      source_system = 'odoo_parametro_global'
      source_model = 'project.project'
      source_record_id = 99
      source_record_url = 'https://example.test/web#id=99&model=project.project'
      sync_trigger = 'manual'
      sync_reason = 'manual publish'
      sync_published_at = '2026-04-13 10:05:00'
      sync_published_by = 'Test User'
      repo_branch = 'main'
      payload_hash = 'sha256:test-scope'
    }
  }

  Write-Utf8NoBomFile -Path (Join-Path $repo '.pg\PG_SCOPE_SYNC.json') -Content (($scopePayload | ConvertTo-Json -Depth 8) + "`n")

  return $repo
}

function Invoke-PowerShellScript {
  param(
    [string]$ScriptPath,
    [string[]]$Arguments
  )

  # ErrorActionPreference tem de baixar para Continue: no PS 5.1 o 2>&1 sobre um
  # executavel nativo embrulha cada linha de stderr num ErrorRecord, o que com
  # Stop aborta o harness antes de a assercao poder mostrar o output recolhido.
  $savedPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
  }
  finally {
    $ErrorActionPreference = $savedPreference
  }

  return [pscustomobject]@{
    Output = ($output | Out-String)
    ExitCode = $exitCode
  }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('pg_imp003_stage2_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
  $dirtyRepo = New-FixtureRepo -RootPath $tempRoot -Name 'dirty_repo' -DirtySnapshots
  $cleanRepo = New-FixtureRepo -RootPath $tempRoot -Name 'clean_repo'

  $dirtyRefresh = Invoke-PowerShellScript -ScriptPath (Join-Path $dirtyRepo '.pg_framework\scripts\pg_refresh_pg_context.ps1') -Arguments @('-RepoPath', $dirtyRepo)
  Assert-True -Condition ($dirtyRefresh.ExitCode -eq 0) -Message "Refresh falhou no fixture dirty: $($dirtyRefresh.Output)"

  $dirtyContext = Read-Utf8TextFile -Path (Join-Path $dirtyRepo 'PG_CONTEXT.md')
  $dirtyScopeBlock = Get-MarkedBlock -Text $dirtyContext -Marker 'SCOPE_ITEMS'
  $dirtyRequestBlock = Get-MarkedBlock -Text $dirtyContext -Marker 'PEDIDO_ATUAL'

  Assert-NotContains -Text $dirtyRequestBlock -Unexpected 'wrote:' -Message 'Quoted reply entrou no bloco PEDIDO_ATUAL.'
  Assert-NotContains -Text $dirtyScopeBlock -Unexpected '[PONTO POR VALIDAR]' -Message 'Placeholder residual entrou no bloco SCOPE_ITEMS.'

  $dirtySmoke = Invoke-PowerShellScript -ScriptPath (Join-Path $dirtyRepo '.pg_framework\scripts\pg_smoke_test_repo.ps1') -Arguments @('-RepoPath', $dirtyRepo)
  Assert-True -Condition ($dirtySmoke.ExitCode -eq 0) -Message "Smoke test falhou no fixture dirty: $($dirtySmoke.Output)"
  Assert-Contains -Text $dirtySmoke.Output -Expected 'mojibake' -Message 'Smoke test nao sinalizou mojibake no fixture dirty.'
  Assert-Contains -Text $dirtySmoke.Output -Expected 'quoted replies' -Message 'Smoke test nao sinalizou quoted replies no fixture dirty.'
  Assert-Contains -Text $dirtySmoke.Output -Expected 'assinatura' -Message 'Smoke test nao sinalizou assinatura no fixture dirty.'

  $cleanRefresh = Invoke-PowerShellScript -ScriptPath (Join-Path $cleanRepo '.pg_framework\scripts\pg_refresh_pg_context.ps1') -Arguments @('-RepoPath', $cleanRepo)
  Assert-True -Condition ($cleanRefresh.ExitCode -eq 0) -Message "Refresh falhou no fixture clean: $($cleanRefresh.Output)"

  $cleanSmoke = Invoke-PowerShellScript -ScriptPath (Join-Path $cleanRepo '.pg_framework\scripts\pg_smoke_test_repo.ps1') -Arguments @('-RepoPath', $cleanRepo)
  Assert-True -Condition ($cleanSmoke.ExitCode -eq 0) -Message "Smoke test falhou no fixture clean: $($cleanSmoke.Output)"
  Assert-False -Condition ($cleanSmoke.Output -like '*quoted replies*') -Message 'Smoke test limpo ainda sinalizou quoted replies.'
  Assert-False -Condition ($cleanSmoke.Output -like '*assinatura*') -Message 'Smoke test limpo ainda sinalizou assinatura.'
  Assert-False -Condition ($cleanSmoke.Output -like '*mojibake*') -Message 'Smoke test limpo ainda sinalizou mojibake.'
  Assert-False -Condition ($cleanSmoke.Output -like '*reaproveitamento defensivo insuficiente*') -Message 'Smoke test limpo ainda sinalizou truncagem insuficiente.'

  # --- Rotulos do PG_CONTEXT.md acentuados vs rotulos ASCII nos scripts -----
  # O template escreve "Versao do Odoo:" com til e "Edicao:" com cedilha; os
  # scripts pedem-nos em ASCII puro. Antes destes helpers a linha nunca casava e
  # o campo ficava em placeholder para sempre.
  $accentedVersionLabel = 'Vers' + (Join-Chars -Codes @(0x00E3)) + 'o do Odoo:'
  $accentedEditionLabel = 'Edi' + (Join-Chars -Codes @(0x00E7, 0x00E3)) + 'o:'
  $labelSample = "### Parametros Odoo ativos`r`n$accentedVersionLabel [PONTO POR VALIDAR]`r`n$accentedEditionLabel [PONTO POR VALIDAR]`r`nAmbiente: [PONTO POR VALIDAR]`r`n"

  Assert-True -Condition ((Get-PgLabeledValue -Text $labelSample -Label 'Versao do Odoo:') -eq '[PONTO POR VALIDAR]') -Message 'Get-PgLabeledValue nao leu o rotulo acentuado a partir do rotulo ASCII.'
  Assert-True -Condition (Test-PgLabelPresent -Text $labelSample -Label 'Edicao:') -Message 'Test-PgLabelPresent nao reconheceu o rotulo acentuado.'
  Assert-False -Condition (Test-PgLabelPresent -Text $labelSample -Label 'Path do core:') -Message 'Test-PgLabelPresent inventou um rotulo inexistente.'

  $labelUpdated = Set-PgLabeledValue -Text $labelSample -Label 'Versao do Odoo:' -Value '19.0'
  Assert-Contains -Text $labelUpdated -Expected ($accentedVersionLabel + ' 19.0') -Message 'Set-PgLabeledValue nao preencheu o valor no rotulo acentuado.'
  Assert-NotContains -Text $labelUpdated -Unexpected 'Versao do Odoo:' -Message 'Set-PgLabeledValue trocou o rotulo acentuado pela grafia ASCII.'
  Assert-Contains -Text $labelUpdated -Expected "19.0`r`n" -Message 'Set-PgLabeledValue perdeu o CR do fim de linha.'

  $labelEnsured = Ensure-PgLabeledValue -Text $labelUpdated -Label 'Versao do Odoo:' -Value '19.0'
  Assert-True -Condition (([regex]::Matches($labelEnsured, 'o do Odoo:')).Count -eq 1) -Message 'Ensure-PgLabeledValue duplicou um rotulo que ja existia.'

  $labelInserted = Ensure-PgLabeledValue -Text $labelSample -Label 'Path do core:' -Value 'C:\odoo_src\community' -InsertAfterLabel 'Ambiente:'
  Assert-Contains -Text $labelInserted -Expected "Ambiente: [PONTO POR VALIDAR]`r`nPath do core: C:\odoo_src\community" -Message 'Ensure-PgLabeledValue nao inseriu a linha depois da ancora.'

  # Valor com '$' nao pode ser lido como referencia de grupo na substituicao.
  $labelDollar = Set-PgLabeledValue -Text $labelSample -Label 'Ambiente:' -Value 'on_premise ($HOME)'
  Assert-Contains -Text $labelDollar -Expected 'Ambiente: on_premise ($HOME)' -Message 'Set-PgLabeledValue nao preservou um valor com $.'

  # --- Mojibake: pares reais contam, letras portuguesas legitimas nao ---------
  $legitimateAccents = 'Par' + (Join-Chars -Codes @(0x00E2)) + 'metros Odoo: itens em ' + (Join-Chars -Codes @(0x00E2)) + 'mbito.'
  Assert-True -Condition ((Get-PgTextMojibakeScore -Text $legitimateAccents) -eq 0) -Message 'Portugues correcto com circunflexo foi pontuado como mojibake.'
  Assert-False -Condition (Test-PgSuspiciousMojibake -Text $legitimateAccents) -Message 'Portugues correcto com circunflexo foi classificado como mojibake suspeito.'

  $templateContext = Read-Utf8TextFile -Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'templates\PG_CONTEXT.md')
  Assert-True -Condition ((Get-PgTextMojibakeScore -Text $templateContext) -eq 0) -Message 'templates/PG_CONTEXT.md pristino foi pontuado como mojibake.'

  $realMojibake = 'Integra' + (Join-Chars -Codes @(0x00C3, 0x00A7, 0x00C3, 0x00A3)) + 'o de faturacao.'
  Assert-True -Condition ((Get-PgTextMojibakeScore -Text $realMojibake) -ge 2) -Message 'Mojibake real deixou de ser pontuado.'
  Assert-True -Condition ((Get-PgTextMojibakeScore -Text (Join-Chars -Codes @(0xFFFD))) -eq 1) -Message 'U+FFFD deixou de valer por si como sinal de mojibake.'

  # --- Ponta a ponta: pg_sync_pg_context sobre o PG_CONTEXT.md do template ---
  $fakeSourceRoot = Join-Path $tempRoot 'odoo_src'
  $fakeCommunity = Join-Path $fakeSourceRoot 'community'
  $fakeEnterprise = Join-Path $fakeSourceRoot 'enterprise'
  New-Item -ItemType Directory -Path (Join-Path $fakeCommunity 'odoo') -Force | Out-Null
  New-Item -ItemType Directory -Path $fakeEnterprise -Force | Out-Null
  Write-Utf8NoBomFile -Path (Join-Path $fakeCommunity 'odoo\release.py') -Content "version_info = (19, 0, 0, 'final', 0, '')`n"

  $syncRepo = New-FixtureRepo -RootPath $tempRoot -Name 'sync_repo'
  $syncRun = Invoke-PowerShellScript -ScriptPath (Join-Path $syncRepo '.pg_framework\scripts\pg_sync_pg_context.ps1') -Arguments @('-RepoPath', $syncRepo, '-CommunityPath', $fakeCommunity, '-EnterprisePath', $fakeEnterprise, '-EditionHint', 'enterprise')
  Assert-True -Condition ($syncRun.ExitCode -eq 0) -Message "pg_sync_pg_context falhou no fixture: $($syncRun.Output)"

  $syncContext = Read-Utf8TextFile -Path (Join-Path $syncRepo 'PG_CONTEXT.md')
  Assert-Contains -Text $syncContext -Expected ($accentedVersionLabel + ' 19.0') -Message 'pg_sync_pg_context nao preencheu a versao no rotulo acentuado do template.'
  Assert-Contains -Text $syncContext -Expected ($accentedEditionLabel + ' Enterprise') -Message 'pg_sync_pg_context nao preencheu a edicao no rotulo acentuado do template.'
  Assert-Contains -Text $syncContext -Expected 'https://www.odoo.com/documentation/19.0/' -Message 'pg_sync_pg_context nao preencheu a documentacao oficial no rotulo acentuado do template.'
  Assert-Contains -Text $syncContext -Expected $fakeCommunity -Message 'pg_sync_pg_context nao registou o Path do core.'
  Assert-Contains -Text $syncContext -Expected $fakeEnterprise -Message 'pg_sync_pg_context nao registou o Path source Enterprise.'

  Write-Host 'OK: testes de higiene de contexto concluidos com sucesso'
}
finally {
  if (Test-Path $tempRoot) {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force
  }
}
