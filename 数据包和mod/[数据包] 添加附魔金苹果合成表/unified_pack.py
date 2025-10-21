# -*- coding: utf-8 -*-
"""
附魔金苹果数据包统一打包工具
从统一的源码生成不同版本的数据包
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from packaging import version

class UnifiedDatapackBuilder:
    def __init__(self, base_dir=None):
        """初始化统一打包器
        
        Args:
            base_dir: 基础目录，默认为脚本所在目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.src_dir = self.base_dir / "src"
        self.output_dir = self.base_dir / "build"
        self.versions_file = self.base_dir / "versions.json"
        self.pack_config_file = self.base_dir / "pack_config.json"
        
        self.load_versions()
        self.load_config()
    
    def load_versions(self):
        """加载版本配置"""
        if not self.versions_file.exists():
            raise FileNotFoundError(f"版本配置文件不存在: {self.versions_file}")
        
        with open(self.versions_file, 'r', encoding='utf-8') as f:
            self.versions_config = json.load(f)
    
    def load_config(self):
        """加载打包配置"""
        default_config = {
            "output_directory": "build",
            "zip_compression": "ZIP_DEFLATED",
            "include_timestamp": True,
            "exclude_patterns": [".git", "__pycache__", "*.pyc", ".DS_Store"],
            "clean_build_dir": True
        }
        
        if self.pack_config_file.exists():
            try:
                with open(self.pack_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.config = {**default_config, **config}
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                self.config = default_config
        else:
            self.config = default_config
    
    def compare_version(self, version_str1, version_str2):
        """比较两个版本号
        
        Args:
            version_str1: 第一个版本号字符串
            version_str2: 第二个版本号字符串
            
        Returns:
            int: -1 如果 version_str1 < version_str2
                  0 如果 version_str1 == version_str2
                  1 如果 version_str1 > version_str2
        """
        try:
            v1 = version.parse(version_str1)
            v2 = version.parse(version_str2)
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception as e:
            print(f"版本比较错误: {e}")
            return 0
    
    def should_use_new_format(self, target_version):
        """判断指定版本是否应该使用新格式 (min_format/max_format)
        
        Args:
            target_version: 目标版本号字符串
            
        Returns:
            bool: True 如果应该使用新格式，False 如果使用旧格式
        """
        # 版本检测配置：版本号大于此版本使用 min_format/max_format，小于等于此版本使用 supported_formats
        format_transition_version = "1.21.8"
        return self.compare_version(target_version, format_transition_version) > 0
    
    def get_result_key_for_version(self, target_version):
        """根据版本自动检测result_key
        
        Args:
            target_version: 目标版本号字符串
            
        Returns:
            str: "item" 如果版本 <= 1.20.4，"id" 如果版本 > 1.20.4
        """
        transition_version = "1.20.4"
        if self.compare_version(target_version, transition_version) <= 0:
            return "item"
        else:
            return "id"
    
    def get_recipe_folder_for_version(self, target_version):
        """根据版本自动检测recipe_folder
        
        Args:
            target_version: 目标版本号字符串
            
        Returns:
            str: "recipes" 如果版本 < 1.21.0，"recipe" 如果版本 >= 1.21.0
        """
        transition_version = "1.21.0"
        if self.compare_version(target_version, transition_version) < 0:
            return "recipes"
        else:
            return "recipe"
    
    def get_recipe_format_for_version(self, target_version):
        """根据版本自动检测recipe_format
        
        Args:
            target_version: 目标版本号字符串
            
        Returns:
            str: "legacy", "modern", 或 "simplified"
        """
        # 1.20.4及以下：legacy
        if self.compare_version(target_version, "1.20.4") <= 0:
            return "legacy"
        # 1.21.2及以上：simplified
        elif self.compare_version(target_version, "1.21.2") >= 0:
            return "simplified"
        # 1.20.5-1.21.1：modern
        else:
            return "modern"
    
    def get_advancement_format_for_version(self, target_version):
        """根据版本自动检测advancement格式
        
        Args:
            target_version: 目标版本号字符串
            
        Returns:
            str: "legacy" 如果版本 <= 1.20.4，"modern" 如果版本 > 1.20.4
        """
        if self.compare_version(target_version, "1.20.4") <= 0:
            return "legacy"
        else:
            return "modern"
    
    def convert_advancement_format(self, advancement_data, target_format):
        """转换advancement文件格式
        
        Args:
            advancement_data: advancement文件的JSON数据
            target_format: 目标格式 ("legacy" 或 "modern")
            
        Returns:
            dict: 转换后的advancement数据
        """
        # 深拷贝数据以避免修改原始数据
        import copy
        converted_data = copy.deepcopy(advancement_data)
        
        # 递归处理所有criteria中的items字段
        def convert_items_field(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "items":
                        # 处理items字段，可能有两种结构：
                        # 1. "items": ["minecraft:gold_block"] (在对象内部)
                        # 2. "items": [{"items": ["minecraft:gold_block"]}] (外层数组)
                        if isinstance(value, list):
                            # 检查是否是外层数组结构
                            if len(value) > 0 and isinstance(value[0], dict) and "items" in value[0]:
                                # 这是外层数组结构，需要处理内部的items
                                for item_obj in value:
                                    if isinstance(item_obj, dict) and "items" in item_obj:
                                        inner_items = item_obj["items"]
                                        if target_format == "legacy":
                                            # legacy格式：保持数组
                                            if isinstance(inner_items, str):
                                                item_obj["items"] = [inner_items]
                                        elif target_format == "modern":
                                            # modern格式：转换为字符串
                                            if isinstance(inner_items, list) and len(inner_items) == 1:
                                                item_obj["items"] = inner_items[0]
                            else:
                                # 这是直接的items数组，处理转换
                                if target_format == "legacy":
                                    # legacy格式：保持数组
                                    if isinstance(value, str):
                                        obj[key] = [value]
                                elif target_format == "modern":
                                    # modern格式：转换为字符串
                                    if len(value) == 1:
                                        obj[key] = value[0]
                        elif isinstance(value, str):
                            # 字符串格式
                            if target_format == "legacy":
                                obj[key] = [value]
                    else:
                        convert_items_field(value)
            elif isinstance(obj, list):
                for item in obj:
                    convert_items_field(item)
        
        convert_items_field(converted_data)
        return converted_data
    
    def find_version_config_for_target(self, target_version):
        """根据目标版本号找到对应的版本配置
        
        Args:
            target_version: 目标版本号字符串
            
        Returns:
            tuple: (version_key, version_config) 或 (None, None) 如果未找到
        """
        versions = self.versions_config['versions']
        
        for version_key, version_config in versions.items():
            version_range = version_config.get('version_range')
            if version_range and len(version_range) == 2:
                min_version, max_version = version_range
                if (self.compare_version(target_version, min_version) >= 0 and 
                    self.compare_version(target_version, max_version) <= 0):
                    return version_key, version_config
        
        return None, None
    
    def convert_datapack_range(self, datapack_range, use_new_format):
        """
        将 datapack_range 转换为对应的格式配置
        
        Args:
            datapack_range: [min_format, max_format] 数组，支持小数
            use_new_format: 是否使用新格式
            
        Returns:
            dict: 包含转换后的格式配置
        """
        if not datapack_range or len(datapack_range) != 2:
            return {}
        
        min_format, max_format = datapack_range
        
        if use_new_format:
            # 新格式：使用 min_format/max_format，确保有小数部分
            if isinstance(min_format, int):
                min_format = float(min_format)
            if isinstance(max_format, int):
                max_format = float(max_format)
            
            # 转换为 [整数部分, 小数部分] 格式
            min_parts = [int(min_format), round((min_format % 1) * 10)]
            max_parts = [int(max_format), round((max_format % 1) * 10)]
            
            return {
                "min_format": min_parts,
                "max_format": max_parts
            }
        else:
            # 旧格式：使用 supported_formats，只取整数部分
            min_int = int(min_format)
            max_int = int(max_format)
            
            return {
                "supported_formats": [min_int, max_int],
                "pack_format": max_int  # 自动使用max_int作为pack_format值
            }
    
    def generate_pack_mcmeta(self, version_key, version_config, target_version=None):
        """生成 pack.mcmeta 文件内容"""
        # 直接构建JSON对象，避免字符串模板问题
        pack_data = {
            "pack": {
                "description": "添加附魔金苹果合成表"
            }
        }
        
        # 自动检测格式类型
        use_new_format = False
        if target_version:
            use_new_format = self.should_use_new_format(target_version)
        
        # 处理新的统一 datapack_range 格式
        if 'datapack_range' in version_config:
            format_config = self.convert_datapack_range(version_config['datapack_range'], use_new_format)
            pack_data["pack"].update(format_config)
        
        return pack_data
    
    def generate_recipe_file(self, target_version):
        """生成合成表文件内容"""
        # 从src目录读取基础模板
        src_recipe_file = self.src_dir / "data" / "minecraft" / "recipe" / "enchanted_golden_apple.json"
        
        if not src_recipe_file.exists():
            raise FileNotFoundError(f"源合成表文件不存在: {src_recipe_file}")
        
        # 读取基础模板
        with open(src_recipe_file, 'r', encoding='utf-8') as f:
            recipe = json.load(f)
        
        # 根据版本调整格式
        recipe_format_name = self.get_recipe_format_for_version(target_version)
        result_key = self.get_result_key_for_version(target_version)
        
        # 根据recipe_format_name确定key_format
        if recipe_format_name == "simplified":
            key_format = "string"
        else:
            key_format = "object"
        
        # 调整key结构以适应不同版本
        if key_format == 'string':
            # 简化格式：直接使用字符串
            if "key" in recipe:
                for key, value in recipe["key"].items():
                    if isinstance(value, dict) and "item" in value:
                        # 从对象格式转换为字符串格式
                        recipe["key"][key] = value["item"]
        else:
            # 对象格式：使用item包装
            if "key" in recipe:
                for key, value in recipe["key"].items():
                    if isinstance(value, str):
                        # 从字符串格式转换为对象格式
                        recipe["key"][key] = {"item": value}
        
        # 调整result字段的key名称
        if "result" in recipe:
            current_result = recipe["result"].copy()
            # 移除旧的key
            if "item" in current_result:
                del recipe["result"]["item"]
            if "id" in current_result:
                del recipe["result"]["id"]
            
            # 设置正确的key
            recipe["result"][result_key] = "minecraft:enchanted_golden_apple"
            if "count" in current_result:
                recipe["result"]["count"] = current_result["count"]
            else:
                recipe["result"]["count"] = 1
        
        return recipe
    
    def copy_advancement_files(self, build_version_dir, target_version):
        """复制并转换进度文件格式
        
        Args:
            build_version_dir: 构建目录
            target_version: 目标版本号
        """
        src_advancement_dir = self.src_dir / "data" / "minecraft" / "advancements"
        if not src_advancement_dir.exists():
            return
        
        dest_advancement_dir = build_version_dir / "data" / "minecraft" / "advancements"
        dest_advancement_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取目标格式
        target_format = self.get_advancement_format_for_version(target_version)
        
        # 递归复制并转换advancement文件
        for root, dirs, files in os.walk(src_advancement_dir):
            root_path = Path(root)
            relative_path = root_path.relative_to(src_advancement_dir)
            dest_root = dest_advancement_dir / relative_path
            
            # 创建目录
            dest_root.mkdir(parents=True, exist_ok=True)
            
            # 处理文件
            for file in files:
                src_file = root_path / file
                dest_file = dest_root / file
                
                if file.endswith('.json'):
                    # 处理JSON advancement文件
                    try:
                        with open(src_file, 'r', encoding='utf-8') as f:
                            advancement_data = json.load(f)
                        
                        # 转换格式
                        converted_data = self.convert_advancement_format(advancement_data, target_format)
                        
                        # 写入转换后的文件
                        with open(dest_file, 'w', encoding='utf-8') as f:
                            json.dump(converted_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"  警告: advancement文件转换失败 {src_file}: {e}")
                        # 如果转换失败，直接复制原文件
                        shutil.copy2(src_file, dest_file)
                else:
                    # 非JSON文件直接复制
                    shutil.copy2(src_file, dest_file)
    
    def build_version(self, version_key, version_config):
        """构建单个版本的数据包"""
        print(f"\\n正在构建版本: {version_key}")
        
        # 从version_config中获取版本范围，使用最大版本作为target_version
        version_range = version_config.get('version_range')
        if version_range and len(version_range) == 2:
            target_version = version_range[1]  # 使用版本范围的最大版本
        else:
            # 如果没有版本范围，从version_key中提取（如 "1.21.2-1.21.8" -> "1.21.8"）
            if '-' in version_key:
                target_version = version_key.split('-')[1]
            else:
                target_version = version_key
        
        # 创建构建目录
        build_version_dir = self.output_dir / f"[附魔金苹果][{version_key}]"
        if build_version_dir.exists():
            shutil.rmtree(build_version_dir)
        build_version_dir.mkdir(parents=True)
        
        try:
            # 1. 生成 pack.mcmeta（传入target_version以自动选择格式）
            pack_mcmeta = self.generate_pack_mcmeta(version_key, version_config, target_version)
            with open(build_version_dir / "pack.mcmeta", 'w', encoding='utf-8') as f:
                json.dump(pack_mcmeta, f, ensure_ascii=False, indent=2)
            
            # 2. 创建数据目录结构（自动检测recipe_folder）
            recipe_folder = self.get_recipe_folder_for_version(target_version)
            recipe_dir = build_version_dir / "data" / "minecraft" / recipe_folder
            recipe_dir.mkdir(parents=True)
            
            # 3. 生成合成表文件（自动检测配置）
            recipe_content = self.generate_recipe_file(target_version=target_version)
            
            with open(recipe_dir / "enchanted_golden_apple.json", 'w', encoding='utf-8') as f:
                json.dump(recipe_content, f, ensure_ascii=False, indent=2)
            
            # 4. 复制进度文件
            self.copy_advancement_files(build_version_dir, target_version)
            
            print(f"  ✓ 构建完成: {build_version_dir.name}")
            return build_version_dir
            
        except Exception as e:
            print(f"  ✗ 构建失败: {e}")
            return None
    
    def create_zip(self, source_folder, output_path):
        """创建zip文件"""
        compression = getattr(zipfile, self.config["zip_compression"], zipfile.ZIP_DEFLATED)
        
        with zipfile.ZipFile(output_path, 'w', compression=compression) as zipf:
            for root, dirs, files in os.walk(source_folder):
                root_path = Path(root)
                
                for file in files:
                    file_path = root_path / file
                    arcname = file_path.relative_to(source_folder)
                    zipf.write(file_path, arcname)
        
        return True
    
    def build_for_target_version(self, target_version, create_zip=True):
        """根据目标版本号构建数据包
        
        Args:
            target_version: 目标 Minecraft 版本号（如 "1.21.9"）
            create_zip: 是否创建 zip 文件
            
        Returns:
            bool: 构建是否成功
        """
        print(f"\n正在为目标版本 {target_version} 查找合适的配置...")
        
        # 查找匹配的版本配置
        version_key, version_config = self.find_version_config_for_target(target_version)
        
        if not version_config:
            print(f"错误: 未找到支持版本 {target_version} 的配置")
            print("可用版本范围:")
            for key, config in self.versions_config['versions'].items():
                version_range = config.get('version_range', [])
                if len(version_range) == 2:
                    print(f"  - {key}: {version_range[0]} 到 {version_range[1]}")
            return False
        
        print(f"找到匹配配置: {version_key}")
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建构建目录（使用目标版本号命名）
        build_version_dir = self.output_dir / f"[附魔金苹果][{target_version}]"
        if build_version_dir.exists():
            shutil.rmtree(build_version_dir)
        build_version_dir.mkdir(parents=True)
        
        try:
            # 1. 生成 pack.mcmeta（传入目标版本号以自动选择格式）
            pack_mcmeta = self.generate_pack_mcmeta(version_key, version_config, target_version)
            with open(build_version_dir / "pack.mcmeta", 'w', encoding='utf-8') as f:
                json.dump(pack_mcmeta, f, ensure_ascii=False, indent=2)
            
            # 2. 创建数据目录结构
            recipe_folder = self.get_recipe_folder_for_version(target_version)
            recipe_dir = build_version_dir / "data" / "minecraft" / recipe_folder
            recipe_dir.mkdir(parents=True)
            
            # 3. 生成合成表文件
            recipe_content = self.generate_recipe_file(target_version=target_version)
            
            with open(recipe_dir / "enchanted_golden_apple.json", 'w', encoding='utf-8') as f:
                json.dump(recipe_content, f, ensure_ascii=False, indent=2)
            
            # 4. 复制进度文件
            self.copy_advancement_files(build_version_dir, target_version)
            
            # 显示使用的格式信息
            print(f"  ✓ 构建完成: {build_version_dir.name}")
            
            # 创建zip文件
            if create_zip:
                print("\n开始打包zip文件...")
                zip_output_dir = self.output_dir / "zips"
                zip_output_dir.mkdir(exist_ok=True)
                
                try:
                    zip_filename = f"附魔金苹果数据包_v{target_version}"
                    if self.config["include_timestamp"]:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        zip_filename += f"_{timestamp}"
                    zip_filename += ".zip"
                    
                    zip_path = zip_output_dir / zip_filename
                    
                    if self.create_zip(build_version_dir, zip_path):
                        file_size = zip_path.stat().st_size
                        print(f"✓ {zip_filename} ({file_size:,} 字节)")
                        print(f"输出路径: {zip_path.absolute()}")
                        return True
                    else:
                        print(f"✗ 打包失败")
                        return False
                        
                except Exception as e:
                    print(f"✗ 打包错误: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"  ✗ 构建失败: {e}")
            return False
    
    def generate_output_filename(self, version_key):
        """生成输出文件名"""
        base_name = f"附魔金苹果数据包_v{version_key}"
        
        if self.config["include_timestamp"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name += f"_{timestamp}"
        
        return f"{base_name}.zip"
    
    def build_all_versions(self, create_zips=True):
        """构建所有版本"""
        # 清理构建目录
        if self.config.get("clean_build_dir", True) and self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        self.output_dir.mkdir(exist_ok=True)
        
        versions = self.versions_config['versions']
        print(f"开始构建 {len(versions)} 个版本的数据包...")
        
        success_count = 0
        built_folders = []
        
        for version_key, version_config in versions.items():
            built_folder = self.build_version(version_key, version_config)
            if built_folder:
                built_folders.append((version_key, built_folder))
                success_count += 1
        
        print(f"\\n构建完成! 成功: {success_count}/{len(versions)}")
        
        # 创建zip文件
        if create_zips and built_folders:
            print("\\n开始打包zip文件...")
            zip_output_dir = self.output_dir / "zips"
            zip_output_dir.mkdir(exist_ok=True)
            
            zip_success_count = 0
            for version_key, built_folder in built_folders:
                try:
                    zip_filename = self.generate_output_filename(version_key)
                    zip_path = zip_output_dir / zip_filename
                    
                    if self.create_zip(built_folder, zip_path):
                        file_size = zip_path.stat().st_size
                        print(f"  ✓ {zip_filename} ({file_size:,} 字节)")
                        zip_success_count += 1
                    else:
                        print(f"  ✗ 打包失败: {version_key}")
                        
                except Exception as e:
                    print(f"  ✗ 打包错误: {version_key} - {e}")
            
            print(f"\\n打包完成! 成功: {zip_success_count}/{len(built_folders)}")
            print(f"输出目录: {zip_output_dir.absolute()}")
        
        print(f"\\n构建目录: {self.output_dir.absolute()}")
        return success_count == len(versions)
    
    def build_single_version(self, version_key, create_zip=True):
        """构建单个版本"""
        versions = self.versions_config['versions']
        
        if version_key not in versions:
            print(f"错误: 版本 '{version_key}' 不存在")
            print("可用版本:")
            for key in versions.keys():
                print(f"  - {key}")
            return False
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        version_config = versions[version_key]
        built_folder = self.build_version(version_key, version_config)
        
        if not built_folder:
            return False
        
        # 创建zip文件
        if create_zip:
            print("\\n开始打包zip文件...")
            zip_output_dir = self.output_dir / "zips"
            zip_output_dir.mkdir(exist_ok=True)
            
            try:
                zip_filename = self.generate_output_filename(version_key)
                zip_path = zip_output_dir / zip_filename
                
                if self.create_zip(built_folder, zip_path):
                    file_size = zip_path.stat().st_size
                    print(f"✓ {zip_filename} ({file_size:,} 字节)")
                    print(f"输出路径: {zip_path.absolute()}")
                    return True
                else:
                    print(f"✗ 打包失败")
                    return False
                    
            except Exception as e:
                print(f"✗ 打包错误: {e}")
                return False
        
        return True
    
    def list_versions(self):
        """列出所有可用版本"""
        versions = self.versions_config['versions']
        print("可用的版本:")
        for version_key, version_config in versions.items():
            # 自动从version_range生成描述
            version_range = version_config.get('version_range', [])
            if len(version_range) >= 2:
                description = f"支持 Minecraft {version_range[0]} 到 {version_range[1]}"
            else:
                description = '无描述'
            print(f"  - {version_key} ({description})")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='附魔金苹果数据包统一打包工具')
    parser.add_argument('--version', '-v', help='指定要构建的版本范围（不指定则构建所有版本）')
    parser.add_argument('--target-version', '-t', help='指定目标 Minecraft 版本号（如 1.21.9），自动选择格式')
    parser.add_argument('--no-zip', action='store_true', help='不创建zip文件，只构建文件夹')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用版本')
    parser.add_argument('--clean', '-c', action='store_true', help='清理构建目录后退出')
    
    args = parser.parse_args()
    
    try:
        builder = UnifiedDatapackBuilder()
        
        if args.clean:
            if builder.output_dir.exists():
                shutil.rmtree(builder.output_dir)
                print(f"已清理构建目录: {builder.output_dir}")
            else:
                print("构建目录不存在，无需清理")
            return
        
        if args.list:
            builder.list_versions()
            return
        
        create_zips = not args.no_zip
        
        if args.target_version:
            # 使用目标版本号构建（自动选择格式）
            success = builder.build_for_target_version(args.target_version, create_zips)
        elif args.version:
            # 使用版本范围构建
            success = builder.build_single_version(args.version, create_zips)
        else:
            # 构建所有版本
            success = builder.build_all_versions(create_zips)
        
        if success:
            print("\\n🎉 构建完成!")
        else:
            print("\\n❌ 构建过程中出现错误")
            
    except Exception as e:
        print(f"\\n❌ 错误: {e}")
        return 1

if __name__ == "__main__":
    main()