const fs = require('fs');
const path = require('path');

const DOMAIN = 'https://dreamwhisperai.com';
const ROOT_DIR = './'; // 你的网页文件所在目录

function getFiles(dir, allFiles = []) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const name = path.join(dir, file);
    if (fs.statSync(name).isDirectory()) {
      if (file !== 'node_modules' && file !== '.git') getFiles(name, allFiles);
    } else if (file.endsWith('.html')) {
      allFiles.push(name);
    }
  });
  return allFiles;
}

const htmlFiles = getFiles(ROOT_DIR);
const sitemapContent = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${htmlFiles.map(file => {
    const urlPath = file.replace(/\\/g, '/').replace('index.html', '');
    return `
    <url>
      <loc>${DOMAIN}/${urlPath}</loc>
      <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
      <priority>0.8</priority>
    </url>`;
  }).join('')}
</urlset>`;

fs.writeFileSync('sitemap.xml', sitemapContent);
console.log('Sitemap 已生成！');