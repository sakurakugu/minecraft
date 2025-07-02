# 这是一个 PowerShell 脚本，用于将 Minecraft 存档文件夹链接到版本文件夹
# 以便在不同版本之间共享存档和其他资源。
# 上次编辑时间：2025年6月30日 23:45
# 作者：Sakurakugu

# 设置主目录
$MC_根目录 = "D:\Software\Games\我的世界\.minecraft"
$官方MC_根目录 = "$env:APPDATA\.minecraft"
$待处理的目录 = [System.Collections.ArrayList]::new()
$目标存档路径 = Join-Path $MC_根目录 "saves"
$含mod但也处理的存档目录 = @(
    "1.21.6-Fabric 0.16.14",
    "1.21.7-Fabric 0.16.14"
)
$要链接的文件夹 = @(
    "resourcepacks", # 资源包
    "shaderpacks",   # 光影
    "backups",       # 备份
    "saves",         # 存档
    "schematics",    # 投影mod
    "screenshots"    # 截图
)

# 函数：输出日志
function Write-Log {
    param (
        [string]$Level,
        [string]$Message
    )

    switch ($Level.ToUpper()) {
        "INFO" {
            Write-Host "[" -NoNewline
            Write-Host "信息" -ForegroundColor Green -NoNewline
            Write-Host "] " -NoNewline
            Write-Host $Message
        }
        "WARN" {
            Write-Host "[" -NoNewline
            Write-Host "警告" -ForegroundColor Yellow -NoNewline
            Write-Host "] " -NoNewline
            Write-Host $Message
        }
        "NOTICE" {
            Write-Host "[" -NoNewline
            Write-Host "注意" -ForegroundColor Yellow -NoNewline
            Write-Host "] " -NoNewline
            Write-Host $Message
        }
        "ERROR" {
            Write-Host "[" -NoNewline
            Write-Host "错误" -ForegroundColor Red -NoNewline
            Write-Host "] " -NoNewline
            Write-Host $Message
        }
        "DEBUG" {
            Write-Host "[" -NoNewline
            Write-Host "调试" -ForegroundColor DarkYellow -NoNewline
            Write-Host "] " -NoNewline
            Write-Host $Message
        }
        default {
            Write-Host "[日志] $Message" -ForegroundColor Gray
        }
    }
}

# 函数：创建符号链接
function 创建软链接 {
    param (
        [string]$待创路径,
        [string]$目标路径
    )
    if (Test-Path -LiteralPath $待创路径) {
        if (-not (Get-Item $待创路径).LinkType) {
            Remove-Item -Recurse -Force $待创路径
        } else {
            # Write-Log -Message "路径 `"$待创路径`" 已是符号链接，跳过"
            Write-Log -Message "目录 `"$((Get-Item $待创路径).Name)`" 已是符号链接，跳过"
            return
        }
    }
    $result = cmd /c mklink /D "`"$待创路径`"" "`"$目标路径`"" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log -Level "ERROR" -Message "创建符号链接失败：$result"
        Write-Log -Level "ERROR" -Message "请检查权限或路径是否正确。"
    }
    else {
        Write-Log -Message "创建符号链接成功：`"$待创路径`" ===>> `"$目标路径`""
    }
}

# 函数：移动文件夹内容并处理重名
function 移动文件夹内容 {
    param (
        [string]$源路径,
        [string]$目标路径,
        [string]$版本名字 = ""
    )
    # 获取所有项目（包括文件夹和文件）
    $所有项目 = Get-ChildItem -Path $源路径
    foreach ($项目 in $所有项目) {
        # 对于 .minecraft\文件夹 的内容，只进行重名检测
        # 对于来自 .minecraft\versions\<版本名>\文件夹 的内容，先将版本名追加到名称后，然后再检测重名并移动
        $原始名称 = $项目.Name
        
        # 对于文件，保持原始扩展名
        if ($项目.PSIsContainer) {
            # 文件夹处理：先去除结尾的(数字)
            $项目名 = $原始名称 -replace '\s\(\d+\)$', ''
            # 如果是来自版本目录的项目，并且没有" [版本名]"作为后缀，则添加后缀
            if ($版本名字 -ne "") {
                if (-not ($项目名 -match "\s\[[^\[\]]+\]$")) {
                    $项目名 = "$项目名 [$版本名字]"
                }
            }
        } else {
            # 文件处理：分离文件名和扩展名
            $文件名 = [System.IO.Path]::GetFileNameWithoutExtension($原始名称)
            $扩展名 = [System.IO.Path]::GetExtension($原始名称)
            # 先去除结尾的(数字)
            $文件名 = $文件名 -replace '\s\(\d+\)$', ''
            # 如果是来自版本目录的文件，并且没有" [版本名]"作为后缀，则添加后缀
            if ($版本名字 -ne "") {
                if (-not ($文件名 -match "\s\[[^\[\]]+\]$")) {
                    $文件名 = "$文件名 [$版本名字]"
                }
            }
            $项目名 = "$文件名$扩展名"
        }
        
        $项目路径 = Join-Path $目标路径 $项目名
        # 检查项目路径是否已存在,如果存在，则添加 "(数字)" 后缀
        $count = 1
        while (Test-Path -LiteralPath $项目路径) {
            if ($项目.PSIsContainer) {
                $项目路径 = Join-Path $目标路径 "$项目名 ($count)"
            } else {
                $文件名 = [System.IO.Path]::GetFileNameWithoutExtension($项目名)
                $扩展名 = [System.IO.Path]::GetExtension($项目名)
                $项目路径 = Join-Path $目标路径 "$文件名 ($count)$扩展名"
            }
            $count++
        }
        Write-Log -Level "INFO" -Message "移动 `"$($项目.Name)`" 到 `"$项目路径`"..."
        Move-Item -LiteralPath $项目.FullName -Destination $项目路径
    }
}

# 函数：处理文件夹目录
function 处理文件夹目录 {
    param (
        [string]$源目录,
        [string]$文件夹类型,
        [string]$目标文件夹路径,
        [string]$版本名字 = ""
    )
    $源文件夹路径 = Join-Path $源目录 $文件夹类型
    if (Test-Path -LiteralPath $源文件夹路径) {
        if (-not (Get-Item $源文件夹路径).LinkType) {
            Write-Log -Level "INFO" -Message "正在移动 `"$源文件夹路径`" 中的内容到 `"$目标文件夹路径`"..."
            移动文件夹内容 -源路径 $源文件夹路径 -目标路径 $目标文件夹路径 -版本名字 $版本名字
        }
    } else {
        Write-Log -Level "INFO" -Message "路径 `"$文件夹类型`" 不存在，正在创建..."
    }
    创建软链接 -待创路径 $源文件夹路径 -目标路径 $目标文件夹路径
}

# 函数：添加待处理的目录到列表
function 添加待处理的目录到列表 {
    $版本目录 = Join-Path $MC_根目录 "versions"
    if (Test-Path -LiteralPath $版本目录) {
        Get-ChildItem -Path $版本目录 -Directory | ForEach-Object {
            # 如果不是纯原版，且不属于含mod但也处理的存档目录，则添加到列表
            $版本名 = $_.Name
            $mod文件夹路径 = Join-Path $_.FullName "mods"
            if (Test-Path -LiteralPath $mod文件夹路径) {
                # 如果属于含mod但也处理的存档目录，则不跳过
                if (-not ($含mod但也处理的存档目录 -contains $版本名)) {
                    Write-Log -Message "该版本 $版本名 存在mod文件夹，跳过文件夹处理"
                    return
                }
            }
            $待处理的目录.Add($_.FullName) | Out-Null
        }
    }
    if($MC_根目录 -ne $官方MC_根目录) {
        $待处理的目录.Add($官方MC_根目录) | Out-Null
        $版本目录 = Join-Path $官方MC_根目录 "versions"
        if (Test-Path -LiteralPath $版本目录) {
            Get-ChildItem -Path $版本目录 -Directory | ForEach-Object {
                # 如果不是纯原版，且不属于含mod但也处理的存档目录，则添加到列表
                $版本名 = $_.Name
                $mod文件夹路径 = Join-Path $_.FullName "mods"
                if (Test-Path -LiteralPath $mod文件夹路径) {
                    # 如果属于含mod但也处理的存档目录，则不跳过
                    if (-not ($含mod但也处理的存档目录 -contains $版本名)) {
                        Write-Log -Message "该版本 $版本名 存在mod文件夹，跳过文件夹处理"
                        return
                    }
                }
                $待处理的目录.Add($_.FullName) | Out-Null
            }
        }
    }
}

function main {
    # 为每个要链接的文件夹类型创建目标目录（如果不存在）
    foreach ($文件夹类型 in $要链接的文件夹) {
        $目标路径 = Join-Path $MC_根目录 $文件夹类型
        if (-not (Test-Path -LiteralPath $目标路径)) {
            New-Item -ItemType Directory -Path $目标路径 | Out-Null
        }
    }
    
    添加待处理的目录到列表
    
    foreach ($目录 in $待处理的目录) {
        Write-Log -Level "INFO" -Message "正在处理目录 `"$($目录)`"..."
        
        # 获取版本名称（如果是版本目录）
        $版本名字 = ""
        if ($目录 -ne $MC_根目录 -and $目录 -ne $官方MC_根目录) {
            $版本名字 = (Get-Item $目录).Name
        }
        
        # 处理每个文件夹类型
        foreach ($文件夹类型 in $要链接的文件夹) {
            $目标路径 = Join-Path $MC_根目录 $文件夹类型
            处理文件夹目录 -源目录 $目录 -文件夹类型 $文件夹类型 -目标文件夹路径 $目标路径 -版本名字 $版本名字
        }
    }
}

main