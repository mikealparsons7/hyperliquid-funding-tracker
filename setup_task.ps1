$action = New-ScheduledTaskAction -Execute 'python' -Argument 'run_collector.py --once' -WorkingDirectory 'C:\Users\Mike Parsons\hyperliquid-funding-tracker'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName 'HyperliquidFunding' -Action $action -Trigger $trigger -Settings $settings -Description 'Fetch Hyperliquid funding rates every hour'
