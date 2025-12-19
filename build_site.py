import json
import os
import datetime
import shutil
import random
import re

# --- 配置 ---
DATA_FILE = 'symbols_updated.json'     # 数据源
TEMPLATE_FILE = 'symbol_template.html' # 模板文件
OUTPUT_DIR = 'public'
DREAMS_DIR = os.path.join(OUTPUT_DIR, 'dreams')
DOMAIN = "https://dreamwhisperai.com" # !!! 请替换为你的真实域名 !!!

# --- SEO 洗稿文案库 ---
SEO_TITLES_ZH = [
    "梦见{name}是什么意思？2025年心理学与周公解梦全解析",
    "昨晚梦见{name}？揭秘潜意识给你的3个暗示",
    "【解梦百科】梦见{name}是吉是凶？完整版解析来了",
    "梦见{name}预示着什么？专家解读梦境背后的秘密",
    "做梦梦到{name}？这篇分析可能颠覆你的认知",
    "周公解梦：梦见{name}的寓意与运势提醒",
    "心理学解读：为什么你会梦见{name}？"
]

INTRO_TEMPLATES_ZH = [
    "梦境是潜意识的语言。梦见<strong>{name}</strong>究竟意味着什么？",
    "你是否昨晚梦见了<strong>{name}</strong>？这可能不是一个巧合。",
    "在中国传统文化中，<strong>{name}</strong>往往承载着特殊的象征意义。",
    "当你醒来记得自己梦见了<strong>{name}</strong>，你的潜意识正在试图告诉你什么？",
    "<strong>{name}</strong>出现在梦中，通常与你近期的情绪状态息息相关。"
]

# --- 辅助函数：清理 HTML 标签用于 Meta 标签 ---
def clean_html_tags(text):
    if not text: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).replace('"', "'").replace('\n', ' ')

# --- 确保目录存在 ---
if not os.path.exists(DREAMS_DIR):
    os.makedirs(DREAMS_DIR)

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"错误：找不到 {DATA_FILE}，请先运行爬虫 scraper.py")
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_detail_pages(data):
    print(f"正在加载模板: {TEMPLATE_FILE}...")
    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到模板文件 {TEMPLATE_FILE}")
        return

    count = 0
    for item in data:
        html = template_content
        zh_data = item.get('zh', {})
        name = zh_data.get('name', '')
        
        # --- 1. 内容生成 ---
        seo_title_template = random.choice(SEO_TITLES_ZH)
        seo_title = seo_title_template.format(name=name)
        
        intro_template = random.choice(INTRO_TEMPLATES_ZH)
        seo_intro = intro_template.format(name=name)
        
        original_summary = zh_data.get('summary', '')
        # 页面显示用的摘要（保留HTML标签）
        final_summary_html = f"{seo_intro}<br/><br/>{original_summary}"
        
        # Meta 标签用的纯文本摘要
        meta_description = clean_html_tags(f"{seo_intro} {original_summary}")[:160] + "..."

        # --- 2. 构造 SEO 头部标签 (SEO Injection) ---
        filename = item.get('filename', f"symbol-{count}.html")
        full_url = f"{DOMAIN}/dreams/{filename}"
        
        seo_tags = f"""
    <!-- Auto-Injected SEO Tags -->
    <meta name="description" content="{meta_description}">
    <meta name="keywords" content="梦见{name}, {name}解梦, {name}象征意义, 周公解梦{name}, 心理学解梦">
    <link rel="canonical" href="{full_url}">
    <meta property="og:title" content="{seo_title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="{full_url}">
    <meta property="og:type" content="article">
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{seo_title}",
      "description": "{meta_description}",
      "mainEntityOfPage": {{
        "@type": "WebPage",
        "@id": "{full_url}"
      }},
      "author": {{
        "@type": "Organization",
        "name": "DreamWhisper"
      }}
    }}
    </script>
        """

        # --- 3. 执行替换 ---
        
        # 3.1 注入 SEO 标签到 </head> 之前
        if '</head>' in html:
            html = html.replace('</head>', f"{seo_tags}\n</head>")
        
        # 3.2 替换 Title
        if '<title>' in html:
            target_str = "象征字典 - {{ZH_NAME}} ({{EN_NAME}})"
            if target_str in html:
                html = html.replace(target_str, seo_title)
            else:
                html = html.replace('<title>', f'<title>{seo_title} | ')
        
        # 3.3 替换正文内容
        html = html.replace('{{ZH_NAME}}', name)
        html = html.replace('{{ZH_SUBNAME}}', zh_data.get('subname', ''))
        html = html.replace('{{ZH_SUMMARY}}', final_summary_html) # 注意这里用带HTML的
        html = html.replace('{{ZH_PSYCH_1}}', zh_data.get('psych_1', ''))
        html = html.replace('{{ZH_PSYCH_2}}', zh_data.get('psych_2', ''))
        html = html.replace('{{ZH_TRAD_GOOD}}', zh_data.get('trad_good', ''))
        html = html.replace('{{ZH_TRAD_BAD}}', zh_data.get('trad_bad', ''))
        
        # 3.4 数据注入
        json_str = json.dumps(item, ensure_ascii=False)
        html = html.replace('"REPLACE_ME_WITH_JSON"', json_str)
        html = html.replace("'REPLACE_ME_WITH_JSON'", json_str)

        # --- 4. 写入文件 ---
        path = os.path.join(DREAMS_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        count += 1

    print(f"成功生成 {count} 个详情页面 (SEO全量增强版) 到 {DREAMS_DIR}")

def generate_index_page(data):
    sorted_data = sorted(data, key=lambda x: len(x['zh']['name']))
    links_html = ""
    for item in sorted_data:
        name = item['zh']['name']
        filename = item['filename']
        links_html += f'<li><a href="dreams/{filename}">{name}</a></li>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>解梦百科全书 - 索引</title>
    <meta name="description" content="DreamWhisper 解梦百科全书，收录超过 {len(data)} 个常见梦境意象的心理学解析与传统周公解梦对照。">
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f7fa; }}
        h1 {{ text-align: center; color: #2c3e50; }}
        .search-box {{ text-align: center; margin-bottom: 30px; }}
        input {{ padding: 10px 20px; width: 80%; max-width: 400px; border-radius: 20px; border: 1px solid #ddd; font-size: 16px; }}
        ul {{ list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }}
        li a {{ display: block; padding: 10px 20px; background: white; text-decoration: none; color: #333; border-radius: 8px; transition: 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        li a:hover {{ background: #3498db; color: white; transform: translateY(-2px); }}
    </style>
</head>
<body>
    <h1>😴 解梦百科索引 ({len(data)})</h1>
    <div class="search-box">
        <input type="text" id="search" placeholder="搜索关键词..." onkeyup="filter()">
    </div>
    <ul id="list">
        {links_html}
    </ul>
    <script>
        function filter() {{
            var input = document.getElementById('search');
            var filter = input.value.toUpperCase();
            var ul = document.getElementById("list");
            var li = ul.getElementsByTagName('li');
            for (var i = 0; i < li.length; i++) {{
                var a = li[i].getElementsByTagName("a")[0];
                if (a.innerHTML.toUpperCase().indexOf(filter) > -1) {{
                    li[i].style.display = "";
                }} else {{
                    li[i].style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>"""
    
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"索引页已生成: {os.path.join(OUTPUT_DIR, 'index.html')}")

def generate_sitemap(data):
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    today = datetime.date.today().isoformat()
    sitemap_content += f"  <url><loc>{DOMAIN}/index.html</loc><lastmod>{today}</lastmod></url>\n"
    for item in data:
        sitemap_content += f"  <url><loc>{DOMAIN}/dreams/{item['filename']}</loc><priority>0.8</priority></url>\n"
    sitemap_content += '</urlset>'
    with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    print(f"Sitemap 已生成")

def main():
    print("=== 开始构建网站 (Final SEO Version) ===")
    data = load_data()
    if not data: return

    # 清理旧目录
    en_dir = os.path.join(OUTPUT_DIR, 'en')
    if os.path.exists(en_dir):
        shutil.rmtree(en_dir)

    build_detail_pages(data)
    generate_index_page(data)
    generate_sitemap(data)
    print("\n=== 构建完成！现在可以开始测试了。 ===")
    print("记得检查 HTML 源代码中的 <meta> 标签和 JSON-LD 数据。")

if __name__ == "__main__":
    main()