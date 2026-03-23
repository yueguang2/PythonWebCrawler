# Python Web Crawler 爬虫管理后台

一个基于Flask的Web爬虫管理后台，支持多关键词搜索、实时日志显示、任务管理等功能。

## 功能特性

- **多关键词支持**：可以同时搜索多个关键词，用逗号分隔
- **实时日志显示**：查看爬取过程中的详细日志
- **任务管理**：创建、启动、查看、删除、重新爬取任务
- **结果查看**：查看爬取到的详细结果，包括标题和链接
- **Docker部署**：支持使用Docker容器化部署

## 技术栈

- **后端**：Python 3.9 + Flask + SQLAlchemy
- **前端**：HTML + Bootstrap + jQuery
- **数据库**：SQLite
- **爬虫**：requests + BeautifulSoup4

## 安装与运行

### 方法1：直接运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/yueguang2/PythonWebCrawler.git
   cd PythonWebCrawler
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行应用**
   ```bash
   python app.py
   ```

4. **访问**
   打开浏览器访问：`http://localhost:5000`

### 方法2：使用Docker

1. **克隆仓库**
   ```bash
   git clone https://github.com/yueguang2/PythonWebCrawler.git
   cd PythonWebCrawler
   ```

2. **使用Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **访问**
   打开浏览器访问：`http://localhost:5000`

## 使用指南

### 创建爬取任务

1. 在首页的表单中填写以下信息：
   - **网站链接**：要爬取的网站URL（例如：https://example.com）
   - **搜索关键词**：要搜索的关键词，多个关键词用逗号分隔（例如：python,flask,crawler）
   - **日志级别**：选择日志详细程度（信息或调试）
   - **最大爬取页面数**：限制爬取的页面数量（默认10）

2. 点击"创建任务"按钮

### 启动爬取任务

1. 在任务列表中找到刚创建的任务
2. 点击"开始"按钮启动爬取
3. 点击"查看日志"按钮查看实时爬取日志

### 查看爬取结果

1. 任务完成后，点击"查看结果"按钮
2. 查看爬取到的详细结果，包括标题、URL和上下文

### 重新爬取任务

1. 对于已完成或失败的任务，点击"重新爬取"按钮
2. 系统会自动使用相同的配置重新启动爬取任务

## 项目结构

```
PythonWebCrawler/
├── app.py              # Flask应用主文件
├── crawler.py          # 爬虫核心代码
├── models.py           # 数据库模型
├── requirements.txt    # 依赖项
├── Dockerfile          # Docker构建文件
├── docker-compose.yml  # Docker Compose配置
├── README.md           # 项目文档
└── templates/
    ├── index.html      # 主界面
    └── results.html    # 结果详情页面
```

## 注意事项

- 爬虫会遵守robots.txt规则，不要爬取不允许的网站
- 建议设置合理的爬取速度，避免对目标网站造成压力
- 对于大型网站，建议设置适当的最大爬取页面数
- 某些网站可能会拒绝爬虫访问，这是正常现象

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！