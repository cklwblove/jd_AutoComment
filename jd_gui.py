'''
FilePath: /jd_AutoComment/jd_gui.py
'''
import sys
import os
import logging
import yaml
import threading
import traceback
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, 
                            QFileDialog, QTabWidget, QProgressBar, QSplitter, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QIcon, QTextCursor, QFont

# 导入主程序
import auto_comment_plus_mod


# 自定义日志处理器，将日志信息发送到GUI
class QTextEditLogger(logging.Handler, QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_widget = text_widget
        self.log_signal.connect(self.append_text)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        log_message = self.format(record)
        self.log_signal.emit(log_message)

    def append_text(self, message):
        self.text_widget.append(message)
        self.text_widget.moveCursor(QTextCursor.MoveOperation.End)


class JDAutoCommentGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_path = "./config.yml"
        self.user_config_path = "./config.user.yml"
        self.cookie = ""
        self.comment_thread = None
        
        # 创建必要的目录
        self.ensure_directories()
        
        self.init_ui()
        self.load_cookie()

    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = ["img", "logs"]
        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logging.debug(f"创建目录: {directory}")
                except Exception as e:
                    logging.error(f"无法创建目录 {directory}: {e}")

    def init_ui(self):
        self.setWindowTitle("京东自动评价工具")
        self.setMinimumSize(800, 600)
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Cookie配置区域
        config_layout = QVBoxLayout()
        
        cookie_layout = QHBoxLayout()
        cookie_label = QLabel("京东Cookie:")
        self.cookie_input = QLineEdit()
        self.cookie_input.setPlaceholderText("请输入您的京东Cookie (从club.jd.com/myJdcomments/myJdcomment.action获取)")
        self.cookie_input.setEchoMode(QLineEdit.EchoMode.Password)  # 隐藏显示
        toggle_button = QPushButton("显示")
        toggle_button.setMaximumWidth(50)
        toggle_button.clicked.connect(self.toggle_cookie_visibility)
        
        cookie_layout.addWidget(cookie_label)
        cookie_layout.addWidget(self.cookie_input)
        cookie_layout.addWidget(toggle_button)
        
        config_layout.addLayout(cookie_layout)
        
        # 保存Cookie按钮
        save_layout = QHBoxLayout()
        save_cookie_button = QPushButton("保存Cookie")
        save_cookie_button.clicked.connect(self.save_cookie)
        save_layout.addStretch()
        save_layout.addWidget(save_cookie_button)
        
        config_layout.addLayout(save_layout)
        main_layout.addLayout(config_layout)
        
        # 创建分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #ccc;")
        main_layout.addWidget(separator)
        
        # 操作区域
        operation_layout = QHBoxLayout()
        
        # 添加日志级别选择
        log_level_layout = QHBoxLayout()
        log_level_label = QLabel("日志级别:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        log_level_layout.addWidget(log_level_label)
        log_level_layout.addWidget(self.log_level_combo)
        
        # 添加按钮
        self.start_button = QPushButton("开始评价")
        self.start_button.clicked.connect(self.start_comment)
        self.stop_button = QPushButton("停止评价")
        self.stop_button.clicked.connect(self.stop_comment)
        self.stop_button.setEnabled(False)
        
        # 添加版本信息和问题排查提示
        version_label = QLabel("v1.2.0 (优化版)")
        version_label.setStyleSheet("color: gray;")
        help_button = QPushButton("帮助")
        help_button.clicked.connect(self.show_help)
        
        operation_layout.addLayout(log_level_layout)
        operation_layout.addStretch()
        operation_layout.addWidget(version_label)
        operation_layout.addWidget(help_button)
        operation_layout.addWidget(self.start_button)
        operation_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(operation_layout)
        
        # 日志输出区域
        log_label = QLabel("运行日志:")
        main_layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier New", 10))
        main_layout.addWidget(self.log_output)
        
        # 设置日志处理器
        self.setup_logger()
        
    def toggle_cookie_visibility(self):
        if self.cookie_input.echoMode() == QLineEdit.EchoMode.Password:
            self.cookie_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText("隐藏")
        else:
            self.cookie_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText("显示")
    
    def setup_logger(self):
        # 清除现有的根logger处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置新的处理器
        handler = QTextEditLogger(self.log_output)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # 创建日志目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                print(f"创建日志目录失败: {e}")
        
        # 添加文件日志处理器
        try:
            import time
            log_file = os.path.join(log_dir, f"jd_auto_comment_{time.strftime('%Y%m%d_%H%M%S')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logging.info(f"日志文件: {log_file}")
        except Exception as e:
            logging.error(f"设置文件日志失败: {e}")
        
        # 配置root logger
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        
        # 配置其他logger
        for logger_name in ['jdspider', 'comment', 'auto_comment']:
            logger = logging.getLogger(logger_name)
            for h in logger.handlers[:]:
                logger.removeHandler(h)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def load_cookie(self):
        # 先尝试加载用户配置文件
        config_path = self.user_config_path if os.path.exists(self.user_config_path) else self.config_path
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config and 'user' in config and 'cookie' in config['user']:
                        # 获取Cookie并规范化格式
                        cookie = config['user']['cookie']
                        
                        # 如果Cookie是字节类型，先解码
                        if isinstance(cookie, bytes):
                            cookie = cookie.decode('utf-8')
                            
                        # 规范化Cookie格式 - 删除多余空格和换行符
                        cookie = ' '.join([part.strip() for part in cookie.split('\n')])
                        
                        self.cookie = cookie
                        self.cookie_input.setText(self.cookie)
                        
                        # 验证Cookie是否包含关键值
                        cookie_parts = {}
                        for item in cookie.split(';'):
                            if '=' in item:
                                try:
                                    name, value = item.strip().split('=', 1)
                                    cookie_parts[name] = value
                                except Exception:
                                    # 忽略格式不正确的Cookie部分
                                    pass
                                
                        important_cookies = ["pin", "_pst", "thor", "TrackID"]
                        missing_cookies = []
                        for item in important_cookies:
                            if item not in cookie_parts:
                                missing_cookies.append(item)
                                
                        if missing_cookies:
                            logging.warning(f"加载的Cookie缺少关键值: {missing_cookies}")
            except Exception as e:
                QMessageBox.warning(self, "配置加载失败", f"无法加载配置文件: {str(e)}")
    
    def save_cookie(self):
        cookie = self.cookie_input.text().strip()
        if not cookie:
            QMessageBox.warning(self, "保存失败", "Cookie不能为空")
            return
        
        # 规范化Cookie格式 - 删除多余空格和换行符
        cookie = ' '.join([part.strip() for part in cookie.split('\n')])
        
        # 验证Cookie中是否包含关键值
        cookie_parts = {}
        for item in cookie.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookie_parts[name] = value
                
        important_cookies = ["pin", "_pst", "thor", "TrackID"]
        missing_cookies = []
        for item in important_cookies:
            if item not in cookie_parts:
                missing_cookies.append(item)
        
        if missing_cookies:
            response = QMessageBox.warning(
                self, 
                "Cookie可能不完整", 
                f"Cookie中似乎缺少以下重要值: {', '.join(missing_cookies)}\n这可能会导致无法获取订单信息。\n\n是否仍要保存?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.No:
                return
        
        config_path = self.user_config_path  # 优先保存到用户配置文件
        try:
            # 如果已有配置文件，先读取
            config = {'user': {'cookie': cookie}}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f)
                    if existing_config:
                        existing_config['user']['cookie'] = cookie
                        config = existing_config
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            self.cookie = cookie
            self.cookie_input.setText(cookie)  # 更新输入框为规范化后的格式
            QMessageBox.information(self, "保存成功", f"Cookie已保存到 {config_path}")
            
            # 验证Cookie格式
            logging.debug(f"保存的Cookie长度: {len(cookie)}")
            if len(cookie_parts) > 0:
                logging.debug(f"识别到 {len(cookie_parts)} 个Cookie键值对")
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存Cookie失败: {str(e)}")
    
    def set_log_level(self):
        level_name = self.log_level_combo.currentText()
        level = getattr(logging, level_name)
        
        # 设置root logger和其他logger的级别
        logging.getLogger().setLevel(level)
        logging.getLogger('jdspider').setLevel(level)
        logging.getLogger('auto_comment').setLevel(level)
        logging.getLogger('comment').setLevel(level)
    
    def start_comment(self):
        # 先保存Cookie
        cookie = self.cookie_input.text().strip()
        if not cookie:
            QMessageBox.warning(self, "启动失败", "请先输入京东Cookie")
            return
            
        # 检查Cookie格式
        important_cookies = ["pin", "_pst", "thor", "TrackID"]
        missing_cookies = []
        
        # 预处理Cookie
        cookie_parts = {}
        for item in cookie.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookie_parts[name] = value
                
        for item in important_cookies:
            if item not in cookie and item not in cookie_parts:
                missing_cookies.append(item)
                
        if missing_cookies:
            response = QMessageBox.warning(
                self, 
                "Cookie可能无效", 
                f"您的Cookie中缺少关键值: {', '.join(missing_cookies)}\n这可能会导致评价失败。\n\n确定要继续吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.No:
                return
                
        # 规范化Cookie格式 - 删除多余空格和换行符
        cookie = ' '.join([part.strip() for part in cookie.split('\n')])
                
        # 设置日志级别
        self.set_log_level()
        
        # 保存当前Cookie
        if cookie != self.cookie:
            self.cookie = cookie
            self.save_cookie()
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.cookie_input.setEnabled(False)
        
        # 清理状态
        auto_comment_plus_mod.stop_flag = False
        
        # 创建并启动线程
        level_name = self.log_level_combo.currentText()
        opts = {
            "dry_run": False,
            "log_level": level_name,
            "logger": logging.getLogger('auto_comment'),
            "config": {
                "cookie": cookie
            }
        }
        
        self.comment_thread = threading.Thread(target=self.run_comment, args=(opts,))
        self.comment_thread.daemon = True
        self.comment_thread.start()
    
    def run_comment(self, opts):
        try:
            logging.info("开始执行自动评价...")
            
            # 创建必要的目录
            try:
                auto_comment_plus_mod.ensure_directories()
            except Exception as e:
                logging.warning(f"创建目录结构失败: {e}")
            
            # 预处理Cookie
            cookie = opts.get("config", {}).get("cookie", "")
            if isinstance(cookie, bytes):
                cookie = cookie.decode('utf-8')
            
            # 检查Cookie有效性
            logging.debug(f"Cookie长度: {len(cookie)}")
            
            # 提取关键Cookie值进行检查
            cookie_parts = {}
            for item in cookie.split(';'):
                if '=' in item:
                    try:
                        name, value = item.strip().split('=', 1)
                        cookie_parts[name] = value
                    except Exception:
                        # 忽略格式不正确的Cookie部分
                        continue
            
            # 检查关键值
            important_cookies = ["pin", "_pst", "thor", "TrackID"]
            missing_cookies = [c for c in important_cookies if c not in cookie_parts]
            if missing_cookies:
                logging.warning(f"Cookie缺少关键值: {missing_cookies}")
            else:
                logging.debug("Cookie包含所有必要的关键值")
            
            # 更新opts中的Cookie格式并确保它是字符串
            opts["config"]["cookie"] = cookie
            
            # 预先设置auto_comment_plus中的headers变量
            # 使用全局变量声明确保变量正确更新
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
            
            # 更新jdspider中的cookie
            try:
                auto_comment_plus_mod.jdspider.cookie = cookie.encode('utf-8')
            except Exception as e:
                logging.error(f"设置jdspider cookie时出错: {str(e)}")
                # 尝试直接设置
                auto_comment_plus_mod.jdspider.cookie = cookie if isinstance(cookie, bytes) else cookie.encode('utf-8')
            
            # 先进行单独的Cookie验证
            logging.info("正在验证Cookie有效性...")
            try:
                # 使用会话对象进行请求
                test_session = requests.Session()
                
                # 临时禁用SSL验证，以防SSL错误导致的连接问题
                test_session.verify = True
                
                test_url = 'https://order.jd.com/center/list.action'
                test_resp = test_session.get(test_url, headers=auto_comment_plus_mod.headers, allow_redirects=False, timeout=15)
                
                if test_resp.status_code == 302 and 'login' in test_resp.headers.get('Location', ''):
                    logging.error("Cookie验证失败: 被重定向到登录页面")
                    # 使用QTimer在主线程中显示消息框
                    QTimer.singleShot(0, lambda: QMessageBox.warning(None, "Cookie无效", 
                        "Cookie已失效，请重新获取Cookie!\n\n提示: 请确保从京东评价页面获取完整Cookie，并且在获取后立即使用。"))
                    return
                elif test_resp.status_code == 200:
                    logging.info("Cookie验证成功")
                else:
                    logging.warning(f"Cookie验证返回未知状态码: {test_resp.status_code}")
                    # 继续执行，可能仍然有效
            except requests.exceptions.Timeout:
                logging.error("验证Cookie超时，可能是网络问题")
                QTimer.singleShot(0, lambda: QMessageBox.warning(None, "网络超时", 
                    "验证Cookie时网络超时，请检查网络连接后重试。"))
                return
            except Exception as e:
                logging.error(f"验证Cookie时出错: {str(e)}")
                # 尝试继续执行，可能仍然有效
                logging.warning("尝试继续执行评价流程...")
            
            # 执行评价获取流程
            try:
                # 包装在try-except块中以捕获所有可能的错误
                result = None
                try:
                    # 设置超时更长一些，避免网络波动导致失败
                    result = auto_comment_plus_mod.No(opts)
                except Exception as e:
                    logging.error(f"获取评价数据时出错: {str(e)}")
                    import traceback
                    logging.error(f"错误堆栈: {traceback.format_exc()}")
                    
                if not result:
                    logging.error("获取评价数据失败，请检查Cookie是否有效")
                    # 使用QTimer在主线程中显示消息框
                    QTimer.singleShot(0, lambda: QMessageBox.warning(None, "获取数据失败", 
                        "无法获取评价数据，请检查Cookie是否有效。\n\n提示: 请确保从京东评价页面获取完整Cookie，建议重新登录京东获取新的Cookie。"))
                    return
            except Exception as e:
                logging.error(f"No函数执行出错: {str(e)}")
                import traceback
                logging.error(f"错误堆栈: {traceback.format_exc()}")
                QTimer.singleShot(0, lambda: QMessageBox.warning(None, "获取数据出错", 
                    f"获取评价数据时出错: {str(e)}\n请检查网络连接或重新获取Cookie。"))
                return
                
            # 如果没有待评价的订单
            if result.get("待评价订单", 0) == 0 and result.get("待追评", 0) == 0 and result.get("服务评价", 0) == 0:
                logging.info("当前没有需要评价的订单")
                # 使用QTimer在主线程中显示消息框
                QTimer.singleShot(0, lambda: QMessageBox.information(None, "无待评价订单", "当前没有需要评价的订单，请稍后再试"))
                return
            
            # 执行主评价流程
            try:
                auto_comment_plus_mod.main(opts)
                logging.info("自动评价完成！")
            except Exception as e:
                logging.error(f"main函数执行出错: {str(e)}")
                import traceback
                logging.error(f"错误堆栈: {traceback.format_exc()}")
                QTimer.singleShot(0, lambda: QMessageBox.warning(None, "评价出错", 
                    f"自动评价过程中出错: {str(e)}\n请检查日志获取详细信息。"))
        except Exception as e:
            logging.error(f"自动评价过程中出错: {str(e)}")
            logging.error(traceback.format_exc())
            # 使用QTimer在主线程中显示消息框
            QTimer.singleShot(0, lambda: QMessageBox.critical(None, "评价出错", f"自动评价过程中出错: {str(e)}"))
        finally:
            # 使用QTimer在主线程中更新UI
            QTimer.singleShot(0, self.on_comment_finished)
    
    def on_comment_finished(self):
        # 恢复按钮状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.cookie_input.setEnabled(True)
    
    def stop_comment(self):
        # 这个方法会被停止按钮触发，但由于Python线程不能直接终止，
        # 需要在auto_comment_plus中添加终止标记来实现
        logging.info("正在停止评价过程...")
        auto_comment_plus_mod.stop_flag = True
        
        # 禁用停止按钮，防止重复点击
        self.stop_button.setEnabled(False)
    
    def show_help(self):
        help_text = """
<h3>京东自动评价工具使用帮助</h3>

<h4>获取Cookie的方法：</h4>
<ol>
  <li>使用电脑浏览器登录京东官网</li>
  <li>进入评价页面：<a href="https://club.jd.com/myJdcomments/myJdcomment.action">https://club.jd.com/myJdcomments/myJdcomment.action</a></li>
  <li>按F12打开开发者工具，选择"网络"(Network)标签</li>
  <li>刷新页面，找到名为"myJdcomment.action"的请求</li>
  <li>在右侧找到"请求头"(Request Headers)，复制其中的"Cookie"字段的全部内容</li>
</ol>

<h4>常见问题：</h4>
<ul>
  <li><b>获取不到待评价订单：</b>请确保Cookie完整且有效，包含pin、_pst、thor和TrackID等关键值</li>
  <li><b>评价失败：</b>尝试使用DEBUG日志级别重新运行，查看详细错误信息</li>
  <li><b>程序崩溃：</b>请检查网络连接，或者京东网站可能更新了页面结构</li>
</ul>

<h4>注意事项：</h4>
<ul>
  <li>Cookie有效期有限，失效后需要重新获取</li>
  <li>请勿频繁使用，避免账号异常</li>
  <li>建议在无人值守时使用，评价过程可能需要较长时间</li>
</ul>
"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("使用帮助")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，跨平台一致性较好
    
    # 设置应用程序名称和组织名
    app.setApplicationName("京东自动评价")
    app.setOrganizationName("JDAutoComment")
    
    # 在macOS上设置额外的应用程序属性
    if sys.platform == 'darwin':
        try:
            from PyQt6.QtCore import Qt
            app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
        except Exception as e:
            print(f"设置macOS应用属性失败: {e}")
    
    # 创建并显示主窗口
    try:
        window = JDAutoCommentGUI()
        window.show()
        
        # 在窗口显示后，记录系统环境信息
        logging.info(f"操作系统: {sys.platform}, Python版本: {sys.version}")
        
        # 检查PyQt版本
        try:
            from PyQt6.QtCore import PYQT_VERSION_STR
            logging.info(f"PyQt版本: {PYQT_VERSION_STR}")
        except:
            logging.info("无法获取PyQt版本信息")
            
    except Exception as e:
        print(f"创建主窗口失败: {e}")
        from PyQt6.QtWidgets import QMessageBox
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("启动错误")
        error_box.setText("应用程序启动失败")
        error_box.setDetailedText(f"错误详情: {str(e)}")
        error_box.exec()
        return 1
    
    # 开始应用程序事件循环
    return app.exec()


if __name__ == "__main__":
    main()