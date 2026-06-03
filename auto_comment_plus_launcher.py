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
    if not args.gui and not args.cli:
        if len(sys.argv) > 1:
            args.cli = True
        else:
            args.gui = True
    
    # GUI模式
    if args.gui:
        # 导入GUI模块
        try:
            import jd_gui
            import auto_comment_plus_mod
            import yaml
            import requests
            import logging
            import time
            from PyQt6.QtWidgets import QApplication
            
            # 设置日志级别
            log_level = getattr(logging, args.log_level.upper())
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            
            # 读取配置文件获取cookie
            cookie = None
            config_path = "./config.user.yml" if os.path.exists("./config.user.yml") else "./config.yml"
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        if config and 'user' in config and 'cookie' in config['user']:
                            cookie = config['user']['cookie']
                            
                            # 如果cookie是字节类型，先解码
                            if isinstance(cookie, bytes):
                                cookie = cookie.decode('utf-8')
                            
                            # 规范化cookie格式
                            cookie = ' '.join([part.strip() for part in cookie.split('\n')])
                            
                            # 预设置全局变量
                            auto_comment_plus_mod.headers = {
                                "Cookie": cookie,
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                                "Connection": "keep-alive",
                                "Cache-Control": "max-age=0",
                                "sec-ch-ua": '"Chromium";v="114", "Not=A?Brand";v="8"',
                                "sec-ch-ua-mobile": "?0",
                                "sec-ch-ua-platform": '"macOS"',
                                "DNT": "1",
                                "Upgrade-Insecure-Requests": "1",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                                "Sec-Fetch-Site": "same-origin",
                                "Sec-Fetch-Mode": "navigate",
                                "Sec-Fetch-User": "?1",
                                "Sec-Fetch-Dest": "document",
                                "Referer": "https://club.jd.com/",
                                "Accept-Encoding": "gzip, deflate, br",
                                "Accept-Language": "zh-CN,zh;q=0.9",
                            }
                            
                            auto_comment_plus_mod.headers2 = {
                                "Cookie": cookie,
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                                "Connection": "keep-alive",
                                "Content-Type": "application/x-www-form-urlencoded",
                                "X-Requested-With": "XMLHttpRequest",
                                "sec-ch-ua": '"Chromium";v="114", "Not=A?Brand";v="8"',
                                "sec-ch-ua-mobile": "?0",
                                "sec-ch-ua-platform": '"macOS"',
                                "Accept": "application/json, text/javascript, */*; q=0.01",
                                "Origin": "https://club.jd.com",
                                "Sec-Fetch-Site": "same-origin",
                                "Sec-Fetch-Mode": "cors",
                                "Sec-Fetch-Dest": "empty",
                                "Referer": "https://club.jd.com/myJdcomments/myJdcomment.action",
                                "Accept-Encoding": "gzip, deflate, br",
                                "Accept-Language": "zh-CN,zh;q=0.9",
                            }
                            
                            try:
                                auto_comment_plus_mod.jdspider.cookie = cookie.encode('utf-8')
                            except Exception as e:
                                print(f"设置cookie时出错: {e}")
                                auto_comment_plus_mod.jdspider.cookie = cookie
                except Exception as e:
                    print(f"读取配置文件失败: {e}")
            
            # 创建应用程序
            app = QApplication(sys.argv)
            
            try:
                # 如果cookie有效，预获取评价数据
                pre_loaded_orders = None
                if cookie:
                    print("预获取评价数据中...")
                    
                    # 创建一个会话对象用于所有请求
                    session = requests.Session()
                    
                    # 验证cookie有效性
                    try:
                        test_url = 'https://order.jd.com/center/list.action'
                        test_resp = session.get(test_url, headers=auto_comment_plus_mod.headers, allow_redirects=False, timeout=15)
                        
                        if test_resp.status_code == 302 and 'login' in test_resp.headers.get('Location', ''):
                            print("Cookie验证失败: 被重定向到登录页面")
                        elif test_resp.status_code == 200:
                            print("Cookie验证成功")
                            
                            # 预热评价页面
                            preheat_urls = [
                                "https://club.jd.com/myJdcomments/myJdcomment.action",
                                "https://club.jd.com/myJdcomments/myJdcomment.action?tabType=newComment",
                                "https://club.jd.com/myJdcomments/myJdcomment.action?tabType=reviewComment",
                                "https://club.jd.com/myJdcomments/myJdcomment.action?tabType=serviceComment"
                            ]
                            
                            for url in preheat_urls:
                                print(f"预热页面: {url}")
                                resp = session.get(url, headers=auto_comment_plus_mod.headers, timeout=15)
                                time.sleep(1)  # 短暂暂停避免请求过快
                            
                            # 设置日志级别
                            opts = {
                                "dry_run": args.dry_run,
                                "log_level": args.log_level,
                                "logger": logging.getLogger('auto_comment'),
                                "config": {
                                    "cookie": cookie
                                },
                                "session": session  # 传递会话对象
                            }
                            
                            # 获取评价数据
                            try:
                                pre_loaded_orders = auto_comment_plus_mod.No(opts)
                                if pre_loaded_orders:
                                    print("预获取评价数据成功:")
                                    order_info = "----".join([f"{i} {pre_loaded_orders[i]}" for i in pre_loaded_orders])
                                    print(order_info)
                            except Exception as e:
                                print(f"预获取评价数据失败: {e}")
                        else:
                            print(f"Cookie验证返回未知状态码: {test_resp.status_code}")
                    except Exception as e:
                        print(f"验证Cookie时出错: {e}")
                
                # 创建主窗口实例
                window = jd_gui.JDAutoCommentGUI()
                
                # 设置预加载的订单数据
                if pre_loaded_orders:
                    window.pre_loaded_orders = pre_loaded_orders
                    
                    # 创建一个会话对象并保存到窗口实例
                    if 'session' in locals():
                        window.session = session
                
                # 显示窗口
                window.show()
                
                # 启动应用程序的事件循环
                return app.exec()
            except Exception as e:
                print(f"GUI启动失败: {e}")
                import traceback
                print(traceback.format_exc())
                return 1
        except ImportError as e:
            print(f"导入GUI模块失败: {e}")
            print("请确保已安装PyQt6库，可以使用以下命令安装：pip install PyQt6")
            return 1

    # CLI模式
    elif args.cli:
        # 导入必要的模块
        try:
            # 设置参数并执行主程序
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_comment_plus.py")
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
                
            # 将args变量传给脚本执行环境
            exec_vars = {'__name__': '__main__', 'sys': sys}
            if args.dry_run:
                sys.argv.append("--dry-run")
                
            # 使用特定的日志级别
            if args.log_level:
                sys.argv.extend(["-lv", args.log_level])
                
            # 执行脚本
            exec(compile(script_content, script_path, 'exec'), exec_vars)
            return 0
        except Exception as e:
            print(f"CLI模式执行失败: {e}")
            import traceback
            print(traceback.format_exc())
            return 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 