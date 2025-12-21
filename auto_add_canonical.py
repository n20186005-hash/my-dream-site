import os
import re

# 您的网站域名（请确保最后没有斜杠）
SITE_DOMAIN = "https:dreamwhisperai.com"

def process_html_files():
    # 获取当前脚本所在的目录作为根目录
    root_dir = os.getcwd()
    modified_count = 0
    
    print(f"正在扫描目录: {root_dir} ...")

    # 遍历所有文件夹和文件
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # 只处理 .html 文件
            if filename.endswith('.html'):
                file_path = os.path.join(dirpath, filename)
                
                # 计算相对路径，例如: /modules/math/calc.html
                rel_path = os.path.relpath(file_path, root_dir)
                # 将 Windows 的反斜杠 \ 替换为 /
                rel_path = rel_path.replace('\\', '/')
                
                # 跳过脚本自己可能产生的临时文件或 .git 文件夹
                if '.git' in rel_path or 'node_modules' in rel_path:
                    continue

                # 生成标准 URL
                if filename == 'index.html' and rel_path == 'index.html':
                    # 首页通常是 https://toolboxpro.top/
                    canonical_url = f"{SITE_DOMAIN}/"
                else:
                    # 其他页面是 https://toolboxpro.top/路径/文件名.html
                    # 确保路径以 / 开头
                    if not rel_path.startswith('/'):
                        rel_path = '/' + rel_path
                    canonical_url = f"{SITE_DOMAIN}{rel_path}"

                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 检查是否已经存在 canonical 标签，避免重复添加
                if 'rel="canonical"' in content:
                    print(f"跳过 (已存在): {rel_path}")
                    continue

                # 构造要插入的标签
                tag = f'\n    <!-- SEO Canonical Tag -->\n    <link rel="canonical" href="{canonical_url}" />'

                # 寻找插入位置：在 <head> 之后，或者 <title> 之后
                # 优先插在 <title>... </title> 后面，比较整齐
                if '</title>' in content:
                    new_content = content.replace('</title>', '</title>' + tag, 1)
                elif '<head>' in content:
                    new_content = content.replace('<head>', '<head>' + tag, 1)
                else:
                    print(f"跳过 (找不到 head 标签): {rel_path}")
                    continue

                # 写入修改后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"已修改: {rel_path} -> {canonical_url}")
                modified_count += 1

    print(f"\n完成！共修改了 {modified_count} 个文件。")
    print("请检查几个文件确认无误后，提交(git push)到 GitHub。")

if __name__ == "__main__":
    process_html_files()