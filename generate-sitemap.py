import os
from datetime import datetime

# 配置
domain = "https://dreamwhisperai.com"
root_dir = "."  # 当前目录

def generate_sitemap():
    urls = []
    # 遍历当前目录及子目录
    for root, dirs, files in os.walk(root_dir):
        # 排除隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith(".html"):
                # 构建相对路径
                filepath = os.path.relpath(os.path.join(root, file), root_dir)
                # 将 Windows 路径符 \ 替换为 /
                url_path = filepath.replace(os.sep, '/')
                
                # 如果是 index.html，通常指向根路径
                if url_path == "index.html":
                    url_path = ""
                elif url_path.endswith("index.html"):
                    url_path = url_path.replace("index.html", "")

                full_url = f"{domain}/{url_path}".rstrip('/')
                urls.append(full_url)

    # 构建 XML 内容
    date_str = datetime.now().strftime("%Y-%m-%d")
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for url in urls:
        xml_lines.append(f'  <url>')
        xml_lines.append(f'    <loc>{url}</loc>')
        xml_lines.append(f'    <lastmod>{date_str}</lastmod>')
        xml_lines.append(f'    <priority>0.8</priority>')
        xml_lines.append(f'  </url>')

    xml_lines.append('</urlset>')

    # 写入文件
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    
    print(f"成功！已处理 {len(urls)} 个 HTML 文件，Sitemap 已生成。")

if __name__ == "__main__":
    generate_sitemap()