#!/usr/bin/env python3
"""
Flask Web UI for Reddit F1 Streaming Demo
Hiển thị live data từ PostgreSQL với các tính năng tương tác
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'postgres',
    'password': 'postgres123'
}

def get_db_connection():
    """Tạo kết nối database"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ====================================================================================
# ROUTES - Pages
# ====================================================================================

@app.route('/')
def index():
    """Trang chủ - Live Thread"""
    return render_template('index.html')

@app.route('/post/<post_id>')
def post_detail(post_id):
    """Chi tiết bài đăng"""
    return render_template('post_detail.html', post_id=post_id)

@app.route('/dashboard')
def dashboard():
    """Dashboard analytics"""
    return render_template('dashboard.html')

# ====================================================================================
# API ENDPOINTS - Posts
# ====================================================================================

@app.route('/api/posts')
def get_posts():
    """
    Lấy danh sách posts
    Query params:
    - flair: Filter theo flair
    - limit: Số lượng posts (default: 20)
    - offset: Phân trang (default: 0)
    """
    flair = request.args.get('flair', '')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if flair:
            cursor.execute("""
                SELECT * FROM posts 
                WHERE flair = %s
                ORDER BY created_utc DESC 
                LIMIT %s OFFSET %s
            """, (flair, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM posts 
                ORDER BY created_utc DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
        
        posts = cursor.fetchall()
        
        # Convert datetime to string
        for post in posts:
            if post['created_utc']:
                post['created_utc'] = post['created_utc'].isoformat()
        
        return jsonify({
            'success': True,
            'data': posts,
            'count': len(posts)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/posts/<post_id>')
def get_post(post_id):
    """Lấy chi tiết một post"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        
        if post:
            if post['created_utc']:
                post['created_utc'] = post['created_utc'].isoformat()
            
            return jsonify({
                'success': True,
                'data': post
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Post not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

# ====================================================================================
# API ENDPOINTS - Comments
# ====================================================================================

@app.route('/api/posts/<post_id>/comments')
def get_post_comments(post_id):
    """
    Lấy comments của một post
    Query params:
    - sort: best|new|controversial (default: best)
    - limit: Số lượng comments (default: 50)
    """
    sort = request.args.get('sort', 'best')
    limit = int(request.args.get('limit', 50))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Xác định sort order
        if sort == 'new':
            order_by = "created_utc DESC"
        elif sort == 'controversial':
            # Controversial = có nhiều upvote và downvote (giả sử bằng score gần 0 nhưng có activity)
            order_by = "ABS(score) DESC, created_utc DESC"
        else:  # best/top
            order_by = "score DESC, created_utc DESC"
        
        query = f"""
            SELECT * FROM comments 
            WHERE post_id = %s 
            ORDER BY {order_by}
            LIMIT %s
        """
        
        cursor.execute(query, (post_id, limit))
        comments = cursor.fetchall()
        
        # Convert datetime to string
        for comment in comments:
            if comment['created_utc']:
                comment['created_utc'] = comment['created_utc'].isoformat()
        
        return jsonify({
            'success': True,
            'data': comments,
            'count': len(comments)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

# ====================================================================================
# API ENDPOINTS - Dashboard Analytics
# ====================================================================================

@app.route('/api/analytics/stats')
def get_analytics_stats():
    """Lấy tổng số posts, comments, contributors cho stats cards"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM posts WHERE created_utc >= NOW() - INTERVAL '7 days') as total_posts,
                (SELECT COUNT(*) FROM comments WHERE created_utc >= NOW() - INTERVAL '7 days') as total_comments,
                (SELECT COUNT(DISTINCT author) FROM comments 
                 WHERE created_utc >= NOW() - INTERVAL '7 days' 
                 AND author != '[deleted]') as total_contributors
        """)
        
        stats = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'data': {
                'total_posts': stats['total_posts'],
                'total_comments': stats['total_comments'],
                'total_contributors': stats['total_contributors']
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/analytics/post-scores')
def get_post_scores():
    """Lấy dữ liệu điểm số posts theo thời gian"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Lấy tất cả posts (hoặc 7 ngày gần nhất nếu có nhiều data)
        cursor.execute("""
            SELECT 
                id,
                title,
                score,
                created_utc,
                flair
            FROM posts
            WHERE created_utc >= NOW() - INTERVAL '7 days'
            ORDER BY created_utc ASC
            LIMIT 100
        """)
        
        posts = cursor.fetchall()
        
        # Format data for Chart.js
        data = {
            'labels': [],
            'datasets': []
        }
        
        for post in posts:
            data['labels'].append(post['created_utc'].strftime('%H:%M'))
        
        # Tạo dataset
        scores = [post['score'] for post in posts]
        data['datasets'].append({
            'label': 'Post Score',
            'data': scores,
            'borderColor': 'rgb(255, 99, 132)',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'tension': 0.4
        })
        
        return jsonify({
            'success': True,
            'data': data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/analytics/top-contributors')
def get_top_contributors():
    """Top 10 contributors"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            WITH author_stats AS (
                SELECT 
                    author,
                    COUNT(*) as comment_count,
                    SUM(score) as total_score
                FROM comments
                WHERE 
                    created_utc >= NOW() - INTERVAL '7 days'
                    AND author != '[deleted]'
                GROUP BY author
            )
            SELECT 
                author,
                comment_count,
                total_score
            FROM author_stats
            ORDER BY total_score DESC, comment_count DESC
            LIMIT 10
        """)
        
        contributors = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': contributors
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/analytics/best-of')
def get_best_of():
    """Best of r/formula1 - Posts và comments có score cao nhất"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Top posts
        cursor.execute("""
            SELECT id, title, score, flair, created_utc
            FROM posts
            WHERE created_utc >= NOW() - INTERVAL '7 days'
            ORDER BY score DESC
            LIMIT 5
        """)
        top_posts = cursor.fetchall()
        
        # Top comments
        cursor.execute("""
            SELECT c.id, c.content, c.score, c.author, c.post_id, p.title as post_title
            FROM comments c
            JOIN posts p ON c.post_id = p.id
            WHERE c.created_utc >= NOW() - INTERVAL '7 days'
            ORDER BY c.score DESC
            LIMIT 5
        """)
        top_comments = cursor.fetchall()
        
        # Convert datetime
        for post in top_posts:
            if post['created_utc']:
                post['created_utc'] = post['created_utc'].isoformat()
        
        return jsonify({
            'success': True,
            'data': {
                'top_posts': top_posts,
                'top_comments': top_comments
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

# ====================================================================================
# API ENDPOINTS - User Interactions
# ====================================================================================

@app.route('/api/subscriptions', methods=['POST'])
def subscribe_to_post():
    """Theo dõi một post"""
    data = request.json
    user_id = data.get('user_id', 'demo_user')
    post_id = data.get('post_id')
    
    if not post_id:
        return jsonify({'success': False, 'error': 'post_id required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        subscription_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO post_subscriptions (id, user_id, post_id, active)
            VALUES (%s, %s, %s, true)
            ON CONFLICT DO NOTHING
        """, (subscription_id, user_id, post_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Subscribed successfully',
            'subscription_id': subscription_id
        })
    
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Tạo keyword alert"""
    data = request.json
    user_id = data.get('user_id', 'demo_user')
    keyword = data.get('keyword')
    min_score = data.get('min_score', 10)
    
    if not keyword:
        return jsonify({'success': False, 'error': 'keyword required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        alert_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO user_alerts (id, user_id, keyword, subreddit, min_score, enabled)
            VALUES (%s, %s, %s, %s, %s, true)
        """, (alert_id, user_id, keyword, 'formula1', min_score))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert created successfully',
            'alert_id': alert_id
        })
    
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts')
def get_alerts():
    """Lấy danh sách alerts của user"""
    user_id = request.args.get('user_id', 'demo_user')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM user_alerts
            WHERE user_id = %s AND enabled = true
            ORDER BY created_at DESC
        """, (user_id,))
        
        alerts = cursor.fetchall()
        
        # Convert datetime
        for alert in alerts:
            if alert['created_at']:
                alert['created_at'] = alert['created_at'].isoformat()
            if alert['updated_at']:
                alert['updated_at'] = alert['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'data': alerts
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/flairs')
def get_flairs():
    """Lấy danh sách flairs có sẵn"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT flair
            FROM posts
            WHERE flair IS NOT NULL AND flair != ''
            ORDER BY flair
        """)
        
        flairs = [row['flair'] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'data': flairs
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

# ====================================================================================
# Main
# ====================================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Reddit F1 Streaming - Web UI")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
