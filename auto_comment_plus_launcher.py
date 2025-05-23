#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @File: auto_comment_plus_launcher.py
# @Description: 京东自动评价统一启动器

import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="京东自动评价工具")
    parser.add_argument("--gui", action="store_true", help="使用图形界面模式启动")
    parser.add_argument("--cli", action="store_true", help="使用命令行模式启动")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不会实际提交评价")
    parser.add_argument("-lv", "--log-level", help="日志级别 (DEBUG/INFO/WARNING/ERROR)", default="INFO")
    parser.add_argument("-o", "--log-file", help="日志文件路径", default="log.txt")
    
    # 如果没有参数，默认启动GUI模式
    if len(sys.argv) == 1:
        sys.argv.append("--gui")  # 添加默认参数
    
    args = parser.parse_args()
    
    # 如果--gui和--cli都没有指定，但有其他参数，默认为CLI模式
    if not args.gui and not args.cli and len(sys.argv) > 1:
        args.cli = True
    
    # GUI模式
    if args.gui:
        try:
            from jd_gui import main as gui_main
            gui_main()
        except ImportError:
            print("错误: 无法导入GUI模块。请确保安装了PyQt6库: pip install PyQt6")
            sys.exit(1)
    # CLI模式
    elif args.cli:
        try:
            # 导入命令行版本
            try:
                from auto_comment_plus_mod import main as cli_main
            except ImportError:
                print("错误: 无法导入命令行模块。请确保auto_comment_plus_mod.py文件存在")
                sys.exit(1)
                
            # 保存原始参数和命令行参数
            cli_argv = ["auto_comment_plus_mod.py"]
            if args.dry_run:
                cli_argv.append("--dry-run")
            if args.log_level:
                cli_argv.append("-lv")
                cli_argv.append(args.log_level)
            if args.log_file:
                cli_argv.append("-o")
                cli_argv.append(args.log_file)
            
            # 保存原始参数
            original_argv = sys.argv.copy()
            
            # 设置sys.argv以供命令行解析使用
            sys.argv = cli_argv
            
            # 手动构建选项并调用main函数
            import logging
            import yaml
            
            # 创建一个opts字典，直接传递给main函数
            opts = {"dry_run": args.dry_run, "log_level": args.log_level}
            if args.log_file:
                opts["log_file"] = args.log_file
            
            # 设置基本日志
            _logging_level = getattr(logging, args.log_level.upper())
            logger = logging.getLogger("comment")
            logger.setLevel(level=_logging_level)
            
            # 添加控制台处理器
            console = logging.StreamHandler()
            console.setLevel(_logging_level)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console.setFormatter(formatter)
            logger.addHandler(console)
            opts["logger"] = logger
            
            # 如果需要文件日志
            if args.log_file:
                try:
                    file_handler = logging.FileHandler(args.log_file, "w")
                    file_handler.setLevel(_logging_level)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
                except Exception as e:
                    logger.error(f"无法创建日志文件: {str(e)}")
            
            # 调用主函数
            cli_main(opts)
            
            # 恢复原始参数
            sys.argv = original_argv
        except Exception as e:
            import traceback
            print(f"错误: {str(e)}")
            print(traceback.format_exc())
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 