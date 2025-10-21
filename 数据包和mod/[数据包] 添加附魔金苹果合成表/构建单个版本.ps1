# 数据包统一构建工具
$Host.UI.RawUI.WindowTitle = "数据包 - 构建单个版本"

Write-Host "========================================"
Write-Host "数据包统一构建工具"
Write-Host "========================================"
Write-Host ""

Write-Host "可用版本列表:"
python unified_pack.py --list

Write-Host ""
set /p version="请输入要构建的版本: "

if "%version%"=="" (
    Write-Host "错误: 未输入版本号"
    goto end
)

Write-Host ""
Write-Host "正在构建版本: %version%"
python unified_pack.py --version "%version%"

:end
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")