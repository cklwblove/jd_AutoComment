# 京东自动评价工具

这是一个能够自动为京东订单生成评价、追评和服务评价的工具，提供了图形界面便于操作。

## 功能特性

- 自动评价待评价订单
- 自动生成追评
- 自动进行服务评价
- 支持上传晒图
- 图形界面操作，简单易用
- 支持随时停止评价过程

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 快速启动（推荐）

使用统一启动器启动程序，可以自动选择图形界面或命令行模式：

```bash
# 默认启动图形界面
python auto_comment_plus_launcher.py

# 指定使用图形界面
python auto_comment_plus_launcher.py --gui

# 指定使用命令行，并传递参数
python auto_comment_plus_launcher.py --cli --dry-run -lv DEBUG
```

### 图形界面启动

```bash
# 直接启动图形界面
python jd_gui.py
```

### 命令行使用

如果不使用图形界面，可以直接使用命令行：

```bash
# 使用增强版本（推荐）
python auto_comment_plus_mod.py [--dry-run] [-lv DEBUG|INFO|WARNING|ERROR] [-o log_file]

# 或使用原始版本
python auto_comment_plus.py [--dry-run] [-lv DEBUG|INFO|WARNING|ERROR] [-o log_file]
```

参数说明：
- `--dry-run`：模拟运行，不实际提交评价
- `-lv, --log-level`：设置日志级别 
- `-o, --log-file`：指定日志文件路径

> 注意：`auto_comment_plus_mod.py` 是优化版，对获取订单信息的方法进行了增强，推荐使用。

### 使用步骤

1. 获取京东Cookie
   - 登录京东网页版：https://www.jd.com/
   - 进入评价页面：https://club.jd.com/myJdcomments/myJdcomment.action
   - 浏览器开发者工具(F12) -> 网络 -> 刷新页面 -> 找到请求头中的Cookie
   
2. 在程序界面输入Cookie，点击"保存Cookie"

3. 选择日志级别，建议普通用户使用"INFO"级别，排查问题使用"DEBUG"级别

4. 点击"开始评价"按钮开始自动评价过程

5. 如需停止，点击"停止评价"按钮

## 常见问题解决

### 获取不到订单信息

如果遇到"获取不到订单信息"或"Cookie出现错误"的提示：

1. 确认Cookie是否有效
   - 重新获取最新的Cookie（注意复制完整，包括所有分号和值）
   - 确保包含关键Cookie值：pin, _pst, thor, TrackID

2. 检查日志文件
   - 使用DEBUG级别运行程序：`python auto_comment_plus_launcher.py --cli -lv DEBUG -o debug.log`
   - 查看生成的debug.log文件和debug_*.html文件找出问题

3. 切换评价页面
   - 建议使用电脑端直接访问：https://club.jd.com/myJdcomments/myJdcomment.action
   - 确保账号中有待评价的订单

4. 尝试使用增强版本
   - 使用`auto_comment_plus_mod.py`代替`auto_comment_plus.py`
   - 增强版本添加了更多的页面解析方法和错误处理

## 图形界面新功能

最新版本的图形界面增加了以下功能：

1. **Cookie验证提示**：在保存Cookie时会检查关键值是否存在，并给出提示
2. **帮助按钮**：提供获取Cookie方法和常见问题解决方案的详细说明
3. **版本标识**：显示当前使用的程序版本
4. **优化的停止功能**：更可靠的评价过程停止机制

## 注意事项

- Cookie有效期有限，过期后需要重新获取
- 可能会因为京东页面结构的变更导致评价失败，如遇问题请提交issue
- 如果没有待评价订单，程序会提示"当前没有需要评价的订单"
- 程序运行期间不要操作京东页面或进行手动评价

## 文件说明

- `auto_comment_plus_launcher.py`：统一启动器（推荐使用）
- `jd_gui.py`：图形界面程序
- `auto_comment_plus.py`：原始核心评价功能模块
- `auto_comment_plus_mod.py`：优化版核心功能模块（推荐使用）
- `config.yml`：默认配置文件
- `config.user.yml`：用户配置文件，保存用户Cookie

## 免责声明

本工具仅供学习交流使用，使用本工具产生的任何后果由使用者自行承担。

## 鸣谢

感谢[qiu-lzsnmb](https://github.com/qiu-lzsnmb)大佬的脚本和[Zhang Jiale](https://github.com/2274900)大佬的评论爬虫

源库链接：[自动评价](https://github.com/qiu-lzsnmb/jd_lzsnmb)
[评论爬虫](https://github.com/2274900/JD_comment_spider)

### 本脚本只是对以上两位的结合以及魔改，用于解决评论文不对题的问题。经测试，本脚本能初步解决这一问题

## 思路

由爬虫先行对商品的既有评价进行爬取，在此基础上进行自己的评价

## 用法

> 请先确保python版本为3.8+，最好是python3.10+。

### 分支说明

main分支为开发版，更新较快，但由于开发者cookie数量远远不足以满足开发需求，测试不够完备，可能存在bug。

stable分支为稳定版，更新较慢，基本可以稳定使用，但功能可能存在欠缺。

more_cookie分支是有需要多账号进行批量评论诞生的分支。

> 由于作者只有一个 jd 账号，因此该more_cookie分支，需要有多账号的朋友进行测试。
> 目前代码逻辑是 先普通评价-》再追评-》再第二个账号继续执行前面的顺序。所以你多账号可能要历史追评结束后才会执行，cookie 可能会失效，如果很多个 jd 账号话。可能实际上效果没那么好。

### 安装依赖库

```bash
pip install -r requirements.
# or
python3 -m pip install -r requirements

请用户自行判断使用哪个分支。

### 快速使用

在终端中执行：

```bash
git clone https://github.com/Dimlitter/jd_AutoComment.git
cd jd_AutoComment
pip install -r requirements.txt
```

`https://club.jd.com/myJdcomments/myJdcomment.action`打开该链接，登录账号后获取 xhr 请求下的 `cookie`，`全部`填入配置文件。可以选择填入默认配置文件 `config.yml` ；也可以填入用户配置文件 `config.user.yml` （需要新建后将 `config.yml` 中的内容复制到该文件中），避免后续的更新覆盖 `config.yml` 中的内容。

需要填入如下内容：

```yml
user:
  cookie: '<Cookie>'
```

例如，若获取得到的ck为 `a=1; b=2; c=3` ，则配置文件中填入：

```yml
user:
  cookie: 'a=1; b=2; c=3'
```

最后运行 `auto_comment_plus.py` ：

```bash
python3 auto_comment_plus.py
```

**注意:** 请根据设备环境换用不同的解释器路径，如 `python`、`py`。

### 命令行参数

本程序支持命令行参数：

```text
usage: auto_comment_plus.py [-h] [--dry-run] [--log-level LOG_LEVEL] [-o LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --dry-run             have a full run without comment submission
  --log-level LOG_LEVEL
                        specify logging level (default: info)
  -o LOG_FILE, --log-file LOG_FILE
                        specify logging file
```

**`-h`, `--help`:**

显示帮助文本。

**`--dry-run`:**

完整地运行程序，但不实际提交评论。

**`--log-level LOG_LEVEL`:**

设置输出日志的等级。默认为 `INFO` 。可选等级为 `DEBUG`、`INFO`、`WARNING`、`ERROR` ，输出内容量依次递减。

**注意:** 若你需要提交 issue 来报告一个 bug ，请将该选项设置为 `DEBUG` 。

**`-o LOG_FILE`:**

设置输出日志文件的路径。若无此选项，则不输出到文件。

## 声明

本项目为Python学习交流的开源非营利项目，仅作为程序员之间相互学习交流之用。

严禁用于商业用途，禁止使用本项目进行任何盈利活动。

使用者请遵从相关政策。对一切非法使用所产生的后果，我们概不负责。

本项目对您如有困扰请联系我们删除。

## 证书

![AUR](https://img.shields.io/badge/license-MIT%20License%202.0-green.svg)
