

$DestDir = "..\urbanair_backend"
$IntervalSeconds = 1800   # 30 minutes -- change this if you want a different sync frequency
$FilesToSync = @("traffic_log.csv", "weather_current_log.csv", "live_pollutants_log.csv", "live_ground_aqi_log.csv")

if (-not (Test-Path $DestDir)) {
    Write-Host "ERROR: $DestDir not found. Run this script from inside aqi_model\." -ForegroundColor Red
    exit 1
}

Write-Host "Starting log sync -> $DestDir every $($IntervalSeconds / 60) min. Press Ctrl+C to stop."

while ($true) {
    $synced = @()
    foreach ($file in $FilesToSync) {
        if (Test-Path $file) {
            Copy-Item -Path $file -Destination $DestDir -Force
            $synced += $file
        }
    }
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    if ($synced.Count -gt 0) {
        Write-Host "[$timestamp] synced: $($synced -join ', ')"
    } else {
        Write-Host "[$timestamp] WARNING: no source CSVs found yet, skipping this round"
    }
    Start-Sleep -Seconds $IntervalSeconds
}