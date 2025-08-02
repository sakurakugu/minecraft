
# -*- coding: utf-8 -*-
"""
这是一个 Python 脚本，用于将 Minecraft 存档文件夹链接到版本文件夹
以便在不同版本之间共享存档和其他资源。
上次编辑时间：2025年7月10日
作者：Sakurakugu
"""

import os
import shutil
import platform
import re
import subprocess
import ctypes

# 设置主目录
MC_根目录 = "D:\\Software\\Games\\我的世界\\.minecraft"
官方MC_根目录 = os.path.join(os.environ.get('APPDATA', ''), '.minecraft')
待处理的目录 = []
目标存档路径 = os.path.join(MC_根目录, "saves")
含mod但也处理的存档目录 = [
    "1.21.8-Fabric 0.16.14"
]
要链接的文件夹 = [
    "resourcepacks",  # 资源包
    "shaderpacks",    # 光影
    "backups",        # 备份
    "saves",          # 存档
    "schematics",     # 投影mod
    "screenshots"     # 截图
]

# 配置日志输出
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
try:
    from lib.log import logging, set_log_path, set_log_level, setup_logging
    set_log_path(os.path.join(log_dir, '版本隔离.log')) # 设置自定义日志文件名
    set_log_level(logging.INFO) # 设置日志级别
    setup_logging() # 重新设置日志配置
except ImportError:
    import os
    import logging
    # 确保日志目录存在（相对于脚本文件位置）
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level="DEBUG",
        handlers=[
            logging.StreamHandler(), 
            logging.FileHandler(os.path.join(log_dir, '版本隔离.log'), encoding='utf-8')
        ],
        format='%(asctime)s - %(levelname)-8s - %(lineno)-3d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
# logging.info("-"*50)

# 函数：创建符号链接
def 创建软链接(待创路径, 目标路径):
    """创建符号链接"""
    if os.path.exists(待创路径):
        if not isLink(待创路径):
        # if not os.path.islink(待创路径):
            if os.path.isdir(待创路径):
                shutil.rmtree(待创路径)
            else:
                os.remove(待创路径)
        else:
            logging.debug(f"目录 \"{os.path.basename(待创路径)}\" 已是符号链接，跳过")
            return
    
    try:
        # 在Windows上创建目录符号链接
        if platform.system() == "Windows":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/D", 待创路径, 目标路径],
                capture_output=True,
                text=True,
                encoding='gbk'
            )
            if result.returncode != 0:
                logging.error(f"创建符号链接失败：{result.stderr}")
                logging.error("请检查权限或路径是否正确。")
            else:
                logging.info(f"创建符号链接成功：\"{待创路径}\" ===>> \"{目标路径}\"")
        else:
            # 在Unix-like系统上使用os.symlink
            os.symlink(目标路径, 待创路径)
            logging.info(f"创建符号链接成功：\"{待创路径}\" ===>> \"{目标路径}\"")
    except Exception as e:
        logging.error(f"创建符号链接时出错：{str(e)}")

# 函数：移动文件夹内容并处理重名
def 移动文件夹内容(源路径, 目标路径, 版本名字=""):
    """移动文件夹内容并处理重名"""
    if not os.path.exists(源路径):
        return
        
    所有项目 = os.listdir(源路径)
    for 项目名 in 所有项目:
        项目路径 = os.path.join(源路径, 项目名)
        原始名称 = 项目名
        
        if os.path.isdir(项目路径):
            # 文件夹处理：先去除结尾的(数字)
            项目名 = re.sub(r'\s\(\d+\)$', '', 原始名称)
            # 如果是来自版本目录的项目，并且没有" [版本名]"作为后缀，则添加后缀
            if 版本名字 and not re.search(r'\s\[[^\[\]]+\]$', 项目名):
                项目名 = f"{项目名} [{版本名字}]"
        else:
            # 文件处理：分离文件名和扩展名
            文件名, 扩展名 = os.path.splitext(原始名称)
            # 先去除结尾的(数字)
            文件名 = re.sub(r'\s\(\d+\)$', '', 文件名)
            # 如果是来自版本目录的文件，并且没有" [版本名]"作为后缀，则添加后缀
            if 版本名字 and not re.search(r'\s\[[^\[\]]+\]$', 文件名):
                文件名 = f"{文件名} [{版本名字}]"
            项目名 = f"{文件名}{扩展名}"
        
        新项目路径 = os.path.join(目标路径, 项目名)
        # 检查项目路径是否已存在，如果存在，则添加 "(数字)" 后缀
        count = 1
        while os.path.exists(新项目路径):
            if os.path.isdir(项目路径):
                新项目路径 = os.path.join(目标路径, f"{项目名} ({count})")
            else:
                文件名, 扩展名 = os.path.splitext(项目名)
                新项目路径 = os.path.join(目标路径, f"{文件名} ({count}){扩展名}")
            count += 1
        
        logging.info(f"移动 \"{原始名称}\" 到 \"{新项目路径}\"...")
        try:
            shutil.move(项目路径, 新项目路径)
        except Exception as e:
            logging.error(f"移动文件失败：{str(e)}")
            
# 函数：判断路径是否为符号链接
def isLink(path):
    # 优先使用 Windows 判断方法
    if os.name == 'nt':
        if not os.path.isdir(path):
            return False
        FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return (attrs & FILE_ATTRIBUTE_REPARSE_POINT) != 0
    else:
        return os.path.islink(path)

# 函数：处理文件夹目录
def 处理文件夹目录(源目录, 文件夹类型, 目标文件夹路径, 版本名字=""):
    """处理文件夹目录"""
    源文件夹路径 = os.path.join(源目录, 文件夹类型)
    
    if os.path.exists(源文件夹路径): # 检查源文件夹是否存在
        if not isLink(源文件夹路径): # 如果源文件夹不是符号链接
        # if not os.path.islink(源文件夹路径): 
            logging.info(f"正在移动 \"{源文件夹路径}\" 中的内容到 \"{目标文件夹路径}\"...")
            移动文件夹内容(源文件夹路径, 目标文件夹路径, 版本名字)
    else:
        logging.info(f"路径 \"{文件夹类型}\" 不存在，正在创建...")
    
    创建软链接(源文件夹路径, 目标文件夹路径)

# 函数：添加待处理的目录到列表
def 添加待处理的目录到列表():
    """添加待处理的目录到列表"""
    global 待处理的目录
    
    版本目录 = os.path.join(MC_根目录, "versions")
    if os.path.exists(版本目录):
        for entry in os.listdir(版本目录):
            entry_path = os.path.join(版本目录, entry)
            if os.path.isdir(entry_path):
                版本名 = entry
                mod文件夹路径 = os.path.join(entry_path, "mods")
                if os.path.exists(mod文件夹路径):
                    # 如果属于含mod但也处理的存档目录，则不跳过
                    if 版本名 not in 含mod但也处理的存档目录:
                        logging.info(f"该版本 {版本名} 存在mod文件夹，跳过文件夹处理")
                        continue
                待处理的目录.append(entry_path)
    
    if MC_根目录 != 官方MC_根目录:
        待处理的目录.append(官方MC_根目录)
        版本目录 = os.path.join(官方MC_根目录, "versions")
        if os.path.exists(版本目录):
            for entry in os.listdir(版本目录):
                entry_path = os.path.join(版本目录, entry)
                if os.path.isdir(entry_path):
                    版本名 = entry
                    mod文件夹路径 = os.path.join(entry_path, "mods")
                    if os.path.exists(mod文件夹路径):
                        # 如果属于含mod但也处理的存档目录，则不跳过
                        if 版本名 not in 含mod但也处理的存档目录:
                            logging.info(f"该版本 {版本名} 存在mod文件夹，跳过文件夹处理")
                            continue
                    待处理的目录.append(entry_path)

def main():
    """主函数"""
    global 待处理的目录
    
    # 为每个要链接的文件夹类型创建目标目录（如果不存在）
    for 文件夹类型 in 要链接的文件夹:
        目标路径 = os.path.join(MC_根目录, 文件夹类型)
        if not os.path.exists(目标路径):
            os.makedirs(目标路径, exist_ok=True)
    
    添加待处理的目录到列表()
    
    for 目录 in 待处理的目录:
        logging.info(f"正在处理目录 \"{目录}\"...")
        
        # 获取版本名称（如果是版本目录）
        版本名字 = ""
        if 目录 != MC_根目录 and 目录 != 官方MC_根目录:
            版本名字 = os.path.basename(目录)
        
        # 处理每个文件夹类型
        for 文件夹类型 in 要链接的文件夹:
            目标路径 = os.path.join(MC_根目录, 文件夹类型)
            处理文件夹目录(目录, 文件夹类型, 目标路径, 版本名字)

if __name__ == "__main__":
    try:
        main()
        logging.info("脚本执行完成！")
    except KeyboardInterrupt:
        logging.info("脚本被用户中断")
    except Exception as e:
        logging.error(f"脚本执行时出现错误：{str(e)}")
        import traceback
        logging.error(traceback.format_exc())
