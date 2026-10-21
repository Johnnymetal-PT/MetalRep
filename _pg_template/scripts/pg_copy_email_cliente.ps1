<#
.SYNOPSIS
  Converte o rascunho markdown de um email ao cliente em HTML colavel no Odoo e
  deixa-o na area de transferencia, pronto a colar com Ctrl+V no compositor.

.DESCRIPTION
  Chama scripts/pg_build_email_cliente.py, que produz o HTML semantico que o
  editor do Odoo aceita (sem CSS: o atributo style nunca sobrevive a colagem).
  Alem de escrever o ficheiro .html para pre-visualizacao no browser, coloca o
  corpo na area de transferencia em dois formatos:

    - "HTML Format" (CF_HTML), que e o que o editor do Odoo le ao colar
    - texto simples, para campos sem formatacao

  Nota de codificacao: o texto atravessa um ficheiro JSON em UTF-8 escrito pelo
  Python e a area de transferencia recebe bytes UTF-8 explicitos. Passar por
  stdout do PS 5.1 estragaria os acentos.

.PARAMETER Path
  Ficheiro markdown do email (rascunho).

.PARAMETER Out
  Ficheiro HTML de saida. Por omissao, o mesmo caminho com extensao .html.

.PARAMETER NoClipboard
  Gera o .html mas nao toca na area de transferencia.

.PARAMETER ManterAssinatura
  Mantem o fecho e a assinatura escritos no rascunho. Por omissao sao retirados,
  porque o compositor do Odoo insere a assinatura do utilizador
  (res.users.signature) e repeti-la obriga a apagar a mao em cada envio.
  Usar quando o destino nao tem assinatura configurada.

.PARAMETER PythonExe
  Executavel Python a usar. Por omissao tenta py, python e python3.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_copy_email_cliente.ps1 -Path .\email_decisao.md
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Path,

  [string]$Out,

  [switch]$NoClipboard,

  [switch]$ManterAssinatura,

  [string]$PythonExe
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'pg_file_io_common.ps1')

function Resolve-PythonExe {
  param([string]$Preferred)

  $candidates = @()
  if ($Preferred) { $candidates += $Preferred }
  $candidates += @('py', 'python', 'python3')

  foreach ($candidate in $candidates) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($command) {
      $probe = & $candidate -c "import sys; sys.stdout.write('ok')" 2>$null
      if ($LASTEXITCODE -eq 0 -and $probe -eq 'ok') { return $candidate }
    }
  }
  throw "Python nao encontrado. Instala o Python 3 ou indica -PythonExe."
}

function New-CfHtml {
  <#
    Monta o cabecalho CF_HTML exigido pelo Windows. Os offsets sao contados em
    bytes UTF-8 a partir do inicio da string, por isso o cabecalho e construido
    primeiro com zeros para se saber o seu tamanho.
  #>
  param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Fragment)

  $utf8 = New-Object System.Text.UTF8Encoding($false)
  $template = "Version:0.9`r`nStartHTML:{0:D10}`r`nEndHTML:{1:D10}`r`nStartFragment:{2:D10}`r`nEndFragment:{3:D10}`r`n"
  $prefix = "<html><body>`r`n<!--StartFragment-->"
  $suffix = "<!--EndFragment-->`r`n</body></html>"

  $headerLength = $utf8.GetByteCount(($template -f 0, 0, 0, 0))
  $startHtml = $headerLength
  $startFragment = $startHtml + $utf8.GetByteCount($prefix)
  $endFragment = $startFragment + $utf8.GetByteCount($Fragment)
  $endHtml = $endFragment + $utf8.GetByteCount($suffix)

  return ($template -f $startHtml, $endHtml, $startFragment, $endFragment) + $prefix + $Fragment + $suffix
}

function Set-ClipboardHtml {
  param(
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Html,
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text
  )

  Add-Type -AssemblyName System.Windows.Forms | Out-Null

  $cfHtml = New-CfHtml -Fragment $Html
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($cfHtml)
  $stream = New-Object System.IO.MemoryStream
  $stream.Write($bytes, 0, $bytes.Length)
  $stream.Position = 0

  $dataObject = New-Object System.Windows.Forms.DataObject
  # O stream de bytes UTF-8 e obrigatorio: passar a string directamente faz o
  # .NET Framework escrever o HTML com a codificacao errada e estraga acentos.
  $dataObject.SetData('HTML Format', $false, $stream)
  $dataObject.SetData([System.Windows.Forms.DataFormats]::UnicodeText, $true, $Text)
  [System.Windows.Forms.Clipboard]::SetDataObject($dataObject, $true)

  # Confirmar que o formato HTML ficou registado. Nota: o GetData do .NET
  # Framework descodifica o "HTML Format" com a codepage ANSI e devolve acentos
  # estragados, por isso esta verificacao so pode olhar para marcas ASCII. Os
  # bytes na area de transferencia continuam em UTF-8 correcto (verificado com
  # leitura crua via Win32).
  $lido = [System.Windows.Forms.Clipboard]::GetData('HTML Format')
  if ($lido -is [System.IO.Stream]) {
    $buffer = New-Object byte[] $lido.Length
    $null = $lido.Read($buffer, 0, $buffer.Length)
    $lido = [System.Text.Encoding]::UTF8.GetString($buffer)
  }
  if (-not $lido -or ($lido -notlike '*<!--StartFragment-->*')) {
    throw "A area de transferencia nao aceitou o formato HTML."
  }
  return $true
}

# ---------------------------------------------------------------------------
# A area de transferencia exige um thread STA. O PowerShell 5.1 arranca em STA,
# mas o host pode ser MTA (ex.: runspaces, pwsh -MTA); nesse caso relanca-se.
# ---------------------------------------------------------------------------
if (-not $NoClipboard -and [System.Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') {
  $relaunch = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Sta', '-File', $PSCommandPath, '-Path', $Path)
  if ($Out) { $relaunch += @('-Out', $Out) }
  if ($ManterAssinatura) { $relaunch += '-ManterAssinatura' }
  if ($PythonExe) { $relaunch += @('-PythonExe', $PythonExe) }
  & powershell.exe @relaunch
  exit $LASTEXITCODE
}

$mdPath = [System.IO.Path]::GetFullPath($Path)
if (-not (Test-Path -LiteralPath $mdPath -PathType Leaf)) {
  throw "Ficheiro markdown nao encontrado: $mdPath"
}

$builder = Join-Path $PSScriptRoot 'pg_build_email_cliente.py'
if (-not (Test-Path -LiteralPath $builder -PathType Leaf)) {
  throw "Conversor nao encontrado: $builder"
}

$python = Resolve-PythonExe -Preferred $PythonExe
$outPath = if ($Out) { [System.IO.Path]::GetFullPath($Out) } else { [System.IO.Path]::ChangeExtension($mdPath, '.html') }
$jsonPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_email_" + [guid]::NewGuid().ToString('N') + ".json")

try {
  $builderArgs = @('--md', $mdPath, '--out', $outPath, '--json', $jsonPath)
  if ($ManterAssinatura) { $builderArgs += '--manter-assinatura' }
  $null = & $python $builder @builderArgs
  if ($LASTEXITCODE -ne 0) {
    throw "O conversor terminou com erro (codigo $LASTEXITCODE)."
  }

  $dados = Read-Utf8JsonFile -Path $jsonPath

  Write-Host "HTML colavel : $($dados.html)"
  if ($dados.assunto) { Write-Host "Assunto      : $($dados.assunto)" }
  foreach ($chave in @('para', 'cc', 'bcc')) {
    $valor = $dados.cabecalho.$chave
    if ($valor) { Write-Host ("{0,-13}: {1}" -f $chave.ToUpper(), $valor) }
  }

  if ($NoClipboard) {
    Write-Host "Area de transferencia: nao alterada (-NoClipboard)."
  }
  else {
    $null = Set-ClipboardHtml -Html $dados.fragmento -Text $dados.texto
    Write-Host "Area de transferencia: corpo do email pronto. Cola no Odoo com Ctrl+V."
  }

  if ($dados.avisos -and $dados.avisos.Count -gt 0) {
    Write-Host ""
    foreach ($aviso in $dados.avisos) { Write-Host "AVISO: $aviso" }
  }
}
finally {
  if (Test-Path -LiteralPath $jsonPath) { Remove-Item -LiteralPath $jsonPath -Force -ErrorAction SilentlyContinue }
}

exit 0
