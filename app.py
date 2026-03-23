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

@app.route('/add_task', methods=['POST'])
def add_task():
    url = request.form.get('url')
    keyword = request.form.get('keyword')
    max_pages = int(request.form.get('max_pages', 10))
    
    if not url or not keyword:
        flash('请填写网站链接和关键词', 'danger')
        return redirect(url_for('index'))
    
    # 创建新任务
    task = Task(url=url, keyword=keyword, max_pages=max_pages, status='pending')
    db.session.add(task)
    db.session.commit()
    
    flash('任务创建成功', 'success')
    return redirect(url_for('index'))

@app.route('/start_task/<int:task_id>')
def start_task(task_id):
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
            crawler = WebCrawler(task.url, task.keyword, task.max_pages, task.id)
            crawler.start()
            # 更新任务状态
            task.status = 'completed'
            task.end_time = time.time()
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
        finally:
            db.session.commit()
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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)