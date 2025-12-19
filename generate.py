import json
import os

# 1. 读取 HTML 模板
# 在实际使用中，您应该读取您上传的 'symbol_detail.html'
# 这里为了演示，我们假设模板内容如下（基于您上传的文件简化）
template_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>象征字典 - {{ZH_NAME}} ({{EN_NAME}})</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Nunito:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); color: white; font-family: 'Nunito', sans-serif; min-height: 100vh; }
        .glass-panel { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
</head>
<body class="pb-20 flex flex-col min-h-screen">
    <!-- Navigation (Simplified) -->
    <nav class="w-full p-6 flex justify-between items-center bg-black/20 backdrop-blur-md sticky top-0 z-50 border-b border-white/5">
        <a href="index.html" class="flex items-center gap-2 hover:text-green-300 transition group">
            <span class="font-serif font-bold text-xl tracking-wide">DreamWhisper</span>
        </a>
    </nav>

    <main class="container mx-auto px-4 mt-8 max-w-3xl flex-grow">
        <div class="mb-4">
            <a href="index.html" class="text-green-300/70 hover:text-green-300 text-sm flex items-center gap-1 transition-colors w-fit">
                <i class="fa-solid fa-arrow-left"></i> <span>返回首页</span>
            </a>
        </div>

        <!-- Symbol Header -->
        <div class="text-center mb-8">
            <div class="w-20 h-20 mx-auto bg-green-500/20 rounded-2xl flex items-center justify-center border border-green-500/30 mb-4 shadow-xl shadow-green-900/20">
                <i class="fa-solid fa-star text-4xl text-green-400"></i>
            </div>
            <!-- KEYWORD: Main Title -->
            <h1 class="text-4xl font-serif font-bold mb-1" id="symName">{{ZH_NAME}}</h1>
            <p class="text-lg text-gray-400 font-serif italic">{{ZH_SUBNAME}}</p>
        </div>

        <!-- Summary -->
        <div class="glass-panel rounded-2xl p-5 text-center mb-8 border-t-2 border-green-500/50">
            <p class="text-base md:text-lg leading-relaxed text-green-50">
                {{ZH_SUMMARY}}
            </p>
        </div>

        <!-- Content -->
        <div class="space-y-8">
            <div class="glass-panel rounded-2xl p-8">
                <h2 class="text-2xl font-serif font-bold mb-4 flex items-center gap-3 text-purple-300">
                    <i class="fa-solid fa-brain"></i> 心理学视角
                </h2>
                <div class="space-y-4 text-gray-300 leading-relaxed">
                    <p>{{ZH_PSYCH_1}}</p>
                    <p>{{ZH_PSYCH_2}}</p>
                </div>
            </div>

            <div class="glass-panel rounded-2xl p-8">
                <h2 class="text-2xl font-serif font-bold mb-4 flex items-center gap-3 text-yellow-300">
                    <i class="fa-solid fa-scroll"></i> 传统与文化解读
                </h2>
                <ul class="space-y-3 text-gray-300">
                    <li class="flex gap-3"><span class="text-yellow-500 font-bold">吉：</span><span>{{ZH_TRAD_GOOD}}</span></li>
                    <li class="flex gap-3"><span class="text-red-400 font-bold">凶：</span><span>{{ZH_TRAD_BAD}}</span></li>
                </ul>
            </div>
        </div>
    </main>
    
    <!-- Injection Script for Translations -->
    <script>
        // We inject the specific data for this page here so the language switcher works
        const pageData = {{JSON_DATA}};
        
        const translations = {
            zh: pageData.zh,
            en: pageData.en
        };

        function changeLanguage(lang) {
            // Simple logic to swap content based on the 'translations' object
            if(lang === 'zh') {
                document.getElementById('symName').innerText = translations.zh.name;
                // ... add other mapping logic here ...
            } else {
                document.getElementById('symName').innerText = translations.en.name;
            }
        }
    </script>
</body>
</html>
"""

# 2. 读取数据
with open('symbols.json', 'r', encoding='utf-8') as f:
    symbols = json.load(f)

# 3. 循环生成
output_dir = "generated_pages"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for sym in symbols:
    # Replace placeholders with Chinese data (Default view)
    # 在实际项目中，可以使用更高级的模板引擎如 Jinja2
    content = template_html.replace('{{ZH_NAME}}', sym['zh']['name'])
    content = content.replace('{{EN_NAME}}', sym['en']['name'])
    content = content.replace('{{ZH_SUBNAME}}', sym['zh']['subname'])
    content = content.replace('{{ZH_SUMMARY}}', sym['zh']['summary'])
    content = content.replace('{{ZH_PSYCH_1}}', sym['zh']['psych_1'])
    content = content.replace('{{ZH_PSYCH_2}}', sym['zh']['psych_2'])
    content = content.replace('{{ZH_TRAD_GOOD}}', sym['zh']['trad_good'])
    content = content.replace('{{ZH_TRAD_BAD}}', sym['zh']['trad_bad'])
    
    # Inject the full JSON object into the script tag for dynamic switching
    content = content.replace('{{JSON_DATA}}', json.dumps(sym, ensure_ascii=False))

    # Write file
    filename = os.path.join(output_dir, sym['filename'])
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated: {filename}")

print("Batch generation complete!")