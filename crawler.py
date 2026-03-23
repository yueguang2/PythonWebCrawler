import requests
from bs4 import BeautifulSoup
import time

class WebCrawler:
    def __init__(self, base_url, keywords, max_pages=10, task_id=None, logs=None):
        self.base_url = base_url
        self.keywords = keywords if isinstance(keywords, list) else [keywords]
        self.max_pages = max_pages
        self.task_id = task_id
        self.logs = logs
        self.visited_urls = set()
        self.results = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
    def log(self, message, level='info'):
        if self.logs and self.task_id:
            import time
            # 直接记录日志，不依赖应用上下文
            try:
                self.logs[self.task_id].append({"time": time.time(), "message": message, "level": level})
            except Exception as e:
                print(f"日志记录失败: {e}")

    def crawl(self, url):
        if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
            return

        self.visited_urls.add(url)
        self.log(f"正在爬取: {url}")

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title = soup.find('title').text if soup.find('title') else '无标题'
            content = soup.get_text()
            content_lower = content.lower()

            # 搜索多个关键词
            matched_keywords = []
            for keyword in self.keywords:
                if keyword.lower() in content_lower:
                    matched_keywords.append(keyword)

            # 如果有匹配的关键词，保存结果
            if matched_keywords:
                # 提取包含关键词的上下文
                contexts = []
                for keyword in matched_keywords:
                    start_idx = content_lower.find(keyword.lower())
                    if start_idx != -1:
                        start = max(0, start_idx - 100)
                        end = min(len(content), start_idx + len(keyword) + 100)
                        context = content[start:end]
                        contexts.append(f"关键词 '{keyword}' 的上下文: {context}")

                # 保存结果
                context_text = '\n\n'.join(contexts)
                self.results.append({
                    'url': url,
                    'title': title,
                    'context': context_text
                })
                self.log(f"在 {url} 中找到关键词: {', '.join(matched_keywords)}")

            # 提取所有链接
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    # 处理相对链接
                    if href.startswith('/'):
                        href = self.base_url + href
                    elif not href.startswith('http'):
                        href = self.base_url + '/' + href

                    # 只爬取同一域名的链接
                    if self.base_url in href:
                        # 检查链接是否可能是文章详情页
                        # 对于房地产网站，详情页通常包含数字ID或特定路径
                        if any(keyword in href.lower() for keyword in ['detail', 'info', 'id', 'item']) or href.endswith('.html'):
                            # 检查链接文本是否包含关键词
                            link_text = link.get_text().lower()
                            if any(keyword.lower() in link_text for keyword in self.keywords):
                                # 保存文章链接
                                self.results.append({
                                    'url': href,
                                    'title': link.get_text().strip(),
                                    'context': f"文章链接: {href}"
                                })
                                self.log(f"找到包含关键词的文章链接: {href}")
                        
                        # 继续爬取其他链接
                        self.crawl(href)

        except Exception as e:
            error_message = f"爬取 {url} 时出错: {e}"
            self.log(error_message, level='error')

        # 避免过快请求
        time.sleep(1)

    def start(self):
        keyword_str = ', '.join(self.keywords)
        self.log(f"开始爬取 {self.base_url}，搜索关键词: {keyword_str}")
        self.crawl(self.base_url)
        self.log(f"爬取完成，共找到 {len(self.results)} 个结果")
        return self.results