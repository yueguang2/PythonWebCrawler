from flask_sqlalchemy import SQLAlchemy

 db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    max_pages = db.Column(db.Integer, default=10)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    start_time = db.Column(db.Float)
    end_time = db.Column(db.Float)
    error_message = db.Column(db.Text)
    results = db.relationship('Result', backref='task', lazy=True, cascade='all, delete-orphan')

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500))
    context = db.Column(db.Text)
    found_at = db.Column(db.Float, default=lambda: time.time())

import time