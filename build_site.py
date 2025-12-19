import json
import os
import datetime
import shutil
import random
import re

# ================= 配置区 =================

# 🚀 增量生成开关
# True  = 日常更新模式。跳过已存在的文件，只生成新的，且自动带上广告。
# False = 全站刷新模式。强制覆盖所有文件（如果你想给所有旧页面也加上广告，请改为 False 跑一次）。
SKIP_EXISTING = True 

DATA_FILE = 'symbols_updated.json'     # 数据源
TEMPLATE_FILE = 'symbol_template.html' # 模板文件
OUTPUT_DIR = 'public'
DREAMS_DIR = os.path.join(OUTPUT_DIR, 'dreams')
DOMAIN = "https://dreamwhisperai.com" 

# 💰 Google AdSense 广告代码
AD_CODE = """<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9279583389810634"
     crossorigin="anonymous"></script>"""

# ================= SEO 文案库 =================
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
    "心理学家荣格认为，梦中的<strong>{name}</strong>折射出了你内心的某种渴望。",
    "当你醒来记得自己梦见了<strong>{name}</strong>，说明你的潜意识正在试图告诉你一些重要信息。"
]

def load_template():
    if not os.path.exists(TEMPLATE_FILE):
        print(f"❌ 错误：找不到模板文件 {TEMPLATE_FILE}")
        return None
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_page(item, template, existing_files):
    filename = item.get('filename')
    if not filename:
        return False
        
    filepath = os.path.join(DREAMS_DIR, filename)

    # ⚡ 检查文件是否存在 (增量逻辑)
    if SKIP_EXISTING and filename in existing_files:
        return "skipped"

    # --- 数据准备 ---
    zh_data = item.get('zh', {})
    en_data = item.get('en', {})
    name_zh = zh_data.get('name', '')
    
    # 随机选择 SEO 文案
    seo_title = random.choice(SEO_TITLES_ZH).format(name=name_zh)
    seo_intro = random.choice(INTRO_TEMPLATES_ZH).format(name=name_zh)

    # 构建页面数据
    page_data = {
        "zh": zh_data,
        "en": en_data,
        "seo_title": seo_title,
        "seo_intro": seo_intro
    }
    json_data = json.dumps(page_data, ensure_ascii=False)

    content = template
    # 1. 基础替换
    content = content.replace('{{ZH_NAME}}', name_zh)
    content = content.replace('{{EN_NAME}}', en_data.get('name', ''))
    
    # 2. 注入数据到 JS
    script_inject = f"<script>var pageData = {json_data};</script>"
    content = content.replace('</body>', f'{script_inject}\n</body>')
    
    # 3. SEO Title 替换
    content = content.replace('<title>象征字典', f'<title>{seo_title}')

    # 🔥 4. 自动植入广告代码
    if "ca-pub-9279583389810634" not in content:
        content = content.replace('</head>', f'{AD_CODE}\n</head>')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return "generated"

def generate_index_page(data):
    """ 生成索引页 index.html (已恢复完整逻辑) """
    print("📄 正在生成索引页 (index.html)...")
    
    # 构建列表项 HTML
    list_items = ""
    for item in data:
        filename = item.get('filename')
        name_zh = item.get('zh', {}).get('name', '未知')
        if filename:
            list_items += f'<li><a href="dreams/{filename}" class="block p-3 bg-white/5 hover:bg-white/10 rounded-lg transition">{name_zh}</a></li>\n'

    # 完整的 Index HTML 模板
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>梦境象征索引 - DreamWhisper</title>
    {AD_CODE}
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); color: white; min-height: 100vh; }}
    </style>
</head>
<body class="p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-8 text-center">梦境词典索引 ({len(data)}条)</h1>
        
        <input type="text" id="searchInput" onkeyup="filterList()" placeholder="搜索梦境..." class="w-full p-4 rounded-xl bg-white/10 border border-white/20 mb-8 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500">
        
        <ul id="symbolList" class="grid grid-cols-2 md:grid-cols-3 gap-4">
            {list_items}
        </ul>
    </div>

    <script>
        function filterList() {{
            var input, filter, ul, li, a, i, txtValue;
            input = document.getElementById('searchInput');
            filter = input.value.toUpperCase();
            ul = document.getElementById("symbolList");
            li = ul.getElementsByTagName('li');

            for (i = 0; i < li.length; i++) {{
                a = li[i].getElementsByTagName("a")[0];
                txtValue = a.textContent || a.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                    li[i].style.display = "";
                }} else {{
                    li[i].style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>"""
    
    index_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 索引页已生成: {index_path}")

def generate_sitemap(data):
    """ 自动生成 Sitemap """
    sitemap_path = os.path.join(OUTPUT_DIR, 'sitemap.xml')
    print(f"🗺️  正在刷新 Sitemap: {sitemap_path}")
    
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    today = datetime.date.today().isoformat()
    
    # 固定页面
    sitemap_content += f"  <url><loc>{DOMAIN}/index.html</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>\n"
    sitemap_content += f"  <url><loc>{DOMAIN}/dream-plaza.html</loc><lastmod>{today}</lastmod><priority>0.9</priority></url>\n"
    
    # 动态生成的页面
    for item in data:
        filename = item.get('filename')
        if filename:
            sitemap_content += f"  <url><loc>{DOMAIN}/dreams/{filename}</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>\n"
            
    sitemap_content += '</urlset>'
    
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

def main():
    print("=== 全自动网站构建系统启动 ===")
    
    if SKIP_EXISTING:
        print("🚀 模式：增量构建 (只生成新页面，自动带广告)")
    else:
        print("🔥 模式：全量覆盖 (重写所有页面，确保所有页面都有广告)")

    ensure_dir(OUTPUT_DIR)
    ensure_dir(DREAMS_DIR)

    if not os.path.exists(DATA_FILE):
        print(f"❌ 找不到数据文件 {DATA_FILE}")
        return
        
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📚 加载了 {len(data)} 条数据")

    template = load_template()
    if not template:
        return

    # 获取已存在文件
    existing_files = set()
    if os.path.exists(DREAMS_DIR):
        existing_files = set(os.listdir(DREAMS_DIR))

    # 生成页面
    count_new = 0
    count_skip = 0
    
    for item in data:
        status = generate_page(item, template, existing_files)
        if status == "generated":
            count_new += 1
            if count_new % 100 == 0:
                print(f"   已生成 {count_new} 个新页面...")
        elif status == "skipped":
            count_skip += 1
            
    print(f"\n✅ 页面构建完成")
    print(f"   - 新增(带广告): {count_new}")
    print(f"   - 跳过(旧文件): {count_skip}")

    # 生成索引页 (这一步非常重要，包含了搜索功能)
    generate_index_page(data)

    # 生成地图 (每次都跑，确保地图是最新的)
    generate_sitemap(data)
    print("🎉 所有任务全部完成！")

if __name__ == "__main__":
    main()