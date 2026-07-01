$ErrorActionPreference = "Stop"

$Root = "C:\Users\wagne\Documents\Codex\2026-06-30\qy"
$Script = Join-Path $Root "work\auto_update_site_from_feeds.py"
$Log = Join-Path $Root "work\auto-update-task.log"

Set-Location $Root

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Iniciando atualizacao automatica" | Out-File -FilePath $Log -Encoding utf8 -Append
python $Script 2>&1 | Out-File -FilePath $Log -Encoding utf8 -Append
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Fim" | Out-File -FilePath $Log -Encoding utf8 -Append
