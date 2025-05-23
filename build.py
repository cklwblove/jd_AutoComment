'''
FilePath: /jd_AutoComment/build.py
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本，生成可执行文件
"""

import os
import sys
import platform
import subprocess
import shutil
import argparse

def check_pyinstaller():
    """检查是否安装了PyInstaller"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    if not check_pyinstaller():
        print("正在安装PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

def get_architecture():
    """获取当前系统架构"""
    arch = platform.machine()
    system = platform.system().lower()
    
    if system == "darwin":
        # 检查是否为 Apple Silicon
        if arch == "arm64":
            return "arm64"
        else:
            return "x86_64"
    elif system == "windows":
        return "amd64" if "64" in arch else "x86"
    else:  # Linux
        if "arm" in arch or "aarch" in arch:
            return "arm64"
        else:
            return "amd64"

def create_icon():
    """为macOS创建图标文件"""
    system = platform.system().lower()
    if system != "darwin":
        return None
        
    print("正在为macOS创建图标文件...")
    
    # 创建临时图标目录
    icon_dir = "icon.iconset"
    if os.path.exists(icon_dir):
        shutil.rmtree(icon_dir)
    os.makedirs(icon_dir)
    
    # 使用Python生成一个简单的图标
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            img = Image.new('RGBA', (size, size), color=(255, 255, 255, 0))
            d = ImageDraw.Draw(img)
            
            # 绘制圆形背景
            d.ellipse([(0, 0), (size, size)], fill=(220, 20, 60))
            
            # 添加文字
            try:
                font_size = size // 2
                font = ImageFont.truetype("Arial", font_size)
            except:
                font = ImageFont.load_default()
                
            text = "JD"
            text_width, text_height = d.textbbox((0, 0), text, font=font)[2:4]
            position = ((size - text_width) // 2, (size - text_height) // 2)
            d.text(position, text, font=font, fill=(255, 255, 255))
            
            # 保存不同尺寸的图标
            img.save(f"{icon_dir}/icon_{size}x{size}.png")
            img.save(f"{icon_dir}/icon_{size}x{size}@2x.png")
        
        # 使用macOS的iconutil工具创建icns文件
        subprocess.run(["iconutil", "-c", "icns", icon_dir])
        print("图标创建成功: icon.icns")
        return "icon.icns"
    except Exception as e:
        print(f"创建图标时出错: {e}")
        print("将使用默认图标继续")
        return None

def fix_app_permissions(app_path):
    """修复macOS应用权限问题"""
    if not os.path.exists(app_path):
        print(f"应用程序不存在: {app_path}")
        return
    
    print(f"修复应用程序权限: {app_path}")
    try:
        # 赋予执行权限
        subprocess.run(["chmod", "-R", "+x", app_path])
        
        # 移除扩展属性（解决隔离标记问题）
        subprocess.run(["xattr", "-cr", app_path])
        
        # 确保应用中的可执行文件有执行权限
        executable_path = f"{app_path}/Contents/MacOS/京东自动评价"
        if os.path.exists(executable_path):
            subprocess.run(["chmod", "+x", executable_path])
            
        # 确保资源文件夹存在且有正确的权限
        resources_path = f"{app_path}/Contents/Resources"
        if os.path.exists(resources_path):
            subprocess.run(["chmod", "-R", "755", resources_path])
            
        # 确保Python库文件有正确的权限
        lib_path = f"{app_path}/Contents/Frameworks"
        if os.path.exists(lib_path):
            subprocess.run(["chmod", "-R", "755", lib_path])
        
        print("权限修复完成")
    except Exception as e:
        print(f"修复权限时出错: {e}")

def create_standalone_launcher():
    """创建独立的启动器脚本"""
    launcher_path = "dist/启动京东自动评价.command"
    print(f"创建独立启动器: {launcher_path}")
    
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write("""#!/bin/bash

# 京东自动评价 - 独立启动脚本
# 此脚本可以在任何位置运行，会自动查找应用程序或提供安装选项

# 设置颜色
GREEN="\\033[0;32m"
RED="\\033[0;31m"
YELLOW="\\033[0;33m"
BLUE="\\033[0;34m"
NC="\\033[0m" # 恢复默认颜色

# 显示欢迎信息
echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}    京东自动评价程序启动工具 v2.0   ${NC}"
echo -e "${BLUE}====================================${NC}"

# 定义可能的应用路径
APP_LOCATIONS=(
    "/Applications/京东自动评价.app"
    "$HOME/Applications/京东自动评价.app"
    "$(dirname "$0")/京东自动评价.app"
    "$(dirname "$0")/../京东自动评价.app"
)

# 查找应用
FOUND_APP=""
for APP_PATH in "${APP_LOCATIONS[@]}"; do
    if [ -d "$APP_PATH" ]; then
        FOUND_APP="$APP_PATH"
        break
    fi
done

# 如果没有找到应用，询问用户是否要安装
if [ -z "$FOUND_APP" ]; then
    echo -e "${YELLOW}未找到京东自动评价应用程序${NC}"
    echo "请选择安装方式:"
    echo "1) 从DMG安装(推荐)"
    echo "2) 尝试解压ZIP安装"
    echo "3) 退出"
    read -p "请输入选项 [1-3]: " choice
    
    case $choice in
        1)
            # 寻找DMG文件
            DMG_FILE=""
            for DMG in "$(dirname "$0")/京东自动评价安装包*.dmg" "$(dirname "$0")/../京东自动评价安装包*.dmg"; do
                if [ -f "$DMG" ]; then
                    DMG_FILE="$DMG"
                    break
                fi
            done
            
            if [ -z "$DMG_FILE" ]; then
                echo -e "${RED}未找到DMG安装包${NC}"
                exit 1
            fi
            
            echo -e "${GREEN}找到DMG文件: $DMG_FILE${NC}"
            echo "正在挂载DMG..."
            VOLUME=$(hdiutil attach "$DMG_FILE" | grep Volumes | cut -f 3)
            echo "DMG已挂载到: $VOLUME"
            
            echo "正在复制应用到Applications文件夹..."
            sudo cp -R "$VOLUME/京东自动评价.app" /Applications/
            
            echo "正在卸载DMG..."
            hdiutil detach "$VOLUME"
            
            FOUND_APP="/Applications/京东自动评价.app"
            echo -e "${GREEN}应用已安装到: $FOUND_APP${NC}"
            ;;
        2)
            # 寻找ZIP文件
            ZIP_FILE=""
            for ZIP in "$(dirname "$0")/京东自动评价*.zip" "$(dirname "$0")/../京东自动评价*.zip"; do
                if [ -f "$ZIP" ]; then
                    ZIP_FILE="$ZIP"
                    break
                fi
            done
            
            if [ -z "$ZIP_FILE" ]; then
                echo -e "${RED}未找到ZIP安装包${NC}"
                exit 1
            fi
            
            echo -e "${GREEN}找到ZIP文件: $ZIP_FILE${NC}"
            echo "正在解压到Applications文件夹..."
            
            # 创建临时目录
            TMP_DIR=$(mktemp -d)
            echo "正在解压到临时目录: $TMP_DIR"
            unzip -q "$ZIP_FILE" -d "$TMP_DIR"
            
            # 查找解压后的应用
            APP_IN_ZIP=$(find "$TMP_DIR" -name "京东自动评价.app" -type d)
            if [ -z "$APP_IN_ZIP" ]; then
                echo -e "${RED}ZIP中未找到应用${NC}"
                rm -rf "$TMP_DIR"
                exit 1
            fi
            
            echo "正在复制应用到Applications文件夹..."
            sudo cp -R "$APP_IN_ZIP" /Applications/
            
            # 清理临时目录
            rm -rf "$TMP_DIR"
            
            FOUND_APP="/Applications/京东自动评价.app"
            echo -e "${GREEN}应用已安装到: $FOUND_APP${NC}"
            ;;
        3)
            echo "退出安装"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项${NC}"
            exit 1
            ;;
    esac
fi

# 移除应用程序的隔离属性
echo "正在移除应用程序的隔离属性..."
sudo xattr -rd com.apple.quarantine "$FOUND_APP"

# 确保可执行文件有执行权限
EXECUTABLE="$FOUND_APP/Contents/MacOS/京东自动评价"
if [ -f "$EXECUTABLE" ]; then
    echo "设置可执行权限..."
    sudo chmod +x "$EXECUTABLE"
else
    echo -e "${RED}找不到应用程序可执行文件: $EXECUTABLE${NC}"
    exit 1
fi

# 检查app的所有权是否正确
USER=$(whoami)
if [ -d "$FOUND_APP" ]; then
    OWNER=$(ls -ld "$FOUND_APP" | awk '{print $3}')
    if [ "$OWNER" != "$USER" ]; then
        echo "修复应用程序所有权..."
        sudo chown -R "$USER" "$FOUND_APP"
    fi
fi

# 启动应用
echo -e "${GREEN}正在启动应用程序...${NC}"
open "$FOUND_APP"

echo -e "${GREEN}启动完成！${NC}"
echo "如果应用程序没有自动打开，请尝试以下解决方法:"
echo "1. 打开系统偏好设置 > 安全性与隐私 > 通用，点击'仍要打开'"
echo "2. 在Finder中找到应用，按住Control键并点击，选择'打开'"
echo -e "${BLUE}====================================${NC}"

# 等待几秒再退出
sleep 3
""")
    
    # 添加执行权限
    subprocess.run(["chmod", "+x", launcher_path])
    print(f"独立启动器创建完成: {launcher_path}")

def build_executable(args):
    """打包为可执行文件"""
    print("开始打包...")
    
    # 确定目标文件名和打包模式
    system = platform.system().lower()
    arch = get_architecture()
    print(f"检测到系统: {system}, 架构: {arch}")
    
    if system == "windows":
        ext = ".exe"
        icon_param = []
    elif system == "darwin":  # macOS
        ext = ".app"
        icon_file = create_icon()
        icon_param = ["--icon", icon_file] if icon_file else []
    else:  # Linux
        ext = ""
        icon_param = []
    
    output_name = f"京东自动评价{ext}"
    
    # 创建dist目录
    if not os.path.exists("dist"):
        os.makedirs("dist")
    else:
        # 清理已存在的应用
        if os.path.exists(f"dist/{output_name}"):
            print(f"删除之前的构建: dist/{output_name}")
            if system == "windows":
                os.remove(f"dist/{output_name}")
            else:
                shutil.rmtree(f"dist/{output_name}")
    
    # 确定要包含的文件
    additional_files = [
        f"config.yml{os.pathsep}.",
        f"jdspider.py{os.pathsep}.",
        f"auto_comment_plus_mod.py{os.pathsep}.",
    ]
    
    # 如果存在config.user.yml，也包含它
    if os.path.exists("config.user.yml"):
        additional_files.append(f"config.user.yml{os.pathsep}.")
    
    # 构建命令行参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "京东自动评价",
        "--windowed",  # GUI模式
        "--noconfirm",  # 不询问确认
        "--clean",  # 清理临时文件
    ]
    
    # 添加图标
    cmd.extend(icon_param)
    
    # 特殊处理macOS
    if system == "darwin":
        cmd.extend([
            "--osx-bundle-identifier", "com.github.jdautocomment",  # 添加Bundle ID
            "--target-architecture", arch,  # 指定目标架构
        ])
        
        # 在Apple Silicon上，确保使用正确的架构
        if arch == "arm64":
            os.environ["ARCHFLAGS"] = "-arch arm64"
            # 确保使用arm64版本的Python
            print("当前在Apple Silicon (M系列) 芯片上构建，使用arm64架构")
    
    # 打包模式
    if args.onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # 添加数据文件
    for data_file in additional_files:
        cmd.extend(["--add-data", data_file])
    
    # 主程序
    if args.launcher:
        cmd.append("auto_comment_plus_launcher.py")
    else:
        cmd.append("jd_gui.py")
    
    # 执行打包命令
    print("执行打包命令:", " ".join(cmd))
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("打包失败！请检查错误信息")
        return None
    
    print(f"打包完成！可执行文件位于 dist/{output_name}")
    
    # 修复macOS应用权限和签名
    if system == "darwin":
        fix_app_permissions(f"dist/{output_name}")
        
        # 额外进行ad-hoc签名，这对防止"意外退出"很重要
        try:
            print(f"正在对应用进行ad-hoc签名...")
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", f"dist/{output_name}"])
            print("签名完成")
        except Exception as e:
            print(f"签名应用时出错: {e}")
            print("应用可能仍然可以使用，但可能需要额外步骤来绕过macOS安全限制")
    
    return output_name

def copy_additional_files(output_name):
    """复制额外文件到dist目录"""
    if output_name is None:
        print("跳过复制额外文件，因为打包失败")
        return
        
    print("复制额外文件...")
    
    # 确定正确的目标目录
    system = platform.system().lower()
    if system == "darwin" and output_name.endswith(".app") and not output_name.endswith(".app/Contents/MacOS/"):
        # macOS应用程序包结构
        if os.path.exists(f"dist/{output_name}"):
            target_dir = f"dist/{output_name}/Contents/MacOS/"
        else:
            target_dir = "dist/"
    else:
        target_dir = "dist/"
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 创建README文件
    with open(f"{target_dir}/使用说明.txt", "w", encoding="utf-8") as f:
        f.write("""京东自动评价工具使用说明

1. 运行程序后，需要在界面中输入京东Cookie
2. Cookie获取方法：
   - 打开 https://club.jd.com/myJdcomments/myJdcomment.action
   - 登录账号
   - 打开浏览器开发者工具(F12)，找到Network标签
   - 刷新页面，找到myJdcomment.action请求
   - 在请求头中找到Cookie字段，复制全部内容
3. 将复制的Cookie粘贴到程序的Cookie输入框中
4. 点击"保存Cookie"按钮
5. 选择日志级别（一般使用INFO，如需查看详细日志选择DEBUG）
6. 点击"开始评价"按钮
7. 等待评价完成

常见问题解决：
1. 如果提示"Cookie已失效"，请重新获取Cookie
2. 使用DEBUG日志级别可以查看更多详细信息
3. macOS用户第一次运行可能需要在"系统偏好设置">"安全性与隐私"中允许应用运行

如遇到问题，请查看github项目地址获取最新版本和支持：
https://github.com/cklwblove/jd_AutoComment
""")
    
    # 如果在macOS上，创建一个说明文件说明如何允许应用运行
    if system == "darwin":
        # macOS安装说明
        with open("dist/macOS安装说明.txt", "w", encoding="utf-8") as f:
            f.write("""# macOS安装指南

由于应用没有Apple开发者签名，macOS会阻止运行该应用。下面提供几种解决办法：

## 方法一：使用启动脚本（推荐方法）

1. 找到`启动京东自动评价.command`脚本
2. 右键点击脚本，选择"打开"
3. 如果出现警告，再次点击"打开"
4. 脚本会自动查找应用，移除隔离属性并启动

## 方法二：通过"隐私与安全性"设置允许运行

1. 双击DMG文件并将应用拖到"应用程序"文件夹
2. 尝试运行应用（会被系统阻止）
3. 打开"系统设置"或"系统偏好设置"
4. 点击"隐私与安全性"或"安全性与隐私"
5. 在"安全性"标签页找到"仍要打开"按钮（该按钮会在你尝试打开应用后约30秒内出现）
6. 点击"打开"确认运行应用

## 方法三：使用Control+点按打开

1. 双击DMG文件并将应用拖到"应用程序"文件夹
2. 在Finder中找到应用程序
3. 按住Control键(⌃)并点击应用图标
4. 在弹出菜单中选择"打开"
5. 在弹出对话框中点击"打开"（而不是"取消"）

## 方法四：使用终端命令移除隔离属性

1. 双击DMG文件并将应用拖到"应用程序"文件夹
2. 打开终端应用程序（在"应用程序/实用工具"中）
3. 输入以下命令，移除应用的隔离属性：

```
sudo xattr -rd com.apple.quarantine /Applications/京东自动评价.app
```

4. 输入您的管理员密码（输入时不会显示字符）
5. 现在可以正常打开应用

## 特别说明

1. 如果首次运行时显示"意外退出"，请尝试以下步骤：
   - 确保已使用上述方法移除隔离属性
   - 确保您有足够的磁盘空间（至少100MB）
   - 确保您的系统支持64位应用

2. 如果应用仍然无法启动：
   - 尝试重启电脑
   - 检查是否有安全软件阻止了应用运行
   - 尝试将应用复制到不同的位置（如桌面）再运行

如有任何问题，请联系开发者获取支持。""")

        # 创建辅助启动脚本
        with open("dist/打开京东自动评价.command", "w", encoding="utf-8") as f:
            f.write("""#!/bin/bash

# 京东自动评价 - 启动脚本
# 此脚本会自动移除应用程序的隔离属性并启动应用

# 设置应用程序路径
APP_PATH="/Applications/京东自动评价.app"
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"
DMG_PATH="$CURRENT_DIR/京东自动评价安装包.dmg"
DMG_SIGNED_PATH="$CURRENT_DIR/京东自动评价安装包-已签名.dmg"

# 显示欢迎信息
echo "====================================="
echo "    京东自动评价程序启动工具"
echo "====================================="

# 检查应用是否已安装
if [ ! -d "$APP_PATH" ]; then
    echo "应用程序未安装在应用程序文件夹中"
    echo "正在查找DMG文件..."

    # 尝试挂载DMG
    if [ -f "$DMG_SIGNED_PATH" ]; then
        echo "找到已签名DMG文件，正在挂载..."
        hdiutil attach "$DMG_SIGNED_PATH"
    elif [ -f "$DMG_PATH" ]; then
        echo "找到DMG文件，正在挂载..."
        hdiutil attach "$DMG_PATH"
    else
        echo "未找到DMG安装文件，请先安装应用程序"
        echo "请将应用程序复制到应用程序文件夹后再运行此脚本"
        read -p "按回车键退出..."
        exit 1
    fi

    echo "请将挂载的DMG中的应用拖到应用程序文件夹，然后再次运行此脚本"
    read -p "按回车键退出..."
    exit 0
fi

# 移除隔离属性
echo "正在移除应用程序的隔离属性..."
sudo xattr -rd com.apple.quarantine "$APP_PATH"
if [ $? -eq 0 ]; then
    echo "隔离属性已成功移除"
else
    echo "移除隔离属性需要管理员权限"
    echo "请输入您的管理员密码（输入时不会显示字符）"
    sudo xattr -rd com.apple.quarantine "$APP_PATH"
fi

# 确保可执行文件有执行权限
EXECUTABLE="$APP_PATH/Contents/MacOS/京东自动评价"
if [ -f "$EXECUTABLE" ]; then
    echo "设置可执行权限..."
    sudo chmod +x "$EXECUTABLE"
fi

# 修复应用程序所有权
USER=$(whoami)
sudo chown -R "$USER" "$APP_PATH"

# 启动应用
echo "正在启动应用程序..."
open "$APP_PATH"

echo "启动完成！"
echo "如果应用程序没有自动打开，请手动打开应用程序文件夹中的京东自动评价应用"
echo "====================================="

# 等待几秒再退出
sleep 3""")
        
        # 添加执行权限
        subprocess.run(["chmod", "+x", "dist/打开京东自动评价.command"])
        
        # 创建独立启动器
        create_standalone_launcher()

    print("文件复制完成")

def create_dmg_for_mac(app_name):
    """为macOS创建DMG安装包"""
    system = platform.system().lower()
    if system != "darwin" or app_name is None:
        return
        
    print(f"为macOS创建DMG安装包: {app_name}")
    try:
        # 检查是否安装了create-dmg
        result = subprocess.run(["which", "create-dmg"], capture_output=True, text=True)
        
        if result.returncode == 0:
            # 使用create-dmg创建DMG
            dmg_file = f"dist/京东自动评价安装包.dmg"
            if os.path.exists(dmg_file):
                os.remove(dmg_file)
                
            cmd = [
                "create-dmg",
                "--volname", "京东自动评价",
                "--volicon", "icon.icns",
                "--window-pos", "200", "120",
                "--window-size", "800", "400",
                "--icon-size", "100",
                "--icon", f"{app_name}", "200", "190",
                "--hide-extension", f"{app_name}",
                "--app-drop-link", "600", "190",
                "--add-file", "macOS安装说明.txt", "400", "190",
                "--add-file", "打开京东自动评价.command", "400", "290",
                "--add-file", "启动京东自动评价.command", "200", "290",
                dmg_file,
                f"dist/{app_name}"
            ]
            
            # 切换到dist目录执行
            current_dir = os.getcwd()
            os.chdir("dist")
            
            # 构建DMG
            print("执行DMG创建命令:", " ".join(cmd))
            subprocess.run(cmd)
            
            # 返回原目录
            os.chdir(current_dir)
            
            print(f"DMG安装包创建成功: {dmg_file}")
        else:
            # 使用hdiutil创建简单的DMG
            dmg_file = "dist/京东自动评价安装包.dmg"
            if os.path.exists(dmg_file):
                os.remove(dmg_file)
                
            # 创建临时目录
            temp_dir = "dist/dmg_temp"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # 复制应用和说明文件
            shutil.copytree(f"dist/{app_name}", f"{temp_dir}/{app_name}")
            if os.path.exists("dist/macOS安装说明.txt"):
                shutil.copy2("dist/macOS安装说明.txt", temp_dir)
            if os.path.exists("dist/打开京东自动评价.command"):
                shutil.copy2("dist/打开京东自动评价.command", temp_dir)
            if os.path.exists("dist/启动京东自动评价.command"):
                shutil.copy2("dist/启动京东自动评价.command", temp_dir)
            
            # 创建DMG
            subprocess.run([
                "hdiutil", "create", "-volname", "京东自动评价", 
                "-srcfolder", temp_dir, "-ov", "-format", "UDZO", 
                dmg_file
            ])
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            print(f"DMG安装包创建成功: {dmg_file}")
            
            # 生成已签名版本
            print("正在创建带签名的DMG...")
            signed_dmg = "dist/京东自动评价安装包-已签名.dmg"
            if os.path.exists(signed_dmg):
                os.remove(signed_dmg)
                
            # 对DMG进行ad-hoc签名
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", dmg_file])
            shutil.copy2(dmg_file, signed_dmg)
            
            print(f"签名版DMG创建成功: {signed_dmg}")
    except Exception as e:
        print(f"创建DMG安装包时出错: {e}")
        print("将继续生成ZIP文件...")

def create_zip_package(app_name):
    """创建ZIP压缩包"""
    if app_name is None:
        return
        
    system = platform.system().lower()
    arch = get_architecture()
    
    # 确定ZIP文件名
    if system == "darwin":
        zip_name = f"dist/京东自动评价-macOS-{arch}.zip"
    elif system == "windows":
        zip_name = "dist/京东自动评价-Windows.zip"
    else:
        zip_name = "dist/京东自动评价-Linux.zip"
    
    print(f"创建ZIP压缩包: {zip_name}")
    
    try:
        # 清理已存在的ZIP
        if os.path.exists(zip_name):
            os.remove(zip_name)
            
        # 准备要压缩的文件
        files_to_zip = [f"dist/{app_name}"]
        
        # 添加说明文件
        if system == "darwin":
            if os.path.exists("dist/macOS安装说明.txt"):
                files_to_zip.append("dist/macOS安装说明.txt")
            if os.path.exists("dist/打开京东自动评价.command"):
                files_to_zip.append("dist/打开京东自动评价.command")
            
        # 创建ZIP
        import zipfile
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_zip:
                if os.path.isdir(file):
                    for root, dirs, files in os.walk(file):
                        for f in files:
                            file_path = os.path.join(root, f)
                            arcname = os.path.relpath(file_path, 'dist')
                            zipf.write(file_path, arcname)
                else:
                    arcname = os.path.basename(file)
                    zipf.write(file, arcname)
        
        # 创建已签名版本
        if system == "darwin":
            signed_zip_name = f"dist/京东自动评价-macOS-{arch}-已签名.zip"
            if os.path.exists(signed_zip_name):
                os.remove(signed_zip_name)
            
            # 对应用进行ad-hoc签名
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", f"dist/{app_name}"])
            
            # 创建带签名应用的ZIP
            with zipfile.ZipFile(signed_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files_to_zip:
                    if os.path.isdir(file):
                        for root, dirs, files in os.walk(file):
                            for f in files:
                                file_path = os.path.join(root, f)
                                arcname = os.path.relpath(file_path, 'dist')
                                zipf.write(file_path, arcname)
                    else:
                        arcname = os.path.basename(file)
                        zipf.write(file, arcname)
            
            print(f"签名版ZIP创建成功: {signed_zip_name}")
                    
        print(f"ZIP压缩包创建成功: {zip_name}")
    except Exception as e:
        print(f"创建ZIP压缩包时出错: {e}")
        
def main():
    parser = argparse.ArgumentParser(description="京东自动评价打包工具")
    parser.add_argument("--onefile", action="store_true", help="打包为单个文件")
    parser.add_argument("--launcher", action="store_true", help="使用启动器作为主程序入口")
    parser.add_argument("--no-dmg", action="store_true", help="不创建DMG安装包(仅macOS)")
    parser.add_argument("--target-architecture", help="指定目标架构(arm64或x86_64)")
    args = parser.parse_args()
    
    install_dependencies()
    output_name = build_executable(args)
    copy_additional_files(output_name)
    
    # 为macOS创建DMG
    if platform.system().lower() == "darwin" and not args.no_dmg:
        create_dmg_for_mac(output_name)
    
    # 创建ZIP压缩包
    create_zip_package(output_name)
    
    print("打包流程全部完成，请检查dist目录")
    
    # 显示附加说明
    system = platform.system().lower()
    if system == "darwin":
        print("\n注意：在macOS上首次运行时，需要在'系统设置'>'隐私与安全性'中允许应用运行")
        print("或者在终端中运行命令：xattr -cr \"dist/京东自动评价.app\"")
        print("如果你有Apple开发者账号，请考虑使用codesign对应用进行签名以避免安全警告")
        print("\n最简单的方法是使用dist目录中的'启动京东自动评价.command'脚本，它会自动处理安全限制")

if __name__ == "__main__":
    main() 