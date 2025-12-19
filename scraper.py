import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
import hashlib
from urllib.parse import urljoin, unquote, quote

# --- 配置 ---
OUTPUT_FILE = 'symbols_updated.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

# --- 1. 强力黑名单 (过滤无效词/品牌词/导航词/乱码) ---
BLACKLIST_KEYWORDS = [
    "Dream Interpreter AI", "Dream Interpreter", "DreamMoods", "Psychologist World",
    "Verywell Mind", "Dream Dictionary", "Baddream Dictionary", "DreamyBot",
    "Home", "Menu", "Search", "Account", "Login", "Sign Up", "About Us",
    "Terms", "Privacy", "Contact", "Blog", "Sitemap", "Dictionary",
    "Previous", "Next", "查看更多", "首页", "解梦", "查询", "八字", "算命",
    "English", "Español", "Français", "Deutsch", "Italiano", "Polski", "Português",
    "User", "Profile", "Logout", "All Dreams", "A-Z", "Categories",
    "周公解梦", "解梦大全", "梦境解析",
    "開始", "語言", "繁體", "简体", "Language", "Settings", "App Store", "Google Play",
    "Download", "Mobile", "View", "Read More", "Source", "Author",
    "%", "language", "start" 
]

# --- 目标源列表 (你提供的网站) ---
ENGLISH_SOURCES = [
    "https://www.dreamly-app.com/dream/",
    "https://dreamybot.com/",
    "https://www.dreammoods.com/",
    "https://baddreamdictionary.com/",
    "https://www.dreamdictionary.org/",
    "https://www.psychologistworld.com/dreams/dictionary/",
    "https://www.verywellmind.com/dream-interpretation-what-do-dreams-mean-2795930",
    "https://www.dreams.co.uk/sleep-matters-club/dream-encyclopaedia"
]

CHINESE_SOURCES = [
    "https://tools.2345.com/m/zhgjm.htm",
    "https://www.mxyn.com/",
    "https://www.ibazi.cn/jiemeng/"
]

def clean_text(text):
    """基础文本清理"""
    if not text: return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def debrand_content(text):
    """去品牌化：移除原网站的名称和痕迹"""
    if not text: return ""
    brands = [
        "Dream Interpreter AI", "DreamInterpreter.ai", "周公解梦大全查询", "2345",
        "DreamMoods", "Psychologist World", "Verywell", "Dream Dictionary",
        "DreamyBot", "第一星座", "爱八字"
    ]
    for brand in brands:
        text = text.replace(brand, "")
    # 移除常见的来源标注
    text = re.sub(r'(Source|来源|From|Author|By)[:：].*?(\s|$)', '', text, flags=re.IGNORECASE)
    return text.strip()

def generate_seo_filename(keyword):
    """生成 SEO 友好的文件名"""
    # 移除非法字符，只保留中英文数字
    clean_key = re.sub(r'[^\w\u4e00-\u9fa5]', '', keyword)
    if not clean_key:
        return f"symbol-{random.randint(10000,99999)}.html"
    return f"{clean_key}.html"

# ==========================================
# PART 1: 关键词发现 (Crawler)
# ==========================================

def crawl_generic_sites(urls, lang='en'):
    """通用的链接发现器"""
    discovered = []
    print(f"正在扫描 {len(urls)} 个{lang}源网站...")
    
    for index_url in urls:
        print(f"  -> 正在抓取索引: {index_url} ...")
        try:
            # 针对不同站点可能需要微调编码
            response = requests.get(index_url, headers=HEADERS, timeout=15)
            
            # 尝试自动检测编码 (尤其是中文站)
            if lang == 'zh':
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有链接
            links = soup.find_all('a', href=True)
            
            count_found = 0
            for link in links:
                text = clean_text(link.get_text())
                href = link.get('href')
                full_url = urljoin(index_url, href)
                
                # 1. 基础长度过滤
                if not text or len(text) < 2 or len(text) > 30: continue
                
                # 2. 特殊字符过滤 (针对你遇到的 %开始... 问题)
                if text.startswith('%') or text.startswith('#') or 'http' in text: continue
                
                # 3. 黑名单过滤
                if any(b.lower() in text.lower() for b in BLACKLIST_KEYWORDS): continue
                
                # 针对特定网站的路径过滤 (提高准确率)
                is_valid = False
                
                # DreamInterpreter 特殊处理
                if "dreaminterpreter.ai" in index_url and "/definition/" in href:
                    is_valid = True
                # English Dictionaries (通常包含 dictionary, meaning, dream, encyclopedia)
                elif lang == 'en':
                    if any(k in href.lower() for k in ['/dream/', '/dictionary/', '/meaning/', '/symbol/', 'encyclopaedia']):
                        is_valid = True
                    # Verywellmind 特殊处理 (文章页可能链接到其他文章)
                    elif "verywellmind" in index_url and ".htm" in href:
                        is_valid = True
                        
                # Chinese Sites (通常包含 jiemeng, meng, htm)
                elif lang == 'zh':
                    if any(k in href.lower() for k in ['jiemeng', 'meng', '.htm', 'show']):
                        is_valid = True

                if is_valid:
                    # 再次清洗关键词 (去掉 "梦见", "梦到" 等前缀，使关键词更纯粹)
                    clean_key = re.sub(r'^(梦见|梦到|梦|About )', '', text)
                    if clean_key and len(clean_key) > 1:
                        # 二次检查 clean_key 是否在黑名单
                        if any(b.lower() in clean_key.lower() for b in BLACKLIST_KEYWORDS): continue
                        
                        discovered.append({
                            "keyword": clean_key,
                            "source": "generic_" + lang,
                            "url": full_url,
                            "original_text": text
                        })
                        count_found += 1
            
            print(f"     发现 {count_found} 个潜在词条")
            time.sleep(1) # 礼貌爬取
            
        except Exception as e:
            print(f"     抓取失败 {index_url}: {e}")
            
    return discovered

def crawl_keywords_from_dreaminterpreter():
    # 保留原有的专用抓取函数，因为它结构比较特殊且质量高
    index_url = "https://dreaminterpreter.ai/zh-tw/dream-dictionary"
    print(f"正在发现关键词 (DreamInterpreter)...")
    discovered = []
    try:
        response = requests.get(index_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/definition/'))
        for link in links:
            text = clean_text(link.get_text())
            href = link.get('href')
            url_keyword = ""
            if href:
                parts = href.split('/')
                if parts: url_keyword = unquote(parts[-1]).replace('-', ' ')
            
            # 优先使用 URL 里的词，因为它通常更干净
            final_keyword = url_keyword if url_keyword else text
            final_keyword = clean_text(final_keyword)
            
            if final_keyword and len(final_keyword) > 1:
                # 过滤逻辑
                if final_keyword.startswith('%') or final_keyword.startswith('#'): continue
                if any(b.lower() in final_keyword.lower() for b in BLACKLIST_KEYWORDS): continue
                
                full_url = urljoin(index_url, href)
                discovered.append({"keyword": final_keyword, "source": "dreaminterpreter", "url": full_url})
    except Exception as e:
        print(f"爬取 DreamInterpreter 失败: {e}")
    return discovered

# ==========================================
# PART 2: 内容提取 (Extractors)
# ==========================================

def extract_dreaminterpreter(keyword):
    # 专用提取器
    url = f"https://dreaminterpreter.ai/zh-tw/dream-dictionary/definition/{quote(keyword)}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = keyword
        h1 = soup.find('h1')
        if h1: 
            page_title = clean_text(h1.get_text())
            if not any(b in page_title for b in BLACKLIST_KEYWORDS): title = page_title

        summary = ""
        paragraphs = soup.find_all('p')
        valid_paragraphs = [clean_text(p.get_text()) for p in paragraphs if len(p.get_text()) > 20]
        
        if valid_paragraphs:
            summary = "<br><br>".join(valid_paragraphs[:2])
        else:
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta: summary = meta['content']

        summary = debrand_content(summary)
        if not summary or len(summary) < 5: return None

        return {
            "name": title,
            "subname": keyword,
            "summary": summary,
            "psych_1": f"从心理学角度看，{keyword}通常象征潜意识中的某种投射。",
            "psych_2": "",
            "trad_good": f"梦见{keyword}，需结合梦境氛围判断吉凶。",
            "trad_bad": ""
        }
    except: return None

def extract_generic_chinese(url, keyword):
    """通用中文提取器 (适配 2345, mxyn, ibazi 等)"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = response.apparent_encoding # 自动识别 GBK/UTF-8
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title = keyword
        h1 = soup.find('h1')
        if h1: title = clean_text(h1.get_text())
        
        # 提取正文 (尝试常见的正文容器)
        content_div = soup.find('div', class_=re.compile(r'(content|detail|article|desc)'))
        if not content_div:
            content_div = soup.find('body') # 兜底
            
        paragraphs = content_div.find_all('p')
        valid_texts = []
        
        for p in paragraphs:
            text = clean_text(p.get_text())
            if len(text) > 15 and not any(b in text for b in BLACKLIST_KEYWORDS):
                valid_texts.append(text)
        
        if not valid_texts: return None
        
        # 智能分配段落
        summary = valid_texts[0]
        # 尝试寻找吉凶相关的段落
        good_luck = next((t for t in valid_texts if "吉" in t or "大吉" in t), "")
        bad_luck = next((t for t in valid_texts if "凶" in t or "忌" in t), "")
        psych = next((t for t in valid_texts if "心理" in t or "意味" in t), "")
        
        return {
            "name": title,
            "subname": "Chinese Interpretation",
            "summary": debrand_content(summary),
            "psych_1": debrand_content(psych) if psych else f"梦见{keyword}的心理学解析暂缺。",
            "psych_2": "",
            "trad_good": debrand_content(good_luck) if good_luck else "（吉凶需根据具体情节分析）",
            "trad_bad": debrand_content(bad_luck)
        }
    except Exception as e:
        # print(f"Chinese extract err: {e}")
        return None

def extract_generic_english(url, keyword):
    """通用英文提取器 (适配 DreamMoods, VeryWellMind 等)"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = keyword
        h1 = soup.find('h1')
        if h1: title = clean_text(h1.get_text())
        
        # 提取所有段落
        paragraphs = soup.find_all('p')
        valid_texts = []
        for p in paragraphs:
            text = clean_text(p.get_text())
            if len(text) > 30 and not any(b in text for b in BLACKLIST_KEYWORDS):
                valid_texts.append(text)
        
        if not valid_texts: return None
        
        # 英文内容通常较长，截取前几段作为摘要
        summary = "<br>".join(valid_texts[:3])
        
        return {
            "name": keyword, # 英文名
            "subname": title, # 英文原名
            "summary": debrand_content(summary),
            "psych_1": "Psychological interpretation available in summary.",
            "psych_2": "",
            "trad_good": "",
            "trad_bad": ""
        }
    except: return None

# ==========================================
# PART 3: 主流程 (含安全暂停)
# ==========================================

def main():
    print("=== 开始运行多源解梦爬虫 (按 Ctrl+C 可随时安全暂停) ===")
    print("支持源: DreamInterpreter, 2345, DreamMoods, VeryWellMind 等 12 个网站")
    
    # 1. 读取历史记录
    existing_data = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except: existing_data = []
    
    # 建立去重集合 (同时检查中文名和英文名/ID)
    existing_keys = set()
    for s in existing_data:
        existing_keys.add(s['zh']['name'])
        if 'id' in s: existing_keys.add(s['id'])

    print(f"检测到已有数据: {len(existing_data)} 条 (将自动跳过)")
    
    # 2. 发现任务 (聚合所有源)
    all_tasks = []
    
    # 2.1 DreamInterpreter (高质量源)
    all_tasks.extend(crawl_keywords_from_dreaminterpreter())
    
    # 2.2 中文源 (2345, mxyn, ibazi)
    all_tasks.extend(crawl_generic_sites(CHINESE_SOURCES, lang='zh'))
    
    # 2.3 英文源 (DreamMoods 等)
    all_tasks.extend(crawl_generic_sites(ENGLISH_SOURCES, lang='en'))
    
    # 去重任务
    unique_tasks_map = {}
    for t in all_tasks:
        if t['keyword'] not in existing_keys and t['keyword'] not in unique_tasks_map:
            unique_tasks_map[t['keyword']] = t
    
    unique_tasks = list(unique_tasks_map.values())
    random.shuffle(unique_tasks) # 打乱顺序，避免对同一个网站请求过于集中
    
    print(f"共发现 {len(unique_tasks)} 个新词条待处理。")
    
    new_count = 0
    total_new = 0
    
    # --- 核心：安全循环 ---
    try:
        for item in unique_tasks:
            keyword = item['keyword']
            url = item['url']
            source = item['source']
            
            print(f"[{total_new+1}/{len(unique_tasks)}] 处理: {keyword} ({source})...")
            
            zh_data = None
            en_data = None
            
            # --- 核心修复：数据分流 ---
            if source == 'dreaminterpreter':
                # 这个源主要是中文繁体/简体混合，算作中文数据
                zh_data = extract_dreaminterpreter(keyword)
                if zh_data:
                    en_data = {
                        "name": keyword, 
                        "subname": "Interpretation",
                        "summary": "Content available in Chinese.",
                        "psych_1": "...", "psych_2": "", "trad_good": "", "trad_bad": ""
                    }

            elif source == 'generic_zh':
                zh_data = extract_generic_chinese(url, keyword)
                if zh_data:
                    en_data = {
                        "name": keyword, 
                        "subname": "Chinese Source",
                        "summary": "This entry comes from a Chinese source.",
                        "psych_1": "...", "psych_2": "", "trad_good": "", "trad_bad": ""
                    }

            elif source == 'generic_en':
                # --- 修复英文内容错位 ---
                # 英文源的数据应该填入 en_data
                raw_en_data = extract_generic_english(url, keyword)
                if raw_en_data:
                    en_data = raw_en_data
                    # zh_data 做一个兜底，复制英文内容，并加上提示
                    # 这样在默认中文界面下，用户能看到英文原文，而不是空白或占位符
                    zh_data = raw_en_data.copy()
                    zh_data['summary'] = f"<strong>(此条目源自英文网站，暂未翻译)</strong><br><br>{raw_en_data['summary']}"
                    zh_data['name'] = keyword # 保持标题

            # 只要有一方有数据，就保存
            if zh_data and zh_data.get('summary'):
                filename = generate_seo_filename(keyword)
                safe_id = hashlib.md5(keyword.encode()).hexdigest()[:8]
                
                entry = {
                    "id": f"auto_{safe_id}_{keyword}",
                    "filename": filename,
                    "zh": zh_data, 
                    "en": en_data if en_data else zh_data, # 双重保险
                    "meta": { "source_url": url, "origin": source }
                }
                
                existing_data.append(entry)
                existing_keys.add(keyword)
                new_count += 1
                total_new += 1
                print(f"  -> 成功: {filename}")
            else:
                print(f"  -> 失败: 无法提取内容")
            
            time.sleep(random.uniform(1.0, 3.0))
            
            if new_count >= 10:
                print("--- 自动保存进度 ---")
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                new_count = 0

    except KeyboardInterrupt:
        print("\n\n>>> 检测到暂停指令 (Ctrl+C) <<<")
        print("正在紧急保存当前数据，请稍候...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        print("✅ 数据已安全保存。下次运行将从此处继续。")
        return

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n全部完成！本次新增 {total_new} 条数据。")

if __name__ == "__main__":
    main()