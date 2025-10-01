#!/usr/bin/env python3
"""
跨平台构建脚本 - 水印应用
支持Windows和MacOS打包
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """安装必要的依赖"""
    print("正在安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    print("依赖安装完成")

def create_icon():
    """创建应用图标（如果不存在）"""
    icon_path = Path("watermark_icon.ico")
    if not icon_path.exists():
        print("注意：未找到图标文件 watermark_icon.ico")
        print("应用将使用默认图标")
    return icon_path.exists()

def build_windows():
    """构建Windows版本"""
    print("正在构建Windows版本...")
    
    # 创建Windows构建目录
    build_dir = Path("dist/windows")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用PyInstaller构建
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "build.spec",
        "--distpath", str(build_dir),
        "--workpath", "build/windows",
        "--noconfirm"
    ]
    
    subprocess.run(cmd, check=True)
    
    # 复制必要的文件
    shutil.copy2("README.md", build_dir / "README.md")
    shutil.copy2("requirements.txt", build_dir / "requirements.txt")
    
    print(f"Windows版本构建完成: {build_dir / 'WatermarkApp.exe'}")

def build_macos():
    """构建MacOS版本"""
    print("正在构建MacOS版本...")
    
    # 创建MacOS构建目录
    build_dir = Path("dist/macos")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用PyInstaller构建
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "build.spec",
        "--distpath", str(build_dir),
        "--workpath", "build/macos",
        "--noconfirm"
    ]
    
    subprocess.run(cmd, check=True)
    
    # 复制必要的文件
    shutil.copy2("README.md", build_dir / "README.md")
    shutil.copy2("requirements.txt", build_dir / "requirements.txt")
    
    print(f"MacOS版本构建完成: {build_dir / 'WatermarkApp'}")

def create_release_package():
    """创建发布包"""
    print("正在创建发布包...")
    
    # 创建发布目录
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    current_platform = platform.system().lower()
    
    if current_platform == "windows":
        # Windows版本
        source_dir = Path("dist/windows")
        if source_dir.exists():
            # 创建ZIP包
            shutil.make_archive(
                str(release_dir / "WatermarkApp-Windows"),
                'zip',
                source_dir
            )
            print(f"Windows发布包创建完成: {release_dir / 'WatermarkApp-Windows.zip'}")
    
    elif current_platform == "darwin":
        # MacOS版本
        source_dir = Path("dist/macos")
        if source_dir.exists():
            # 创建DMG包（简化版，实际需要更复杂的DMG创建）
            shutil.make_archive(
                str(release_dir / "WatermarkApp-MacOS"),
                'zip',
                source_dir
            )
            print(f"MacOS发布包创建完成: {release_dir / 'WatermarkApp-MacOS.zip'}")
    
    else:
        print(f"不支持的平台: {current_platform}")

def main():
    """主函数"""
    print("=" * 50)
    print("水印应用构建脚本")
    print("=" * 50)
    
    # 检查当前平台
    current_platform = platform.system()
    print(f"当前平台: {current_platform}")
    
    try:
        # 安装依赖
        install_dependencies()
        
        # 创建图标
        create_icon()
        
        # 根据平台构建
        if current_platform == "Windows":
            build_windows()
        elif current_platform == "Darwin":
            build_macos()
        else:
            # 在其他平台上尝试构建两个版本
            print("检测到非Windows/MacOS平台，尝试构建两个版本...")
            build_windows()
            build_macos()
        
        # 创建发布包
        create_release_package()
        
        print("\n构建完成！")
        print("可执行文件位于 dist/ 目录")
        print("发布包位于 release/ 目录")
        
    except subprocess.CalledProcessError as e:
        print(f"构建过程中出错: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
