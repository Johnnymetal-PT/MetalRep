param(
  [string]$BaseUrl = "https://parametroglobal.odoo.com",
  [string]$Database = "parametro-main-29950773",
  [string]$Login = "claudio.pereira@parametro.pt",
  [string]$WorkspaceXmlId = "pg_doc_templates.workspace_doc_templates",
  [string]$PythonExe = "python",
  [string]$FrameworkVersion = "v2.9.1",
  [string]$SimulatedPullJsonPath,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

$requiredTemplateCodes = @(
  "TPL_LEVANTAMENTO_AMBITO",
  "TPL_EMAIL_CLIENTE",
  "TPL_PROPOSTA_TECNICA",
  "TPL_PONTO_SITUACAO",
  "TPL_PONTO_SITUACAO_PPTX",
  "TPL_MIGRACAO_DADOS_ODOO",
  "TPL_CRIA_DEMO_DADOS_CLIENTE",
  "TPL_ORCAMENTO",
  "TPL_ORCAMENTO_PPTX",
  "TPL_MATRIZ_FUNCIONAL_RACI_EXECUTAVEL",
  "TPL_STATUS_SEMANAL_V1"
)

# Credencial do canal Knowledge — resolvida em cascata, nunca hardcoded neste ficheiro:
#   1. $env:PG_ODOO_KNOWLEDGE_TOKEN — override por sessão (é também o caminho do CI, via secret)
#   2. credentials/brodoo_credentials.json — segredo partilhado que vive no _pg_template privado
# O passo 2 existe porque o bootstrap de um projeto novo chama este script: obrigar a uma
# variável de ambiente por máquina fazia o onboarding falhar em qualquer máquina que não
# fosse a de quem definiu o token. Quem tem o framework passa a ter a credencial.
function Resolve-KnowledgeCredential {
  param([hashtable]$BoundParameters)

  $envToken = $env:PG_ODOO_KNOWLEDGE_TOKEN
  if (-not [string]::IsNullOrWhiteSpace($envToken)) {
    return @{
      ApiKey = $envToken
      Login = $Login
      BaseUrl = $BaseUrl
      Database = $Database
      Source = "env:PG_ODOO_KNOWLEDGE_TOKEN"
    }
  }

  $credentialsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "credentials\brodoo_credentials.json"
  if (Test-Path $credentialsPath) {
    $credentials = Read-Utf8TextFile -Path $credentialsPath | ConvertFrom-Json
    $apiKey = [string]$credentials.api_key
    if ((-not [string]::IsNullOrWhiteSpace($apiKey)) -and ($apiKey -notmatch "COLAR_AQUI")) {
      # Parâmetro explícito do chamador vence a credencial partilhada; o resto vem do ficheiro
      # para que login, url e base de dados fiquem coerentes entre si (chave de um utilizador
      # com o login de outro não autentica).
      return @{
        ApiKey = $apiKey
        Login = $(if ($BoundParameters.ContainsKey("Login")) { $Login } else { [string]$credentials.login })
        BaseUrl = $(if ($BoundParameters.ContainsKey("BaseUrl")) { $BaseUrl } else { [string]$credentials.url })
        Database = $(if ($BoundParameters.ContainsKey("Database")) { $Database } else { [string]$credentials.db })
        Source = "credentials/brodoo_credentials.json"
      }
    }
  }

  $mensagem = "Credencial do canal Knowledge indisponivel. Resolver por uma das vias: "
  $mensagem += "(1) definir `$env:PG_ODOO_KNOWLEDGE_TOKEN = '<api-key>' antes de correr; "
  $mensagem += "(2) preencher a api_key real em $credentialsPath (ver credentials/README.md)."
  throw $mensagem
}

function Remove-DirectoryIfExists {
  param([string]$Path)

  if (Test-Path $Path) {
    Remove-Item -Path $Path -Recurse -Force
  }
}

function Invoke-PythonPull {
  param(
    [string]$BaseUrl,
    [string]$Database,
    [string]$Login,
    [string]$ApiKey,
    [string]$WorkspaceXmlId,
    [string]$PythonExe
  )

  $apiKey = $ApiKey

  $scriptPath = Join-Path $PSScriptRoot "pg_doc_templates_common.py"
  if (-not (Test-Path $scriptPath)) {
    throw "Helper Python nao encontrado: $scriptPath"
  }

  $tempJsonPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_doc_templates_pull_{0}.json" -f [System.Guid]::NewGuid().ToString("N"))
  $logPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_doc_templates_pull_{0}.log" -f [System.Guid]::NewGuid().ToString("N"))

  # O stderr do helper vai para ficheiro em vez da consola: um traceback do Python sao ~50
  # linhas a vermelho por tentativa, e num bootstrap isso enterrava as mensagens que
  # interessam (o WARN de contencao e os passos seguintes). O que sobe e a ultima linha da
  # excepcao -- a que diz a causa -- com o caminho do log completo para quem precisar.
  # O ErrorActionPreference volta a Continue durante a chamada porque, com Stop, redirecionar
  # o stderr de um executavel nativo em PS 5.1 faz o proprio PowerShell lancar
  # NativeCommandError e mascarar o erro real do Python.
  $previousPreference = $ErrorActionPreference
  try {
    $env:PYTHONUTF8 = "1"
    $ErrorActionPreference = "Continue"
    & $PythonExe $scriptPath pull --base-url $BaseUrl --database $Database --login $Login --api-key $apiKey --workspace-xmlid $WorkspaceXmlId --output-file $tempJsonPath 2> $logPath | Out-Null
  }
  finally {
    $ErrorActionPreference = $previousPreference
    Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
  }

  if ($LASTEXITCODE -ne 0) {
    $causa = "sem detalhe no stderr"
    if (Test-Path $logPath) {
      $linhas = @(Get-Content -Path $logPath | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
      if ($linhas.Count -gt 0) {
        $causa = $linhas[-1].Trim()
      }
    }
    throw "helper Python falhou: $causa (traceback completo em $logPath)"
  }

  Remove-Item -Path $logPath -Force -ErrorAction SilentlyContinue

  if (-not (Test-Path $tempJsonPath)) {
    throw "Helper Python nao gerou o ficheiro de output esperado."
  }

  $jsonPayload = Read-Utf8TextFile -Path $tempJsonPath
  Remove-Item -Path $tempJsonPath -Force -ErrorAction SilentlyContinue
  return $jsonPayload
}

function Invoke-PythonPullWithFallback {
  param(
    [string]$BaseUrl,
    [string]$Database,
    [string]$Login,
    [string]$ApiKey,
    [string]$WorkspaceXmlId,
    [string]$PythonExe
  )

  # Um unico alvo: o que a cascata de credenciais resolveu. Os dois endpoints extra que aqui
  # estavam hardcoded estao mortos e so produziam ruido -- 'parametroglobal' responde
  # "Database not found" e o dev 'parametroglobal-dev-32714143' ja nao resolve em DNS. Cada
  # falha real custava assim tres tentativas e tres tracebacks, dois deles garantidamente
  # inuteis. A redundancia que interessa e outra e vive no helper: JSON-2 primeiro, JSON-RPC
  # como fallback. Para apontar a outro Odoo, passar -BaseUrl/-Database.
  $targets = @(@{ BaseUrl = $BaseUrl; Database = $Database })

  $errors = @()
  foreach ($target in $targets) {
    try {
      Write-Host ("INFO: tentativa pull doc templates em {0} / {1}" -f $target.BaseUrl, $target.Database)
      return Invoke-PythonPull `
        -BaseUrl $target.BaseUrl `
        -Database $target.Database `
        -Login $Login `
        -ApiKey $ApiKey `
        -WorkspaceXmlId $WorkspaceXmlId `
        -PythonExe $PythonExe
    }
    catch {
      $errors += ("{0} / {1} -> {2}" -f $target.BaseUrl, $target.Database, $_.Exception.Message)
      continue
    }
  }

  throw ("Falha ao obter doc templates (tentado JSON-2 e, em fallback, JSON-RPC). Tentativas: `n- " + ($errors -join "`n- "))
}

function Invoke-AssetExtraction {
  param(
    [string]$PythonExe,
    [string]$AssetsDir,
    [string]$OutputDir
  )

  $scriptPath = Join-Path $PSScriptRoot "pg_extract_doc_template_assets.py"
  if (-not (Test-Path $scriptPath)) {
    throw "Script de extracao de assets nao encontrado: $scriptPath"
  }

  if (-not (Test-Path $AssetsDir)) {
    return @{}
  }

  $assetFiles = Get-ChildItem -Path $AssetsDir -File -ErrorAction SilentlyContinue
  if (-not $assetFiles -or $assetFiles.Count -eq 0) {
    return @{}
  }

  $output = & $PythonExe $scriptPath --assets-dir $AssetsDir --output-dir $OutputDir
  if ($LASTEXITCODE -ne 0) {
    throw "Falha ao executar extracao de assets em $AssetsDir"
  }

  $parsed = $output | ConvertFrom-Json
  $map = @{}
  foreach ($item in @($parsed.extracted_assets)) {
    $map[[string]$item.asset_name] = @{
      txt_file = [string]$item.txt_file
      md_file = [string]$item.md_file
    }
  }
  return $map
}

function Get-TemplateRoot {
  return (Split-Path -Parent $PSScriptRoot)
}

# LF, e nao CRLF: o .gitattributes do framework impoe "*.md text eol=lf", pelo que e em LF
# que os TPL_*.md materializam em qualquer checkout, em qualquer sistema. Escrevendo CRLF,
# o sha256 gravado no MANIFEST era calculado sobre bytes que deixavam de existir no primeiro
# checkout seguinte, e o pg_smoke_test_repo.ps1 -- que compara com Get-FileHash cru -- acusava
# "hash mismatch" em todos os projetos.
function Convert-ToCanonicalTemplateContent {
  param([AllowNull()][string]$Content)

  if ($null -eq $Content) {
    return ""
  }

  return ($Content -replace "`r`n", "`n" -replace "`r", "`n")
}

# O manifest passa pelo pg_json_canonical.py para nao depender do shell: o ConvertTo-Json do
# Windows PowerShell 5.1 e o do PowerShell 7 formatam de maneira diferente e reescreviam o
# ficheiro inteiro consoante quem corria o pull. Aqui o PowerShell so produz JSON compacto
# (conteudo) e o Python fixa a forma (indentacao de 2 espacos, LF, nao-ASCII literal).
function Write-CanonicalJsonFile {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][object]$Payload,
    [Parameter(Mandatory = $true)][string]$PythonExe
  )

  $scriptPath = Join-Path $PSScriptRoot "pg_json_canonical.py"
  if (-not (Test-Path $scriptPath)) {
    throw "Canonicalizador de JSON nao encontrado: $scriptPath"
  }

  $compactPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_manifest_compact_{0}.json" -f [System.Guid]::NewGuid().ToString("N"))
  try {
    Write-Utf8NoBomFile -Path $compactPath -Content ($Payload | ConvertTo-Json -Depth 20 -Compress)
    $null = & $PythonExe $scriptPath --input $compactPath --output $Path
    if ($LASTEXITCODE -ne 0) {
      throw "Falha ao canonicalizar JSON com pg_json_canonical.py"
    }
  }
  finally {
    Remove-Item -Path $compactPath -Force -ErrorAction SilentlyContinue
  }
}

function Assert-TemplateEncodingQuality {
  param(
    [string]$TemplateCode,
    [string]$Content
  )

  # Mojibake patterns (UTF-8 interpreted as CP1252/Latin-1)
  # Examples: "Ã¡", "Ã§", "Ã£", "â€”", "â€™", "â€œ"
  $suspiciousPatterns = @(
    "\u00C3[\u0080-\u00BF]",
    "\u00E2[\u0080-\u00BF]{1,2}"
  )

  foreach ($pattern in $suspiciousPatterns) {
    if ([regex]::IsMatch($Content, $pattern)) {
      throw "Possivel corrupcao de encoding detetada no template ${TemplateCode} (padrao regex: $pattern)."
    }
  }
}

function Build-Manifest {
  param(
    [object[]]$Templates,
    [string]$FrameworkVersion,
    [string]$BaseUrl,
    [string]$Database,
    [string]$WorkspaceXmlId,
    [string]$StagingDir,
    [hashtable]$ExtractedAssetMap
  )

  $templateMap = [ordered]@{}

  foreach ($item in $Templates) {
    $article = $item.article
    $code = [string]$article.pg_template_code
    $templateFile = Join-Path $StagingDir ("{0}.md" -f $code)
    $templateSha = (Get-FileHash -Path $templateFile -Algorithm SHA256).Hash.ToLowerInvariant()

    $attachmentEntries = @()
    foreach ($attachment in @($item.attachments)) {
      $assetPath = Join-Path $StagingDir "assets\$($attachment.name)"
      $assetSha = $null
      if (Test-Path $assetPath) {
        $assetSha = (Get-FileHash -Path $assetPath -Algorithm SHA256).Hash.ToLowerInvariant()
      }
      $attachmentEntries += [ordered]@{
        id = $attachment.id
        name = $attachment.name
        path = "assets/$($attachment.name)"
        sha256 = $assetSha
        mimetype = $attachment.mimetype
        write_date = $attachment.write_date
        extracted_txt = $(if ($ExtractedAssetMap.ContainsKey([string]$attachment.name)) { "assets_extracted/$($ExtractedAssetMap[[string]$attachment.name].txt_file)" } else { $null })
        extracted_md = $(if ($ExtractedAssetMap.ContainsKey([string]$attachment.name)) { "assets_extracted/$($ExtractedAssetMap[[string]$attachment.name].md_file)" } else { $null })
      }
    }

    $templateMap[$code] = [ordered]@{
      article_id = $article.id
      version = $article.pg_template_version
      state = $article.pg_template_state
      file = "$code.md"
      sha256 = $templateSha
      write_uid = $article.write_uid
      write_date = $article.write_date
      attachments = $attachmentEntries
    }
  }

  return [ordered]@{
    schema_version = "1.0"
    generated_at = (Get-Date).ToString("o")
    framework_version = $FrameworkVersion
    source = [ordered]@{
      base_url = $BaseUrl
      database = $Database
      workspace_xmlid = $WorkspaceXmlId
      protocol = "json-rpc"
      endpoint = "/web/dataset/call_kw"
    }
    templates = $templateMap
  }
}

function Assert-RequiredTemplates {
  param(
    [object[]]$Templates,
    [string[]]$RequiredTemplateCodes
  )

  $present = @{}
  foreach ($item in $Templates) {
    $code = [string]$item.article.pg_template_code
    $present[$code] = $true
  }

  $missing = @()
  foreach ($code in $RequiredTemplateCodes) {
    if (-not $present.ContainsKey($code)) {
      $missing += $code
    }
  }

  if ($missing.Count -gt 0) {
    throw "Templates obrigatorios em falta no pull: $($missing -join ', ')"
  }
}

$templateRoot = Get-TemplateRoot
$docTemplatesDir = Join-Path $templateRoot "doc_templates"
$stagingDir = Join-Path $docTemplatesDir ".staging"
$stagingAssetsDir = Join-Path $stagingDir "assets"
$stagingExtractedDir = Join-Path $stagingDir "assets_extracted"
$manifestPath = Join-Path $docTemplatesDir "MANIFEST.json"
$backupDir = Join-Path $docTemplatesDir ".pull_backup"

Remove-DirectoryIfExists -Path $stagingDir
New-Item -ItemType Directory -Path $stagingAssetsDir -Force | Out-Null
New-Item -ItemType Directory -Path $stagingExtractedDir -Force | Out-Null

try {
  if ($SimulatedPullJsonPath) {
    Write-Host "WARN: modo simulado ativo via $SimulatedPullJsonPath"
    $rawPayload = Read-Utf8TextFile -Path $SimulatedPullJsonPath
  }
  else {
    # Resolver a credencial ANTES do loop de endpoints: sem ela, as tres tentativas falhavam
    # todas com a mesma mensagem e o erro real ficava enterrado em ruido.
    $credential = Resolve-KnowledgeCredential -BoundParameters $PSBoundParameters
    Write-Host ("INFO: credencial Knowledge via {0} (login {1})" -f $credential.Source, $credential.Login)

    $rawPayload = Invoke-PythonPullWithFallback `
      -BaseUrl $credential.BaseUrl `
      -Database $credential.Database `
      -Login $credential.Login `
      -ApiKey $credential.ApiKey `
      -WorkspaceXmlId $WorkspaceXmlId `
      -PythonExe $PythonExe
  }

  $payload = $rawPayload | ConvertFrom-Json
  $templates = @($payload.templates)

  Assert-RequiredTemplates -Templates $templates -RequiredTemplateCodes $requiredTemplateCodes

  foreach ($item in $templates) {
    $article = $item.article
    $code = [string]$article.pg_template_code
    $content = Convert-ToCanonicalTemplateContent -Content ([string]$article.pg_template_body_md)
    Assert-TemplateEncodingQuality -TemplateCode $code -Content $content
    Write-Utf8NoBomFile -Path (Join-Path $stagingDir "$code.md") -Content ($content + "`n")

    foreach ($attachment in @($item.attachments)) {
      if ([string]::IsNullOrWhiteSpace([string]$attachment.datas)) {
        continue
      }
      $bytes = [System.Convert]::FromBase64String([string]$attachment.datas)
      $targetPath = Join-Path $stagingAssetsDir ([string]$attachment.name)
      [System.IO.File]::WriteAllBytes($targetPath, $bytes)
    }
  }

  $extractedAssetMap = Invoke-AssetExtraction -PythonExe $PythonExe -AssetsDir $stagingAssetsDir -OutputDir $stagingExtractedDir

  $manifest = Build-Manifest `
    -Templates $templates `
    -FrameworkVersion $FrameworkVersion `
    -BaseUrl $BaseUrl `
    -Database $Database `
    -WorkspaceXmlId $WorkspaceXmlId `
    -StagingDir $stagingDir `
    -ExtractedAssetMap $extractedAssetMap

  $stagingManifestPath = Join-Path $stagingDir "MANIFEST.json"

  # Idempotencia ao nivel do ficheiro: se o pull nao trouxer mudanca nenhuma de conteudo,
  # o unico campo diferente seria o generated_at e o MANIFEST.json aparecia modificado a
  # cada bootstrap sem nada ter mudado -- ruido que convidava a commits vazios. Nesse caso
  # preserva-se o generated_at anterior e o promote fica um no-op.
  # Semantica do campo: quando o snapshot mudou, nao quando o pull correu. O sha256 de cada
  # template cobre todo o conteudo, pelo que "manifest igual" implica "snapshot igual".
  $existingGeneratedAt = $null
  if (Test-Path $manifestPath) {
    $existingGeneratedAt = [string]((Read-Utf8TextFile -Path $manifestPath | ConvertFrom-Json).generated_at)
  }

  Write-CanonicalJsonFile -Path $stagingManifestPath -Payload $manifest -PythonExe $PythonExe

  if (-not [string]::IsNullOrWhiteSpace($existingGeneratedAt)) {
    $freshGeneratedAt = [string]$manifest.generated_at
    $manifest.generated_at = $existingGeneratedAt
    $candidatePath = Join-Path $stagingDir "MANIFEST.candidate.json"
    Write-CanonicalJsonFile -Path $candidatePath -Payload $manifest -PythonExe $PythonExe

    # -ceq e nao -eq: o -eq do PowerShell e insensivel a maiusculas e mascararia uma
    # diferenca so de caixa (por exemplo num sha256 reescrito noutro formato).
    if ((Read-Utf8TextFile -Path $candidatePath) -ceq (Read-Utf8TextFile -Path $manifestPath)) {
      Copy-Item -Path $candidatePath -Destination $stagingManifestPath -Force
      Write-Host "INFO: snapshot sem alteracoes; generated_at preservado para o promote nao mexer no ficheiro"
    }
    else {
      $manifest.generated_at = $freshGeneratedAt
    }

    Remove-Item -Path $candidatePath -Force -ErrorAction SilentlyContinue
  }

  if ($DryRun) {
    Write-Host "OK: dry-run concluido. Staging valido em $stagingDir"
    Remove-DirectoryIfExists -Path $stagingDir
    return
  }

  Remove-DirectoryIfExists -Path $backupDir
  New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

  Get-ChildItem -Path $docTemplatesDir -File -Filter "TPL_*.md" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination (Join-Path $backupDir $_.Name) -Force
  }
  if (Test-Path (Join-Path $docTemplatesDir "assets")) {
    Copy-Item -Path (Join-Path $docTemplatesDir "assets") -Destination $backupDir -Recurse -Force
  }
  if (Test-Path (Join-Path $docTemplatesDir "assets_extracted")) {
    Copy-Item -Path (Join-Path $docTemplatesDir "assets_extracted") -Destination $backupDir -Recurse -Force
  }
  if (Test-Path $manifestPath) {
    Copy-Item -Path $manifestPath -Destination (Join-Path $backupDir "MANIFEST.json") -Force
  }

  Get-ChildItem -Path $docTemplatesDir -File -Filter "TPL_*.md" | Remove-Item -Force
  Remove-DirectoryIfExists -Path (Join-Path $docTemplatesDir "assets")
  Remove-DirectoryIfExists -Path (Join-Path $docTemplatesDir "assets_extracted")
  if (Test-Path $manifestPath) {
    Remove-Item -Path $manifestPath -Force
  }

  Get-ChildItem -Path $stagingDir -File -Filter "TPL_*.md" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination (Join-Path $docTemplatesDir $_.Name) -Force
  }
  if (Test-Path $stagingAssetsDir) {
    Copy-Item -Path $stagingAssetsDir -Destination (Join-Path $docTemplatesDir "assets") -Recurse -Force
  }
  if (Test-Path $stagingExtractedDir) {
    Copy-Item -Path $stagingExtractedDir -Destination (Join-Path $docTemplatesDir "assets_extracted") -Recurse -Force
  }
  Copy-Item -Path (Join-Path $stagingDir "MANIFEST.json") -Destination $manifestPath -Force

  Write-Host "OK: pull de doc templates concluido e promovido para $docTemplatesDir"
}
catch {
  Write-Host "ERROR: $($_.Exception.Message)"
  throw
}
finally {
  Remove-DirectoryIfExists -Path $stagingDir
  Remove-DirectoryIfExists -Path $backupDir
}
