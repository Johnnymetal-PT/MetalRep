function Read-Utf8TextFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $targetPath = [System.IO.Path]::GetFullPath($Path)
  return [System.IO.File]::ReadAllText($targetPath, [System.Text.Encoding]::UTF8)
}

function Read-Utf8Lines {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $targetPath = [System.IO.Path]::GetFullPath($Path)
  return [System.IO.File]::ReadAllLines($targetPath, [System.Text.Encoding]::UTF8)
}

function Read-Utf8JsonFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  return (Read-Utf8TextFile -Path $Path | ConvertFrom-Json)
}

function Write-Utf8NoBomFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$Content
  )

  $targetPath = [System.IO.Path]::GetFullPath($Path)
  $directory = Split-Path -Parent $targetPath
  if ($directory -and -not (Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
  }

  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($targetPath, $Content, $encoding)
}

# ---------------------------------------------------------------------------
# Bloco gerido do .gitignore.
#
# O sync de assets partilhados copiava o .gitignore com Copy-Item -Force, o que
# DESTRUIA as regras proprias do projeto. Num repo .NET isso apagava
# '[Bb]in/', '[Oo]bj/' e '.vs/', e os artefactos de build passavam a ser
# versionados sem ninguem notar -- observado no PRIacademia. Como o bootstrap
# corre tipicamente DEPOIS de o repo do cliente ja ter codigo, o dano era a
# regra e nao a excepcao.
#
# A partir daqui as regras da framework vivem num bloco delimitado e tudo o que
# esta fora dele e do projeto: o sync so reescreve o bloco. Em repos antigos (sem
# marcadores) o conteudo existente e preservado como seccao do projeto e o bloco
# e acrescentado no fim.
# ---------------------------------------------------------------------------

$script:PgGitignoreBlockStart = '# >>> PG_FRAMEWORK:START (bloco gerido por pg_sync_shared_assets.ps1 - nao editar aqui)'
$script:PgGitignoreBlockEnd = '# <<< PG_FRAMEWORK:END (regras do projeto vao FORA deste bloco)'

function Get-PgGitignoreManagedBlock {
  param(
    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$FrameworkContent
  )

  $rules = ($FrameworkContent -replace "`r`n", "`n" -replace "`r", "`n").Trim("`n")
  return ($script:PgGitignoreBlockStart + "`n" + $rules + "`n" + $script:PgGitignoreBlockEnd)
}

# Devolve so as regras dentro do bloco gerido (sem marcadores), ou $null se o
# ficheiro nao tiver bloco. Usado pelo smoke test: com merge, o .gitignore deixa
# de ser byte-igual ao template, pelo que a paridade passa a ser do BLOCO.
function Get-PgGitignoreBlockRules {
  param([AllowNull()][string]$Content)

  if ([string]::IsNullOrEmpty($Content)) {
    return $null
  }

  $normalized = ($Content -replace "`r`n", "`n" -replace "`r", "`n")
  $pattern = [regex]::Escape($script:PgGitignoreBlockStart) + "`n(.*?)`n" + [regex]::Escape($script:PgGitignoreBlockEnd)
  $match = [regex]::Match($normalized, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  if (-not $match.Success) {
    return $null
  }

  return $match.Groups[1].Value.Trim("`n")
}

function Merge-PgGitignoreContent {
  param(
    [AllowNull()][string]$ExistingContent,
    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$FrameworkContent
  )

  $block = Get-PgGitignoreManagedBlock -FrameworkContent $FrameworkContent

  if ([string]::IsNullOrWhiteSpace($ExistingContent)) {
    return ($block + "`n")
  }

  $normalized = ($ExistingContent -replace "`r`n", "`n" -replace "`r", "`n")
  $pattern = [regex]::Escape($script:PgGitignoreBlockStart) + ".*?" + [regex]::Escape($script:PgGitignoreBlockEnd)
  if ([regex]::IsMatch($normalized, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
    # Substituicao por MatchEvaluator: um '$' numa regra do bloco seria lido como
    # referencia de grupo numa string de substituicao.
    $evaluator = { param($m) return $block }
    $merged = [regex]::Replace($normalized, $pattern, $evaluator, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    return ($merged.TrimEnd("`n") + "`n")
  }

  # Repo antigo, sem marcadores: tudo o que la esta e do projeto. Retira-se o que o
  # bloco passa a garantir, para nao ficar a mesma regra escrita duas vezes.
  #
  # A desduplicacao e por PARAGRAFO (grupos separados por linha vazia) e nao linha a
  # linha: retirar so as regras deixava atras os comentarios que as encabecavam, e o
  # ficheiro ficava com uma serie de titulos sem nada por baixo.
  $blockRules = @()
  foreach ($line in ($FrameworkContent -replace "`r`n", "`n" -replace "`r", "`n").Split("`n")) {
    $trimmed = $line.Trim()
    if (-not [string]::IsNullOrWhiteSpace($trimmed) -and -not $trimmed.StartsWith('#')) {
      $blockRules += $trimmed
    }
  }

  $keptParagraphs = New-Object System.Collections.ArrayList
  $paragraph = New-Object System.Collections.ArrayList

  function Add-PgGitignoreParagraph {
    param($Paragraph, $Kept, $BlockRules)

    if ($Paragraph.Count -eq 0) {
      return
    }

    $rules = @($Paragraph | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and -not $_.Trim().StartsWith('#') })
    $survivors = @($rules | Where-Object { $BlockRules -notcontains $_.Trim() })

    # Paragrafo cujas regras o bloco ja cobre (ou que nao tem regra nenhuma, sendo
    # so o comentario que as encabecava) desaparece por inteiro.
    if ($rules.Count -gt 0 -and $survivors.Count -eq 0) {
      return
    }
    if ($rules.Count -eq 0) {
      return
    }

    $lines = @($Paragraph | Where-Object { $BlockRules -notcontains $_.Trim() })
    [void]$Kept.Add(($lines -join "`n"))
  }

  foreach ($line in $normalized.Split("`n")) {
    if ([string]::IsNullOrWhiteSpace($line)) {
      Add-PgGitignoreParagraph -Paragraph $paragraph -Kept $keptParagraphs -BlockRules $blockRules
      $paragraph = New-Object System.Collections.ArrayList
      continue
    }
    [void]$paragraph.Add($line)
  }
  Add-PgGitignoreParagraph -Paragraph $paragraph -Kept $keptParagraphs -BlockRules $blockRules

  $projectSection = (($keptParagraphs -join "`n`n").Trim("`n"))
  if ([string]::IsNullOrWhiteSpace($projectSection)) {
    return ($block + "`n")
  }

  return ($projectSection + "`n`n" + $block + "`n")
}

# ---------------------------------------------------------------------------
# Rotulos do PG_CONTEXT.md (linhas no formato "Etiqueta: valor").
#
# Os templates escrevem os rotulos com acentuacao correcta ("Versao do Odoo:"
# leva til no primeiro "a", "Edicao:" leva cedilha), como manda a regra de
# redacao em portugues europeu de templates/AGENTS_SHARED.md. Os scripts, por
# seu lado, tem de se manter em ASCII puro (ver a nota do bloco de acentuacao
# mais abaixo: o Windows PowerShell 5.1 le .ps1 sem BOM como ANSI).
#
# Sem correspondencia insensivel a acentos as duas regras colidem: um
# Set-PgLabeledValue -Label 'Versao do Odoo:' nunca encontrava a linha
# acentuada do template e o campo ficava em placeholder para sempre. Por isso o
# padrao aceita as duas grafias, e a reescrita PRESERVA o rotulo tal como esta
# no ficheiro (nunca troca a versao acentuada pela ASCII).
# ---------------------------------------------------------------------------

$script:PgLabelAccentGroups = @(
  @{ Base = 'a'; Codes = @(0x00E0, 0x00E1, 0x00E2, 0x00E3, 0x00E4) },
  @{ Base = 'e'; Codes = @(0x00E8, 0x00E9, 0x00EA, 0x00EB) },
  @{ Base = 'i'; Codes = @(0x00EC, 0x00ED, 0x00EE, 0x00EF) },
  @{ Base = 'o'; Codes = @(0x00F2, 0x00F3, 0x00F4, 0x00F5, 0x00F6) },
  @{ Base = 'u'; Codes = @(0x00F9, 0x00FA, 0x00FB, 0x00FC) },
  @{ Base = 'c'; Codes = @(0x00E7) },
  @{ Base = 'n'; Codes = @(0x00F1) }
)

function Get-PgLabelEquivalenceMap {
  if ($null -ne $script:PgLabelEquivalenceMapCache) {
    return $script:PgLabelEquivalenceMapCache
  }

  # Hashtable ORDINAL: a de PowerShell (@{}) e case-insensitive, pelo que a
  # classe das maiusculas sobrescrevia a das minusculas e um rotulo com "a"
  # passava a exigir "A" no padrao (nada casava).
  $map = New-Object 'System.Collections.Hashtable' -ArgumentList @([System.StringComparer]::Ordinal)
  foreach ($group in $script:PgLabelAccentGroups) {
    $lowerClass = [string]$group.Base
    foreach ($code in $group.Codes) {
      $lowerClass += [string][char]$code
    }
    $upperClass = $lowerClass.ToUpperInvariant()

    foreach ($char in $lowerClass.ToCharArray()) {
      $map[[string]$char] = $lowerClass
    }
    foreach ($char in $upperClass.ToCharArray()) {
      $map[[string]$char] = $upperClass
    }
  }

  $script:PgLabelEquivalenceMapCache = $map
  return $map
}

# Fim de linha: em .NET, e mesmo em modo multiline, o '$' casa antes de '\n' mas
# NAO antes de '\r\n'. Um '[^\r\n]*$' nunca casaria num ficheiro CRLF (o codigo
# antigo escapava a isto com '.*$', porque o '.' engole o '\r' -- e depois perdia
# o CR na reescrita). O lookahead casa nos dois formatos e deixa o '\r' de fora
# do match, preservando o fim de linha original.
$script:PgLabelLineEndPattern = '(?=\r?$)'

# Converte "Versao do Odoo:" num padrao que casa tambem com "Vers<a-til>o do Odoo:".
function Get-PgLabelPattern {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label
  )

  $map = Get-PgLabelEquivalenceMap
  $builder = New-Object System.Text.StringBuilder
  foreach ($char in $Label.ToCharArray()) {
    $key = [string]$char
    if ($map.ContainsKey($key)) {
      [void]$builder.Append('[' + $map[$key] + ']')
    }
    else {
      [void]$builder.Append([regex]::Escape($key))
    }
  }

  return $builder.ToString()
}

function Test-PgLabelPresent {
  param(
    [AllowNull()][string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$Label
  )

  if ([string]::IsNullOrEmpty($Text)) {
    return $false
  }

  return [regex]::IsMatch($Text, "(?m)^" + (Get-PgLabelPattern -Label $Label) + "[^\r\n]*" + $script:PgLabelLineEndPattern)
}

function Get-PgLabeledValue {
  param(
    [AllowNull()][string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$Label
  )

  if ([string]::IsNullOrEmpty($Text)) {
    return $null
  }

  $match = [regex]::Match($Text, "(?m)^" + (Get-PgLabelPattern -Label $Label) + "[ \t]*([^\r\n]*)" + $script:PgLabelLineEndPattern)
  if ($match.Success) {
    return $match.Groups[1].Value.Trim()
  }

  return $null
}

# Substitui o valor de um rotulo existente. Nao cria a linha se ela nao existir
# (para isso existe Ensure-PgLabeledValue).
function Set-PgLabeledValue {
  param(
    [AllowNull()][string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [AllowEmptyString()][string]$Value
  )

  if ([string]::IsNullOrEmpty($Text)) {
    return $Text
  }

  $pattern = "(?m)^(" + (Get-PgLabelPattern -Label $Label) + ")[^\r\n]*" + $script:PgLabelLineEndPattern
  if (-not [regex]::IsMatch($Text, $pattern)) {
    return $Text
  }

  # MatchEvaluator (e nao string de substituicao) por duas razoes: preservar o
  # rotulo tal como aparece no ficheiro e evitar que um '$' no valor seja lido
  # como referencia de grupo.
  $evaluator = {
    param($match)

    return ($match.Groups[1].Value + " " + $Value)
  }

  return [regex]::Replace($Text, $pattern, $evaluator)
}

function Ensure-PgLabeledValue {
  param(
    [AllowNull()][string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [AllowEmptyString()][string]$Value,
    [string]$InsertAfterLabel
  )

  if (Test-PgLabelPresent -Text $Text -Label $Label) {
    return (Set-PgLabeledValue -Text $Text -Label $Label -Value $Value)
  }

  $newLine = [Environment]::NewLine + $Label + " " + $Value

  if ($InsertAfterLabel -and (Test-PgLabelPresent -Text $Text -Label $InsertAfterLabel)) {
    $anchor = [regex]::Match($Text, "(?m)^" + (Get-PgLabelPattern -Label $InsertAfterLabel) + "[^\r\n]*" + $script:PgLabelLineEndPattern)
    return $Text.Insert($anchor.Index + $anchor.Length, $newLine)
  }

  return $Text + $newLine
}

$script:PgPlaceholderPattern = '^\[?\s*(?:PONTO POR VALIDAR|PREENCHER|TODO|TBD|PLACEHOLDER|POR VALIDAR)(?:\s*[:\-].*)?\s*\]?$'
$script:PgReplyHeaderPattern = '^\s*(?:From|De|Sent|Enviado|To|Para|Subject|Assunto|Cc|Date|Data)\s*:'
$script:PgReplyWrotePattern = '^\s*(?:On|Em)\b.+\b(?:wrote|escreveu)\s*:\s*$'
$script:PgReplySeparatorPattern = '^\s*(?:-{2,}\s*(?:Original|Forwarded)\s+Message\s*-{2,}|_{5,})\s*$'
$script:PgSignaturePattern = '^\s*(?:--+|__+|Best regards[,]?|Kind regards[,]?|Regards[,]?|Cumprimentos[,]?|Atenciosamente[,]?|Thanks[,]?|Sent from my|Enviado do meu)\b'
# Mojibake real (UTF-8 lido como Latin-1/CP1252) aparece sempre em PARES: um
# caractere lider -- 0x00C3/0x00C2 ("A" com til / com circunflexo) para as
# sequencias de 2 bytes, 0x00E2 ("a" com circunflexo) para as de 3 -- seguido de
# outro caractere fora do ASCII, como em "A-til + cedilha" ou "a-circunflexo +
# euro + apostrofo". Contar lideres isolados dava falsos positivos em portugues
# CORRECTO: "Parametros" com circunflexo e "ambito" com circunflexo somavam 5
# pontos no proprio templates/PG_CONTEXT.md e todos os repos da frota ficavam com
# um WARN permanente de mojibake. Dai o par obrigatorio; o U+FFFD, que nunca e
# legitimo, continua a valer por si.
$script:PgMojibakeLeadCodes = @(0x00C3, 0x00C2, 0x00C4, 0x00C5, 0x00E2, 0x00D0, 0x00CC)
$script:PgMojibakeReplacementChar = [string][char]0xFFFD

function Get-PgMojibakePairPattern {
  if ($null -ne $script:PgMojibakePairPatternCache) {
    return $script:PgMojibakePairPatternCache
  }

  $leads = [string]::Concat(@($script:PgMojibakeLeadCodes | ForEach-Object { [char]$_ }))
  $script:PgMojibakePairPatternCache = '[' + $leads + '][^\x00-\x7F]'
  return $script:PgMojibakePairPatternCache
}

function Get-PgTextMojibakeScore {
  param([AllowNull()][string]$Text)

  if ([string]::IsNullOrEmpty($Text)) {
    return 0
  }

  $score = ([regex]::Matches($Text, (Get-PgMojibakePairPattern))).Count
  $score += ([regex]::Matches($Text, [regex]::Escape($script:PgMojibakeReplacementChar))).Count
  return $score
}

function Repair-PgCommonMojibake {
  param([AllowNull()][string]$Text)

  if ([string]::IsNullOrEmpty($Text)) {
    return ''
  }

  $bestText = $Text
  $bestScore = Get-PgTextMojibakeScore -Text $Text
  if ($bestScore -eq 0) {
    return $Text
  }

  $encodings = @(
    [System.Text.Encoding]::GetEncoding('iso-8859-1'),
    [System.Text.Encoding]::GetEncoding(1252)
  )

  foreach ($encoding in $encodings) {
    try {
      $bytes = $encoding.GetBytes($Text)
      $candidate = [System.Text.Encoding]::UTF8.GetString($bytes)
      $candidateScore = Get-PgTextMojibakeScore -Text $candidate
      if ($candidateScore -lt $bestScore) {
        $bestText = $candidate
        $bestScore = $candidateScore
      }
    }
    catch {
      continue
    }
  }

  return $bestText
}

function Test-PgSuspiciousMojibake {
  param([AllowNull()][string]$Text)

  $normalized = Repair-PgCommonMojibake -Text $Text
  return ((Get-PgTextMojibakeScore -Text $normalized) -ge 2) -or ($normalized -like "*$($script:PgMojibakeReplacementChar)*")
}

function Test-PgPlaceholderText {
  param([AllowNull()][string]$Text)

  return (-not [string]::IsNullOrWhiteSpace($Text)) -and [regex]::IsMatch($Text.Trim(), $script:PgPlaceholderPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
}

function Test-PgQuotedReplyText {
  param([AllowNull()][string]$Text)

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return $false
  }

  $meaningfulCount = 0
  foreach ($line in ($Text -replace "`r`n", "`n" -replace "`r", "`n").Split("`n")) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
      continue
    }
    if ($trimmed.StartsWith('>')) {
      if ($meaningfulCount -gt 0) {
        return $true
      }
      continue
    }
    if (
      [regex]::IsMatch($trimmed, $script:PgReplyHeaderPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) -or
      [regex]::IsMatch($trimmed, $script:PgReplyWrotePattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) -or
      [regex]::IsMatch($trimmed, $script:PgReplySeparatorPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    ) {
      return $true
    }
    $meaningfulCount += 1
  }

  return $false
}

function Test-PgSignatureText {
  param([AllowNull()][string]$Text)

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return $false
  }

  foreach ($line in ($Text -replace "`r`n", "`n" -replace "`r", "`n").Split("`n")) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
      continue
    }
    if ([regex]::IsMatch($trimmed, $script:PgSignaturePattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
      return $true
    }
  }

  return $false
}

function Normalize-PgText {
  param(
    [AllowNull()][string]$Text,
    [string]$Fallback = '',
    [int]$MaxChars = 0,
    [switch]$DropPlaceholders
  )

  $normalized = Repair-PgCommonMojibake -Text $Text
  if ($null -eq $normalized) {
    $normalized = ''
  }
  $normalized = [regex]::Replace($normalized, '\s+', ' ').Trim()

  if ($DropPlaceholders -and (Test-PgPlaceholderText -Text $normalized)) {
    $normalized = ''
  }

  if ($MaxChars -gt 0 -and $normalized.Length -gt $MaxChars) {
    if ($MaxChars -le 3) {
      $normalized = $normalized.Substring(0, $MaxChars)
    }
    else {
      $normalized = $normalized.Substring(0, $MaxChars - 3).TrimEnd(' ', ',', ';', ':') + '...'
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($normalized)) {
    return $normalized
  }

  return $Fallback
}

function Get-PgSanitizedLines {
  param(
    [AllowNull()][object[]]$Items,
    [switch]$StripEmailNoise,
    [switch]$DropPlaceholders,
    [int]$MaxItems = 0,
    [int]$MaxChars = 0
  )

  $rawLines = @()
  foreach ($item in @($Items)) {
    if ($null -eq $item) {
      continue
    }
    $parts = ([string]$item -replace "`r`n", "`n" -replace "`r", "`n").Split("`n")
    $rawLines += $parts
  }

  $candidateLines = @()
  $meaningfulCount = 0
  foreach ($line in $rawLines) {
    $trimmed = ([string]$line).Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
      continue
    }

    if ($StripEmailNoise) {
      if ($trimmed.StartsWith('>')) {
        if ($meaningfulCount -gt 0) {
          break
        }
        continue
      }

      if (
        [regex]::IsMatch($trimmed, $script:PgReplyHeaderPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) -or
        [regex]::IsMatch($trimmed, $script:PgReplyWrotePattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) -or
        [regex]::IsMatch($trimmed, $script:PgReplySeparatorPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
      ) {
        break
      }
    }

    $candidateLines += $trimmed
    $meaningfulCount += 1
  }

  $result = @()
  $seen = @{}
  $meaningfulCount = 0
  foreach ($line in $candidateLines) {
    if (
      $StripEmailNoise -and
      $meaningfulCount -gt 0 -and
      [regex]::IsMatch($line, $script:PgSignaturePattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    ) {
      break
    }

    $normalized = Normalize-PgText -Text $line.Trim(' ', '-', '*', "`t") -Fallback '' -MaxChars $MaxChars -DropPlaceholders:$DropPlaceholders
    if ([string]::IsNullOrWhiteSpace($normalized)) {
      continue
    }

    if (-not $seen.ContainsKey($normalized)) {
      $seen[$normalized] = $true
      $result += $normalized
      $meaningfulCount += 1
    }

    if ($MaxItems -gt 0 -and $result.Count -ge $MaxItems) {
      break
    }
  }

  return @($result)
}

function Convert-ToPgBulletLines {
  param(
    [AllowNull()][object[]]$Items,
    [string]$Fallback = '[PREENCHER]',
    [switch]$StripEmailNoise,
    [int]$MaxItems = 0,
    [int]$MaxChars = 0
  )

  $lines = Get-PgSanitizedLines -Items $Items -StripEmailNoise:$StripEmailNoise -DropPlaceholders -MaxItems $MaxItems -MaxChars $MaxChars
  if ($lines.Count -eq 0) {
    $lines = @($Fallback)
  }

  return (($lines | ForEach-Object { "- $_" }) -join "`r`n")
}

# ---------------------------------------------------------------------------
# Deteccao de portugues escrito em ASCII (acentuacao em falta).
#
# Este bloco apoia a regra "Regras de redacao em portugues europeu" definida em
# templates/AGENTS_SHARED.md. Cobre apenas perda de acentos na GERACAO de texto,
# nao mojibake/encoding (esse problema vive nos helpers Repair-PgCommonMojibake).
#
# O mapa de correcoes vive em pg_pt_accent_map.tsv (UTF-8) e e lido por
# Read-Utf8TextFile. Manter este .ps1 em ASCII puro: o Windows PowerShell 5.1 le
# scripts sem BOM como ANSI, pelo que caracteres acentuados no proprio script
# seriam corrompidos (mesma razao pela qual PgMojibakeHints usa [char]0x..).
# So entram correcoes SEM homografos (sem "esta"/"esta", "so"/"so", "e"/"e",
# "publico"/"publico"). O dominio parametro.global, paths e identificadores com
# ponto sao protegidos pelo PgAccentProtectedPattern, nao por exclusao no mapa.
# ---------------------------------------------------------------------------

$script:PgPortugueseAccentMapPath = Join-Path $PSScriptRoot 'pg_pt_accent_map.tsv'

function Get-PgPortugueseAccentMap {
  if ($null -ne $script:PgPortugueseAccentMapCache) {
    return $script:PgPortugueseAccentMapCache
  }

  $map = @{}
  if (Test-Path $script:PgPortugueseAccentMapPath) {
    foreach ($line in (Read-Utf8Lines -Path $script:PgPortugueseAccentMapPath)) {
      $trimmed = $line.Trim()
      if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('#')) {
        continue
      }
      $parts = $trimmed -split '\s+', 2
      if ($parts.Count -eq 2) {
        $map[$parts[0]] = $parts[1]
      }
    }
  }

  $script:PgPortugueseAccentMapCache = $map
  return $map
}

# Sufixos que, em portugues, quase sempre exigem acento. Usado apenas para WARN
# (recall extra), nunca para auto-fix, porque o termo exato nao foi verificado.
$script:PgPortugueseAccentHeuristicPattern = '^(?:[a-z]{2,}(?:cao|coes|ao)|[a-z]{3,}(?:ncia|ncias|avel|ivel|aveis|iveis))$'
# Intervalo Latin-1 (0x00C0-0x00FF) construido por codigo para manter o .ps1 em
# ASCII puro (o PS 5.1 le scripts sem BOM como ANSI). Mesma tatica de PgMojibakeHints.
$script:PgAccentWordPattern = "[A-Za-z$([char]0x00C0)-$([char]0x00FF)]+"
# Protege spans inline `assim`, URLs, emails, paths com barras, identificadores com
# ponto (dominios como parametro.global, paths e nomes de ficheiro como
# PG_SCOPE_SYNC.json) e identificadores snake_case (como odoo_parametro_global) para
# nao acentuar chaves.
#
# O alternativa de path com barras cobre os alvos de links markdown, que nao estao
# entre acentos graves: um `[texto](projects/pri-academia-reformulacao/PG_CONTEXT.md)`
# fazia o validador exigir acento em "reformulacao" DENTRO do path. Como os
# project_key sao slugs kebab-case derivados do nome portugues do projeto, isto era
# um falso positivo garantido em qualquer documento que ligasse a um artefacto
# namespaced -- e paths sao excepcao explicita da regra de acentuacao.
$script:PgAccentProtectedPattern = '`[^`]*`|https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.\w+|[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+|[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+|[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+'

function Get-PgCasedAccentReplacement {
  param(
    [string]$Token,
    [string]$Accented
  )

  if ($Token.Length -gt 0 -and [char]::IsUpper($Token[0])) {
    return ($Accented.Substring(0, 1).ToUpperInvariant() + $Accented.Substring(1))
  }
  return $Accented
}

# Percorre um texto multi-linha (markdown ou JSON) e devolve as palavras em
# portugues-ASCII. Ignora blocos de codigo cercados (``` / ~~~), spans inline
# `assim`, URLs e tokens TODO-MAIUSCULOS (acronimos/identificadores).
# Quando -ApplyFix, devolve tambem o texto corrigido (so com correcoes do mapa).
function Get-PgPortugueseAccentFindings {
  param(
    [AllowNull()][string]$Text,
    [switch]$ApplyFix
  )

  $findings = New-Object System.Collections.ArrayList
  $fixedLines = New-Object System.Collections.ArrayList

  if ([string]::IsNullOrEmpty($Text)) {
    return [pscustomobject]@{ Findings = @(); FixedText = ($Text) }
  }

  $map = Get-PgPortugueseAccentMap
  $lines = ($Text -replace "`r`n", "`n" -replace "`r", "`n").Split("`n")
  $inFence = $false
  $lineNumber = 0

  foreach ($line in $lines) {
    $lineNumber += 1
    $fenceTrim = $line.Trim()

    if ($fenceTrim -match '^(?:```|~~~)') {
      $inFence = -not $inFence
      [void]$fixedLines.Add($line)
      continue
    }
    if ($inFence) {
      [void]$fixedLines.Add($line)
      continue
    }

    $protected = New-Object System.Collections.ArrayList
    foreach ($pm in [regex]::Matches($line, $script:PgAccentProtectedPattern)) {
      [void]$protected.Add(@{ Start = $pm.Index; End = $pm.Index + $pm.Length })
    }

    $currentLineNumber = $lineNumber
    $evaluator = {
      param($m)

      $start = $m.Index
      foreach ($range in $protected) {
        if ($start -ge $range.Start -and $start -lt $range.End) {
          return $m.Value
        }
      }

      $token = $m.Value
      if ($token -ceq $token.ToUpperInvariant() -and $token.Length -gt 1) {
        return $token
      }

      $key = $token.ToLowerInvariant()
      if ($map.ContainsKey($key)) {
        $suggestion = Get-PgCasedAccentReplacement -Token $token -Accented $map[$key]
        [void]$findings.Add([pscustomobject]@{
            LineNumber = $currentLineNumber
            Word       = $token
            Suggestion = $suggestion
            Confidence = 'high'
          })
        if ($ApplyFix) {
          return $suggestion
        }
        return $token
      }

      if ($key -match $script:PgPortugueseAccentHeuristicPattern) {
        [void]$findings.Add([pscustomobject]@{
            LineNumber = $currentLineNumber
            Word       = $token
            Suggestion = ''
            Confidence = 'heuristic'
          })
      }
      return $token
    }

    $fixedLine = [regex]::Replace($line, $script:PgAccentWordPattern, $evaluator)
    [void]$fixedLines.Add($fixedLine)
  }

  $newline = "`n"
  if ($Text.Contains("`r`n")) {
    $newline = "`r`n"
  }

  return [pscustomobject]@{
    Findings  = @($findings)
    FixedText = ($fixedLines -join $newline)
  }
}

# Estado local da maquina que a framework declara como nunca versionavel. Lista
# EXPLICITA, e nao uma varredura pelas regras do bloco do .gitignore: o bloco tem
# padroes largos (`.vscode/`, `*.log`, `.idea/`) e um projeto pode versionar algum
# deles de proposito. Desversionar por inferencia apagaria trabalho alheio do indice.
$script:PgLocalStatePaths = @(
  # Regenerado a cada arranque por pg_preflight_context.ps1 e traz o path absoluto de
  # quem correu o preflight. A v2.20.0 acrescentou-o ao .gitignore do template, mas o
  # .gitignore nao desversiona o que ja esta seguido: ficava ignorado E seguido ao
  # mesmo tempo, a gerar conflito em cada merge e a viajar entre maquinas.
  '.pg/PREFLIGHT.json'
)

function Remove-PgTrackedLocalState {
  param([string]$RepoPath)

  $dentroDeGit = $false
  $anteriorTeste = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $inside = & git -C $RepoPath rev-parse --is-inside-work-tree 2> $null
    if ($LASTEXITCODE -eq 0 -and (($inside -join '').Trim() -eq 'true')) { $dentroDeGit = $true }
  }
  catch { $dentroDeGit = $false }
  finally { $ErrorActionPreference = $anteriorTeste }

  if (-not $dentroDeGit) { return @() }

  # ErrorActionPreference deste script e Stop; um executavel nativo a escrever no stderr
  # vira erro terminante. E `ls-files --error-unmatch` escreve mesmo ("error: pathspec ...
  # did not match") quando o ficheiro NAO esta seguido -- o caso normal na segunda
  # passagem. Sem esta guarda o sync passava a falhar depois de desversionar com sucesso.
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $removidos = @()
    foreach ($relativo in $script:PgLocalStatePaths) {
      # sem --error-unmatch: saida vazia ja significa "nao esta seguido", sem stderr
      $seguido = & git -C $RepoPath ls-files -- $relativo 2> $null
      if ([string]::IsNullOrWhiteSpace(($seguido -join ''))) { continue }

      # --cached: sai do indice, fica no disco. O ficheiro e estado local util; o que
      # nao pode e continuar versionado.
      & git -C $RepoPath rm --cached --quiet -- $relativo 2> $null | Out-Null
      if ($LASTEXITCODE -eq 0) {
        $removidos += $relativo
        Write-Host "OK: $relativo desversionado (estado local da maquina; fica no disco)"
      }
      else {
        Write-Host "AVISO: nao foi possivel desversionar $relativo; remover a mao com 'git rm --cached'"
      }
    }
  }
  finally {
    $ErrorActionPreference = $anterior
  }

  return $removidos
}

# ---------------------------------------------------------------------------
# Overrides locais do AGENTS.md / CLAUDE.md
# ---------------------------------------------------------------------------
#
# O AGENTS.md diz de si proprio que serve "para registar overrides locais quando
# existirem", e o sync copiava o template por cima dele com -Force, sem preservar nada
# -- enquanto o PG_CONTEXT.md e o PG_SCOPE_INTAKE.yaml eram preservados. A contradicao
# custou caro: `FACTO OBSERVADO` (givachoice, 11/08/2026) um re-sync apagou 41 linhas
# do AGENTS.md do projeto, precisamente a seccao que dizia onde estava o codigo vivo
# dos servidores. A equipa deixou de confiar no ficheiro e passou a guardar as regras
# locais em memorias do agente, que nao viajam com o repositorio.
#
# O padrao e o mesmo do .gitignore: o que e da framework vem do template, o que e do
# projeto vive num bloco delimitado e sobrevive ao sync.

$script:PgLocalOverridesHeading = '## Overrides locais do projeto'
$script:PgLocalOverridesPlaceholder = '[Sem overrides locais neste momento]'

function Get-PgLocalOverridesBlock {
  # Devolve o bloco de overrides (cabecalho inclusive) ou $null se nao houver nada
  # que valha a pena preservar.
  param([AllowNull()][string]$Content)

  if ([string]::IsNullOrWhiteSpace($Content)) { return $null }

  $normalized = ($Content -replace "`r`n", "`n" -replace "`r", "`n")
  $indice = $normalized.IndexOf($script:PgLocalOverridesHeading)
  if ($indice -lt 0) { return $null }

  $bloco = $normalized.Substring($indice).TrimEnd("`n")

  # O bloco por estrear -- so o cabecalho e o marcador de vazio -- nao e override
  # nenhum. Preserva-lo faria o sync reescrever o ficheiro sem necessidade.
  $corpo = $bloco.Substring($script:PgLocalOverridesHeading.Length)
  $corpo = ($corpo -replace [regex]::Escape($script:PgLocalOverridesPlaceholder), '')
  $corpo = ($corpo -replace '[-\s]', '')
  if ([string]::IsNullOrWhiteSpace($corpo)) { return $null }

  return $bloco
}

function Merge-PgLocalOverrides {
  # Conteudo do template com o bloco de overrides do projeto no fim.
  param(
    [AllowNull()][string]$ExistingContent,
    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$FrameworkContent
  )

  $bloco = Get-PgLocalOverridesBlock -Content $ExistingContent
  if ($null -eq $bloco) { return $FrameworkContent }

  $base = ($FrameworkContent -replace "`r`n", "`n" -replace "`r", "`n")
  $indice = $base.IndexOf($script:PgLocalOverridesHeading)
  if ($indice -ge 0) { $base = $base.Substring(0, $indice) }

  return ($base.TrimEnd("`n") + "`n`n" + $bloco + "`n")
}

# ---------------------------------------------------------------------------
# Drift entre o projeto e a framework (tarefa 8014)
#
# Ate 2026-10-08, "o projeto esta na versao corrente" era o HEAD do _pg_template ser
# igual ao registado em PG_TEMPLATE_SYNC_STATE.json. Qualquer commit na framework --
# um registo de defeitos, uma linha de documentacao -- punha a frota inteira em drift:
# o passo 2 re-sincronizava em cada projeto, deixava ficheiros por commitar, e o
# alinhador dava 0 de 34 repositorios na versao corrente por causa de um commit que nao
# mudava nada em nenhum deles.
#
# A pergunta certa e se mudou algum ficheiro de que o resultado do sync depende. Sao as
# fontes que o pg_sync_shared_assets.ps1 copia e o codigo que decide como as copia.
# Passo 2, preflight e alinhador usam esta mesma regra, para nao voltarem a divergir.
# ---------------------------------------------------------------------------
function Get-PgSyncSourcePaths {
  return @(
    'templates',
    'config.toml',
    'doc_templates',
    'scripts/pg_sync_shared_assets.ps1',
    'scripts/pg_file_io_common.ps1',
    'scripts/pg_link_framework.ps1'
  )
}

function Test-PgFrameworkSyncCurrent {
  # $true quando nenhum ficheiro que o sync usa mudou entre o head registado no projeto
  # e o head atual da framework. Head em falta, ou desconhecido neste clone, conta como
  # desatualizado: na duvida, re-sincroniza-se, que e idempotente.
  param(
    [string]$FrameworkPath,
    [string]$SyncedHead,
    [string]$CurrentHead
  )

  if ([string]::IsNullOrWhiteSpace($SyncedHead) -or [string]::IsNullOrWhiteSpace($CurrentHead)) { return $false }
  if ($SyncedHead.Trim() -eq $CurrentHead.Trim()) { return $true }

  # O git escreve no stderr quando o commit e desconhecido; com Stop isso abortaria o
  # chamador mesmo sendo um caso previsto.
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $argumentos = @('-C', $FrameworkPath, 'diff', '--quiet', $SyncedHead.Trim(), $CurrentHead.Trim(), '--') + (Get-PgSyncSourcePaths)
    & git @argumentos 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
  }
  catch {
    return $false
  }
  finally {
    $ErrorActionPreference = $anterior
  }
}

function Get-PgFrameworkManagedPaths {
  # Ficheiros que a framework escreve num projeto. O alinhador faz stage so destes, e o
  # preflight conta-os quando ficam por commitar.
  return @(
    'AGENTS.md', 'CLAUDE.md', 'config.toml',
    '.gitignore', '.editorconfig', '.gitattributes',
    '.claude', '.codex', '.agents', '.github',
    'doc_templates',
    '.pg/PG_TEMPLATE_SYNC_STATE.json',
    '.pg/tokens/consumption.jsonl'
  )
}
