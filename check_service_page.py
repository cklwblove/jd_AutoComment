import requests
from lxml import etree
import yaml

# 加载配置文件
with open("./config.yml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# 获取用户的 cookie
cookie = cfg["user"]["cookie"]

# 设置请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Cookie": cookie
}

# 发送请求 - 访问服务评价页面
response = requests.get("https://club.jd.com/myJdcomments/myJdcomment.action?sort=4", headers=headers)
print(f"状态码: {response.status_code}")
print(f"响应URL: {response.url}")

# 检查是否重定向到登录页面
if "login.aspx" in response.url or "passport.jd.com" in response.url:
    print("Cookie已失效，需要重新登录并获取新的Cookie")
    exit(0)

# 解析HTML
html = etree.HTML(response.text)

# 打印标题，确认是否进入了服务评价页面
try:
    title = html.xpath('//title/text()')[0]
    print(f"页面标题: {title}")
except:
    print("无法获取页面标题")

# 检查是否是服务评价页面
service_elements = html.xpath('//*[contains(text(), "服务评价")]')
if service_elements:
    print("成功进入服务评价页面")
else:
    print("未能进入服务评价页面，可能是Cookie已失效")
    exit(0)

# 尝试查找服务评价订单数据
print("\n尝试查找服务评价订单数据...")

# 原始XPath选择器
original_xpaths = [
    '//*[@id="main"]/div[2]/div[2]/table/tbody/tr[@class="tr-bd"]',
    '//*[@id="main"]/div[2]/div[2]/table/tr[@class="tr-bd"]'
]

for xpath in original_xpaths:
    elements = html.xpath(xpath)
    print(f"XPath '{xpath}' 找到 {len(elements)} 个元素")
    if elements:
        for i, element in enumerate(elements[:2]):  # 只显示前2个元素
            print(f"元素 {i+1}:")
            # 尝试获取商品名称
            try:
                oname = element.xpath("td[1]/div[1]/div[2]/div/a/text()")
                print(f"  商品名称: {oname}")
            except:
                print("  无法获取商品名称")
            
            # 尝试获取订单ID
            try:
                oid = element.xpath("td[4]/div/a[1]/@oid")
                print(f"  订单ID: {oid}")
            except:
                print("  无法获取订单ID")
            
            # 打印元素的HTML
            try:
                elem_html = etree.tostring(element, pretty_print=True, encoding="utf-8").decode("utf-8")
                print(f"  HTML片段(前300字符): {elem_html[:300]}...")
            except:
                print("  无法获取HTML")

# 尝试其他可能的XPath选择器
alternative_xpaths = [
    '//table[contains(@class, "order-tb")]/tbody/tr[not(contains(@class, "tr-th"))]',
    '//table[contains(@class, "order-tb")]/tr[not(contains(@class, "tr-th"))]',
    '//div[contains(@class, "comment-item")]',
    '//div[contains(@class, "commentlist")]/div',
    '//div[@id="main"]//table//tr[position() > 1]'  # 跳过表头行
]

print("\n尝试其他可能的XPath选择器...")
for xpath in alternative_xpaths:
    elements = html.xpath(xpath)
    print(f"XPath '{xpath}' 找到 {len(elements)} 个元素")
    if elements and len(elements) > 0:
        for i, element in enumerate(elements[:2]):  # 只显示前2个元素
            print(f"元素 {i+1} 的标签: {element.tag}")
            # 打印元素的HTML
            try:
                elem_html = etree.tostring(element, pretty_print=True, encoding="utf-8").decode("utf-8")
                print(f"  HTML片段(前300字符): {elem_html[:300]}...")
            except:
                print("  无法获取HTML")

# 分析页面整体结构
print("\n页面整体结构分析...")
main_element = html.xpath('//div[@id="main"]')
if main_element:
    print("找到主要内容区域")
    main_html = etree.tostring(main_element[0], pretty_print=True, encoding="utf-8").decode("utf-8")
    # 打印页面结构的部分内容
    print(f"主要内容区域结构(前500字符):\n{main_html[:500]}...")
    
    # 查找表格
    tables = main_element[0].xpath('.//table')
    print(f"找到 {len(tables)} 个表格")
    
    if tables:
        for i, table in enumerate(tables):
            print(f"\n表格 {i+1}:")
            # 查找表格的所有行
            rows = table.xpath('./tbody/tr | ./tr')
            print(f"  表格包含 {len(rows)} 行")
            
            if rows:
                # 分析第一行，通常是表头
                if len(rows) > 0:
                    print("  表头内容:")
                    header_html = etree.tostring(rows[0], pretty_print=True, encoding="utf-8").decode("utf-8")
                    print(f"  {header_html[:200]}...")
                
                # 分析数据行
                if len(rows) > 1:
                    print("  第一个数据行:")
                    row_html = etree.tostring(rows[1], pretty_print=True, encoding="utf-8").decode("utf-8")
                    print(f"  {row_html[:200]}...")
                    
                    # 尝试找到订单ID和商品名称
                    try:
                        oname = rows[1].xpath(".//div[contains(@class, 'goods-item')]/div[contains(@class, 'p-name')]/a/text() | .//a[contains(@class, 'product-detail')]/text()")
                        print(f"  商品名称: {oname}")
                    except:
                        print("  无法确定商品名称")
                    
                    try:
                        oid = rows[1].xpath(".//@oid | .//a[contains(@class, 'btn-def')]/@oid")
                        print(f"  订单ID: {oid}")
                    except:
                        print("  无法确定订单ID")
else:
    print("未找到主要内容区域") 