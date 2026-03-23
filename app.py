from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Task, Result
from crawler import WebCrawler
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crawler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 时间戳转换过滤器
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

# 初始化数据库
with app.app_context():
    db.create_all()

# 爬虫任务线程
task_threads = {}

@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

# 全局日志存储
logs = {}

@app.route('/add_task', methods=['POST'])
def add_task():
    url = request.form.get('url')
    keywords = request.form.get('keyword')
    max_pages = int(request.form.get('max_pages', 10))
    log_level = request.form.get('log_level', 'info')
    
    if not url or not keywords:
        flash('请填写网站链接和关键词', 'danger')
        return redirect(url_for('index'))
    
    # 创建新任务
    task = Task(url=url, keywords=keywords, max_pages=max_pages, log_level=log_level, status='pending')
    db.session.add(task)
    db.session.commit()
    
    # 初始化日志
    logs[task.id] = []
    
    flash('任务创建成功', 'success')
    return redirect(url_for('index'))

@app.route('/start_task/<int:task_id>')
def start_task(task_id):
    with app.app_context():
        task = Task.query.get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('index'))
        
        if task.status == 'running':
            flash('任务已经在运行', 'warning')
            return redirect(url_for('index'))
        
        # 更新任务状态
        task.status = 'running'
        task.start_time = time.time()
        db.session.commit()
    
    # 启动爬虫线程
    def crawl_task():
        try:
            # 分割关键词
            with app.app_context():
                # 重新获取任务对象，确保在当前上下文中
                current_task = Task.query.get(task_id)
                if not current_task:
                    log_message = f"任务不存在: {task_id}"
                    logs[task_id].append({"time": time.time(), "message": log_message, "level": "error"})
                    return
                
                keywords = [k.strip() for k in current_task.keywords.split(',') if k.strip()]
                
                # 记录开始日志
                log_message = f"开始爬取 {current_task.url}，搜索关键词: {', '.join(keywords)}"
                logs[task_id].append({"time": time.time(), "message": log_message, "level": "info"})
            
            # 启动爬虫
            crawler = WebCrawler(current_task.url, keywords, current_task.max_pages, task_id, logs)
            results = crawler.start()
            
            # 保存结果到数据库
            with app.app_context():
                # 重新获取任务对象，确保在当前上下文中
                current_task = Task.query.get(task_id)
                if current_task:
                    # 创建新的会话
                    from models import db
                    # 保存结果
                    for result_data in results:
                        result = Result(
                            task_id=task_id,
                            url=result_data['url'],
                            title=result_data['title'],
                            context=result_data['context']
                        )
                        db.session.add(result)
                    
                    # 记录完成日志
                    log_message = f"爬取完成，共找到 {len(results)} 个结果"
                    logs[task_id].append({"time": time.time(), "message": log_message, "level": "info"})
                    
                    # 更新任务状态
                    current_task.status = 'completed'
                    current_task.end_time = time.time()
                    db.session.commit()
        except Exception as e:
            # 记录错误日志
            log_message = f"爬取过程中出错: {str(e)}"
            logs[task_id].append({"time": time.time(), "message": log_message, "level": "error"})
            
            # 使用应用上下文更新任务状态
            with app.app_context():
                # 重新获取任务对象，确保在当前上下文中
                current_task = Task.query.get(task_id)
                if current_task:
                    current_task.status = 'failed'
                    current_task.error_message = str(e)
                    db.session.commit()
        finally:
            del task_threads[task_id]
    
    thread = threading.Thread(target=crawl_task)
    thread.daemon = True
    thread.start()
    task_threads[task_id] = thread
    
    flash('任务开始执行', 'success')
    return redirect(url_for('index'))

@app.route('/task_results/<int:task_id>')
def task_results(task_id):
    task = Task.query.get(task_id)
    if not task:
        flash('任务不存在', 'danger')
        return redirect(url_for('index'))
    
    results = Result.query.filter_by(task_id=task_id).all()
    return render_template('results.html', task=task, results=results)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        flash('任务不存在', 'danger')
        return redirect(url_for('index'))
    
    # 删除相关结果
    Result.query.filter_by(task_id=task_id).delete()
    # 删除任务
    db.session.delete(task)
    db.session.commit()
    
    flash('任务删除成功', 'success')
    return redirect(url_for('index'))

@app.route('/restart_task/<int:task_id>')
def restart_task(task_id):
    with app.app_context():
        task = Task.query.get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('index'))
        
        # 删除旧的结果
        Result.query.filter_by(task_id=task_id).delete()
        
        # 重置任务状态
        task.status = 'running'
        task.start_time = time.time()
        task.end_time = None
        task.error_message = None
        db.session.commit()
    
    # 启动爬虫线程
    def crawl_task():
        try:
            # 分割关键词
            with app.app_context():
                # 重新获取任务对象，确保在当前上下文中
                current_task = Task.query.get(task_id)
                if not current_task:
                    log_message = f"任务不存在: {task_id}"
                    logs[task_id] = []
                    logs[task_id].append({"time": time.time(), "message": log_message, "level": "error"})
                    return
                
                keywords = [k.strip() for k in current_task.keywords.split(',') if k.strip()]
                
                # 初始化日志
                logs[task_id] = []
                
                # 记录开始日志
                log_message = f"开始爬取 {current_task.url}，搜索关键词: {', '.join(keywords)}"
                logs[task_id].append({"time": time.time(), "message": log_message, "level": "info"})
            
            # 启动爬虫
            crawler = WebCrawler(current_task.url, keywords, current_task.max_pages, task_id, logs)
            results = crawler.start()
            
            # 保存结果到数据库
            with app.app_context():
                # 重新获取任务对象，确保在当前上下文中
                current_task = Task.query.get(task_id)
                if current_task:
                    # 保存结果
                    for result_data in results:
                        result = Result(
                            task_id=task_id,
                            url=result_data['url'],
                            title=result_data['title'],
                            context=result_data['context']
                        )
                        db.session.add(result)
                    
                    # 记录完成日志
                    log_message = f"爬取完成，共找到 {len(results)} 个结果"
                    logs[task_id].append({"time": time.time(), "message": log_message, "level": "info"})
                    
                    # 更新任务状态
                    current_task.status = 'completed'
                    current_task.end_time = time.time()
                    db.session.commit()
        except Exception as e:
            # 记录错误日志
            log_message = f"爬取过程中出错: {str(e)}"
            if task_id not in logs:
                logs[task_id] = []
            logs[task_id].append({"time": time.time(), "message": log_message, "level": "error"})
            
            # 使用应用上下文更新任务状态
            with app.app_context():
                current_task = Task.query.get(task_id)
                if current_task:
                    current_task.status = 'failed'
                    current_task.error_message = str(e)
                    db.session.commit()
        finally:
            if task_id in task_threads:
                del task_threads[task_id]
    
    thread = threading.Thread(target=crawl_task)
    thread.daemon = True
    thread.start()
    task_threads[task_id] = thread
    
    flash('任务重新开始执行', 'success')
    return redirect(url_for('index'))

@app.route('/api/task_status/<int:task_id>')
def task_status(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'status': 'error', 'message': '任务不存在'})
    
    # 计算已爬取数量
    result_count = Result.query.filter_by(task_id=task_id).count()
    
    return jsonify({
        'status': task.status,
        'result_count': result_count
    })

@app.route('/api/task_logs/<int:task_id>')
def task_logs(task_id):
    if task_id in logs:
        return jsonify({'logs': logs[task_id]})
    else:
        return jsonify({'logs': []})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)