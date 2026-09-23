# Native PowerShell entrypoint. Review before executing; no administrator required.
[CmdletBinding()]
param([string]$Server = 'https://artifacts.botto.is', [switch]$NoPath)
$ErrorActionPreference = 'Stop'
$uri = [Uri]$Server
if ($uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.AbsolutePath -ne '/' -or $uri.Query -or $uri.Fragment) { throw 'Use an HTTPS server origin without a path or credentials.' }
$Server = $Server.TrimEnd('/')
Write-Host 'Margen - install/update for your Windows account: Codex, Claude Code, Hermes.'
Write-Host 'Each person connects their own account. No token is included or requested here.'
$pythonCommand = $null
$pythonArgs = @()
foreach ($candidate in @('py.exe','python.exe','python3.exe')) {
  $found = Get-Command $candidate -ErrorAction SilentlyContinue
  if (-not $found) { continue }
  $probeArgs = @()
  if ($candidate -eq 'py.exe') { $probeArgs = @('-3') }
  try {
    & $found.Source @probeArgs -X utf8 -c 'import sys; raise SystemExit(sys.version_info < (3,10))' 2>$null
    if ($LASTEXITCODE -eq 0) { $pythonCommand = $found.Source; $pythonArgs = $probeArgs; break }
  } catch { continue }
}
if (-not $pythonCommand) { throw 'Python 3.10+ is required. Install Python from python.org/downloads/windows/, reopen PowerShell and retry.' }
$temp = Join-Path ([IO.Path]::GetTempPath()) ('margen-install-'+[Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temp) | Out-Null
try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  $installer = Join-Path $temp 'install.py'
  Invoke-WebRequest -UseBasicParsing -Uri "$Server/install.py" -OutFile $installer -TimeoutSec 60
  & $pythonCommand @pythonArgs -X utf8 $installer --server $Server
  if ($LASTEXITCODE -ne 0) { throw "Margen installation failed (exit $LASTEXITCODE)." }
  $bin = Join-Path $HOME '.local\bin'
  if (-not $NoPath) {
    $userPath = [string][Environment]::GetEnvironmentVariable('Path','User')
    if (($userPath -split ';') -notcontains $bin) { [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';')+';'+$bin).TrimStart(';')), 'User') }
    if (($env:Path -split ';') -notcontains $bin) { $env:Path += ';'+$bin }
  }
  Write-Host 'Ready. Restart your agent and ask it to use margen. Update: margen update'
  Write-Host 'Connect your own account at the portal. Never paste a token into agent chat.'
} finally { Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue }
