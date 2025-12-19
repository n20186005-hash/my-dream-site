import sys
import os

# 强制刷新输出，确保你能看到打印内容
sys.stdout.reconfigure(encoding='utf-8')

print("Script is starting... (脚本启动中)", flush=True)

# ================= 配置区 =================

# ⚠️ 安全开关：
# True  = 预演模式 (只看不改)
# False = 实战模式 (真正修改)
DRY_RUN = False 

# 🎯 目标文件夹
# 确保这个路径相对于脚本是存在的
TARGET_FOLDER = 'public/dreams'

# 你的 Google AdSense 代码
AD_CODE = """<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9279583389810634"
     crossorigin="anonymous"></script>"""

# 扫描后缀
TARGET_EXTENSIONS = ['.html', '.htm']

# ==========================================

def insert_ad_code(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 检查是否已有广告
        if "ca-pub-9279583389810634" in content:
            return False

        # 2. 寻找 </head> 标签
        if "</head>" in content:
            if DRY_RUN:
                print(f"[预演] 发现目标: {filepath}", flush=True)
                return True
            else:
                new_content = content.replace("</head>", f"{AD_CODE}\n</head>")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[成功] 已添加广告: {filepath}", flush=True)
                return True
        else:
            print(f"[跳过] 没找到head标签: {filepath}", flush=True)
            return False

    except Exception as e:
        print(f"[错误] 读写失败 {filepath}: {e}", flush=True)
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, TARGET_FOLDER)

    print(f"正在寻找文件夹: {base_dir}", flush=True)

    if not os.path.exists(base_dir):
        print(f"\n❌ 错误：找不到文件夹！", flush=True)
        print(f"请检查路径是否正确: {base_dir}", flush=True)
        return

    
    if DRY_RUN:
        print("\n--- 🛡️ 安全预演模式 (不会修改文件) ---", flush=True)
        print("如果是第一次运行，请先看是否有 '[预演] 发现目标' 的日志。", flush=True)
        print("确认无误后，请修改代码 DRY_RUN = False 再次运行。\n", flush=True)
    else:
        print("\n--- ⚡ 实战模式 (正在修改文件) ---", flush=True)
        print("正在处理...", flush=True)

    updated_count = 0
    scanned_count = 0

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                filepath = os.path.join(root, file)
                scanned_count += 1
                if insert_ad_code(filepath):
                    updated_count += 1
    
    print("-" * 30, flush=True)
    if DRY_RUN:
        print(f"预演结束。如果开启实战模式，将有 {updated_count} 个文件被修改。", flush=True)
    else:
        print(f"大功告成！一共修改了 {updated_count} 个文件。", flush=True)

if __name__ == "__main__":
    main()