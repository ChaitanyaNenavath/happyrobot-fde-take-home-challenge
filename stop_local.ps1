$ports = 8000, 8501

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        try {
            Stop-Process -Id $connection.OwningProcess -Force -ErrorAction Stop
            Write-Host "Stopped process $($connection.OwningProcess) on port $port"
        } catch {
            Write-Host "Could not stop process $($connection.OwningProcess) on port $port"
        }
    }
}
