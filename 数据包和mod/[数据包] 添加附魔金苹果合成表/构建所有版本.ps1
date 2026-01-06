# 数据包统一构建工具
$Host.UI.RawUI.WindowTitle = "数据包 - 构建所有版本"

Write-Host "========================================"
Write-Host "数据包统一构建工具"
Write-Host "========================================"
Write-Host ""

# 获取脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptDir "unified_pack.py"

python $pythonScript

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")