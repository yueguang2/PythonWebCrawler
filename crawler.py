import requests
from bs4 import BeautifulSoup
import time
from models import db, Result
from app import app

class WebCrawler:
    def __init__(self, base_url, keyword, max_pages=10, task_id=None):
        self.base_url = base_url
        self.keyword = keyword
        self.max_pages = max_pages
        self.task_id = task_id
        self.visited_urls = set()
        self.results = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def crawl(self, url):
        if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
            return

        self.visited_urls.add(url)
        print(f"正在爬取: {url}")

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 搜索关键词
            if self.keyword.lower() in response.text.lower():
                # 提取标题和摘要
                title = soup.find('title').text if soup.find('title') else '无标题'
                # 提取包含关键词的上下文
                content = soup.get_text()
                start_idx = content.lower().find(self.keyword.lower())
                if start_idx != -1:
                    start = max(0, start_idx - 100)
                    end = min(len(content), start_idx + len(self.keyword) + 100)
                    context = content[start:end]
                    
                    # 保存结果到数据库
                    if self.task_id:
                        with app.app_context():
                            result = Result(
                                task_id=self.task_id,
                                url=url,
                                title=title,
                                context=context
                            )
                            db.session.add(result)
                            db.session.commit()
                    
                    self.results.append({
                        'url': url,
                        'title': title,
                        'context': context
                    })

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
                        self.crawl(href)

        except Exception as e:
            print(f"爬取 {url} 时出错: {e}")

        # 避免过快请求
        time.sleep(1)

    def start(self):
        print(f"开始爬取 {self.base_url}，搜索关键词: {self.keyword}")
        self.crawl(self.base_url)
        print(f"爬取完成，共找到 {len(self.results)} 个包含关键词 '{self.keyword}' 的页面")
        return self.results