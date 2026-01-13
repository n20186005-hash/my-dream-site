import os
import re
from pathlib import Path

# -------------------------- 配置项 --------------------------
INPUT_DIR = "dream_pages"       # 待处理文件目录
OUTPUT_DIR = "processed_pages"  # 处理后文件输出目录
ENCODING = "utf-8"              # 文件编码（保持和原文件一致）

# 需要注入/替换的核心代码片段
# 1. 字体链接替换（新增繁体字体）
FONT_LINK_OLD = (
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Nunito:wght@300;400;600&display=swap" rel="stylesheet">'
)
FONT_LINK_NEW = (
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Noto+Serif+TC:wght@400;700&family=Nunito:wght@300;400;600&display=swap" rel="stylesheet">'
)

# 2. OG标签扩展（新增繁体locale）
OG_LOCALE_OLD = (
    '<meta property="og:locale" content="zh_CN">'
)
OG_LOCALE_NEW = (
    '<meta property="og:locale" content="zh_CN">\n    <meta property="og:locale:alternate" content="zh_TW">\n    <meta property="og:locale:alternate" content="en_US">'
)

# 3. 语言选择器替换（新增繁体选项）
LANG_SELECTOR_OLD = re.compile(
    r'<div class="relative group cursor-pointer z-50">[\s\S]*?</div></div>',
    re.MULTILINE
)
LANG_SELECTOR_NEW = '''<div class="relative group cursor-pointer z-50" id="languageSelector">
            <button class="flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 hover:bg-white/5 transition-all text-sm">
                <i class="fa-solid fa-globe text-green-300"></i>
                <span id="currentLang">中文</span>
                <i class="fa-solid fa-chevron-down text-xs opacity-70"></i>
            </button>
            <div class="absolute right-0 pt-2 hidden group-hover:block w-36">
                <div class="glass-panel rounded-xl overflow-hidden shadow-xl border-green-300/20 bg-[#0f172a]">
                    <button onclick="changeLanguage('zh')" class="block w-full text-left px-4 py-2 hover:bg-green-500/20 text-white transition-colors text-sm">简体中文</button>
                    <button onclick="changeLanguage('zh-tw')" class="block w-full text-left px-4 py-2 hover:bg-green-500/20 text-white transition-colors text-sm">繁體中文</button>
                    <button onclick="changeLanguage('en')" class="block w-full text-left px-4 py-2 hover:bg-green-500/20 text-white transition-colors text-sm">English</button>
                </div>
            </div>
        </div>'''

# 4. 核心翻译脚本（三语版本）
TRANSLATION_SCRIPT = '''
    <!-- SSR友好的JS加载策略 -->
    <script type="module">
        // 多语言翻译核心逻辑（批量生成版）
        const getTranslationData = () => {
            // 从页面元数据提取核心文本（保持原有内容）
            const pageTitle = document.title || '';
            const dreamKeyword = document.getElementById('symName')?.textContent || '';
            
            // 基础翻译模板（动态适配当前页面关键词）
            return {
                "zh": {
                    "name": dreamKeyword,
                    "subname": "解梦全解析",
                    "dream_guide_title": `想解读你的${dreamKeyword}梦境？`,
                    "dream_guide_desc": "前往首页，输入你的梦境细节，获取专属的心理学解梦分析",
                    "dream_btn": "立即解梦",
                    "more_dream_title": "还想了解更多梦境含义？",
                    "more_dream_desc": "首页提供更全面的梦境解析工具，定制专属解读",
                    "go_home_btn": "前往首页",
                    "back_dict": "返回首页",
                    "title_psych": "心理学视角",
                    "title_trad": "传统与文化解读",
                    "trad_good_label": "吉：",
                    "trad_bad_label": "凶："
                },
                "zh-tw": {
                    "name": convertToTraditional(dreamKeyword),
                    "subname": "解夢全解析",
                    "dream_guide_title": `想解讀你的${convertToTraditional(dreamKeyword)}夢境？`,
                    "dream_guide_desc": "前往首頁，輸入你的夢境細節，獲取專屬的心理學解夢分析",
                    "dream_btn": "立即解夢",
                    "more_dream_title": "還想了解更多夢境含義？",
                    "more_dream_desc": "首頁提供更全面的夢境解析工具，定制專屬解讀",
                    "go_home_btn": "前往首頁",
                    "back_dict": "返回首頁",
                    "title_psych": "心理學視角",
                    "title_trad": "傳統與文化解讀",
                    "trad_good_label": "吉：",
                    "trad_bad_label": "凶："
                },
                "en": {
                    "name": translateToEnglish(dreamKeyword),
                    "subname": "Complete Dream Interpretation",
                    "dream_guide_title": `Want to interpret your ${translateToEnglish(dreamKeyword)} dream?`,
                    "dream_guide_desc": "Go to the homepage, enter the details of your dream, and get exclusive psychological dream analysis",
                    "dream_btn": "Interpret Dream Now",
                    "more_dream_title": "Want to learn more about dream meanings?",
                    "more_dream_desc": "The homepage offers comprehensive dream interpretation tools for personalized analysis",
                    "go_home_btn": "Go to Homepage",
                    "back_dict": "Back Home",
                    "title_psych": "Psychological Perspective",
                    "title_trad": "Traditional & Cultural Interpretation",
                    "trad_good_label": "Good Omen:",
                    "trad_bad_label": "Bad Omen:"
                }
            };
        };

        // 简体转繁体（核心字库，可扩展）
        const convertToTraditional = (text) => {
            const charMap = {
                "门": "門", "梦": "夢", "进": "進", "发": "發", "体": "體",
                "会": "會", "适": "適", "应": "應", "优": "優", "华": "華",
                "罗": "羅", "荣": "榮", "权": "權", "护": "護", "儿": "兒",
                "万": "萬", "过": "過", "说": "說", "话": "話", "听": "聽",
                "觉": "覺", "宝": "寶", "贝": "貝", "长": "長", "头": "頭",
                "里": "裏", "后": "後", "面": "麵", "机": "機", "关": "關",
                "闭": "閉", "开": "開", "显": "顯", "现": "現", "阶": "階",
                "段": "段", "补": "補", "充": "充", "优": "優", "化": "化"
            };
            return text.split('').map(c => charMap[c] || c).join('');
        };

        // 中文关键词转英文（基础版，可根据实际需求扩展）
        const translateToEnglish = (text) => {
            const translateMap = {
                "舞台陷阱门": "Stage Trapdoor",
                "父母的": "Parents",
                "梦见": "Dreaming of",
                "心理学": "Psychology",
                "传统": "Traditional"
            };
            // 优先匹配完整短语，再按字匹配
            for (const [cn, en] of Object.entries(translateMap)) {
                text = text.replace(cn, en);
            }
            return text || "Dream Symbol";
        };

        // SSR Hydration逻辑
        document.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const langParam = urlParams.get('lang');
            if (langParam) changeLanguage(langParam);
            else initLanguage('zh'); // 默认简体中文
        });

        // 语言初始化函数
        function initLanguage(lang) {
            const validLangs = ['zh', 'zh-tw', 'en'];
            const targetLang = validLangs.includes(lang) ? lang : 'zh';
            
            updateUrlLangParam(targetLang);
            updatePageContent(targetLang);
            updatePageMeta(targetLang);
        }

        // URL参数更新
        function updateUrlLangParam(lang) {
            if (window.history && window.history.pushState) {
                const url = new URL(window.location);
                url.searchParams.set('lang', lang);
                window.history.pushState({}, '', url);
            }
        }

        // 页面内容更新
        function updatePageContent(lang) {
            const translationData = getTranslationData();
            const translations = translationData[lang];
            
            // 更新语言显示文本
            const langTextMap = { 
                'zh': '简体中文', 
                'zh-tw': '繁體中文', 
                'en': 'English' 
            };
            document.getElementById('currentLang').textContent = langTextMap[lang] || '简体中文';
            
            // 应用翻译内容
            if (translations) {
                document.querySelectorAll('[data-i18n]').forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    if (translations[key]) {
                        el.innerHTML = translations[key];
                    }
                });
            }
            
            // 更新页面语言属性和字体
            const langHtmlMap = { 'zh': 'zh-CN', 'zh-tw': 'zh-TW', 'en': 'en-US' };
            document.documentElement.lang = langHtmlMap[lang] || 'zh-CN';
            
            // 字体切换
            if (lang === 'zh-tw') {
                document.body.style.fontFamily = "'Noto Serif TC', 'Nunito', sans-serif";
            } else if (lang === 'zh') {
                document.body.style.fontFamily = "'Noto Serif SC', 'Nunito', sans-serif";
            } else {
                document.body.style.fontFamily = "'Nunito', sans-serif";
            }
        }

        // 页面元信息更新
        function updatePageMeta(lang) {
            const title = document.title || '';
            const titleMap = {
                'zh': title,
                'zh-tw': convertToTraditional(title),
                'en': `What Does Dreaming of ${translateToEnglish(document.getElementById('symName')?.textContent || '')} Mean? Full Analysis`
            };
            
            document.title = titleMap[lang] || titleMap.zh;
            
            // 更新OG标签
            const ogTitle = document.querySelector('meta[property="og:title"]');
            if (ogTitle) ogTitle.setAttribute('content', document.title);
            
            const ogLocale = document.querySelector('meta[property="og:locale"]');
            if (ogLocale) {
                const localeMap = { 'zh': 'zh_CN', 'zh-tw': 'zh_TW', 'en': 'en_US' };
                ogLocale.setAttribute('content', localeMap[lang] || 'zh_CN');
            }
        }

        // 全局语言切换函数
        window.changeLanguage = function(lang) {
            initLanguage(lang);
        };

        // 交互增强
        function enhanceInteractivity() {
            // 语言选择器交互
            document.getElementById('languageSelector')?.addEventListener('click', (e) => {
                const dropdown = e.currentTarget.querySelector('.absolute');
                if (dropdown) dropdown.classList.toggle('hidden');
            });
            
            // 点击外部关闭下拉菜单
            document.addEventListener('click', (e) => {
                const selector = document.getElementById('languageSelector');
                if (selector && !selector.contains(e.target)) {
                    const dropdown = selector.querySelector('.absolute');
                    if (dropdown) dropdown.classList.add('hidden');
                }
            });
        }
        
        // 初始化交互
        enhanceInteractivity();
    </script>
    
    <!-- 无JS降级处理 -->
    <noscript>
        <style>
            #languageSelector .absolute { display: none !important; }
            .dream-btn { pointer-events: auto; cursor: pointer; }
        </style>
        <meta name="robots" content="index, follow">
    </noscript>
'''

# -------------------------- 核心处理逻辑 --------------------------
def process_html_file(file_path, output_path):
    """处理单个HTML文件"""
    try:
        # 读取原文件
        with open(file_path, 'r', encoding=ENCODING) as f:
            content = f.read()
        
        # 1. 替换字体链接
        content = content.replace(FONT_LINK_OLD, FONT_LINK_NEW)
        
        # 2. 扩展OG locale标签
        if OG_LOCALE_OLD in content:
            content = content.replace(OG_LOCALE_OLD, OG_LOCALE_NEW)
        else:
            # 如果没有原有标签，插入到合适位置
            content = content.replace(
                '<meta property="og:type" content="article">',
                '<meta property="og:type" content="article">\n    ' + OG_LOCALE_NEW
            )
        
        # 3. 替换语言选择器
        content = LANG_SELECTOR_OLD.sub(LANG_SELECTOR_NEW, content)
        
        # 4. 注入解梦引导模块（如果不存在）
        guide_module = '''
        <!-- 新增：解梦引导模块 -->
        <div class="glass-panel rounded-2xl p-6 mb-8 border-2 border-green-500/40 bg-gradient-to-r from-green-900/20 to-emerald-800/10 text-center">
            <h3 class="text-xl font-serif font-bold mb-3 text-green-300" data-i18n="dream_guide_title">想解读你的梦境？</h3>
            <p class="text-gray-300 mb-4" data-i18n="dream_guide_desc">前往首页，输入你的梦境细节，获取专属的心理学解梦分析</p>
            <a href="https://dreamwhisperai.com" target="_blank" rel="noopener noreferrer" class="dream-btn inline-block px-8 py-3 bg-green-600/80 hover:bg-green-500 rounded-full text-white font-medium shadow-lg shadow-green-900/30">
                <i class="fa-solid fa-moon mr-2"></i><span data-i18n="dream_btn">立即解梦</span>
            </a>
        </div>'''
        
        if '<!-- 新增：解梦引导模块 -->' not in content:
            # 插入到Symbol Header之后
            content = content.replace(
                '</div>\n\n        <!-- Summary -->',
                '</div>' + guide_module + '\n\n        <!-- Summary -->'
            )
        
        # 5. 注入底部引导模块（如果不存在）
        bottom_guide = '''
        <!-- 新增：底部再次引导解梦模块 -->
        <div class="glass-panel rounded-2xl p-6 bg-black/10 border border-purple-500/20">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
                <div>
                    <h4 class="text-lg font-serif font-bold text-purple-300" data-i18n="more_dream_title">还想了解更多梦境含义？</h4>
                    <p class="text-gray-400 text-sm mt-1" data-i18n="more_dream_desc">首页提供更全面的梦境解析工具</p>
                </div>
                <a href="https://dreamwhisperai.com" target="_blank" rel="noopener noreferrer" class="dream-btn px-6 py-2 bg-purple-600/80 hover:bg-purple-500 rounded-lg text-white font-medium">
                    <i class="fa-solid fa-house-chimney mr-1"></i><span data-i18n="go_home_btn">前往首页</span>
                </a>
            </div>
        </div>'''
        
        if '<!-- 新增：底部再次引导解梦模块 -->' not in content:
            # 插入到Traditional部分之后
            content = content.replace(
                '</ul>\n            </div>\n        </div>',
                '</ul>\n            </div>\n        </div>' + bottom_guide
            )
        
        # 6. 替换原有脚本为新的多语言脚本
        # 先移除原有script（匹配pageData相关的脚本）
        content = re.sub(
            r'<script>[\s\S]*?pageData[\s\S]*?</script>',
            '',
            content
        )
        
        # 注入新的多语言脚本（插入到</main>之后）
        content = content.replace(
            '</main>',
            '</main>' + TRANSLATION_SCRIPT
        )
        
        # 7. 为所有需要翻译的元素添加data-i18n属性（如果未添加）
        # 匹配h1#symName
        content = re.sub(
            r'<h1 class="text-4xl font-serif font-bold mb-1" id="symName">([\s\S]*?)</h1>',
            r'<h1 class="text-4xl font-serif font-bold mb-1" id="symName" data-i18n="name">\1</h1>',
            content
        )
        
        # 匹配副标题p
        content = re.sub(
            r'<p class="text-lg text-gray-400 font-serif italic">([\s\S]*?)</p>',
            r'<p class="text-lg text-gray-400 font-serif italic" data-i18n="subname">\1</p>',
            content
        )
        
        # 8. 优化链接为新标签页跳转
        content = content.replace(
            'href="index.html"',
            'href="https://dreamwhisperai.com" target="_blank" rel="noopener noreferrer"'
        )
        
        # 9. 添加dream-btn样式（如果不存在）
        if '.dream-btn {' not in content:
            style_addition = '''
        .dream-btn { transition: all 0.3s ease; }
        .dream-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(74, 222, 128, 0.2); }'''
            content = content.replace(
                '</style>',
                style_addition + '\n    </style>'
            )
        
        # 保存处理后的文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding=ENCODING) as f:
            f.write(content)
        
        return True, f"处理成功: {file_path}"
    
    except Exception as e:
        return False, f"处理失败 {file_path}: {str(e)}"

def batch_process():
    """批量处理所有文件"""
    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # 遍历所有HTML文件
    success_count = 0
    fail_count = 0
    failed_files = []
    
    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith('.html'):
                # 构建输入输出路径
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_path, INPUT_DIR)
                output_path = os.path.join(OUTPUT_DIR, relative_path)
                
                # 处理单个文件
                success, msg = process_html_file(input_path, output_path)
                print(msg)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    failed_files.append(msg)
    
    # 输出统计结果
    print("\n=== 批量处理完成 ===")
    print(f"成功处理: {success_count} 个文件")
    print(f"处理失败: {fail_count} 个文件")
    
    if failed_files:
        print("\n失败文件列表:")
        for fail in failed_files:
            print(f"- {fail}")

# 执行批量处理
if __name__ == "__main__":
    batch_process()