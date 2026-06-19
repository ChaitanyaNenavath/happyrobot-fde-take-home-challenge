$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$apiCommand = "Set-Location '$root\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$uiCommand = '$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS=''false''; Set-Location ''{0}''; python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false' -f $root

Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", $apiCommand
Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", $uiCommand

Write-Host "API: http://127.0.0.1:8000"
Write-Host "UI:  http://127.0.0.1:8501"
