#!/usr/bin/env python3
"""
Reddit Streamer cho r/formula1
Stream posts và comments từ Reddit API sử dụng PRAW
"""

import praw
import time
import socket
import json
from datetime import datetime
import sys

class RedditStreamer:
    """Client để stream dữ liệu từ Reddit"""
    
    def __init__(self):
        """Khởi tạo Reddit client với thông tin xác thực"""
        print("Initializing Reddit client...")
        
        self.reddit = praw.Reddit(
            client_id="",
            client_secret="",
            user_agent="F1StreamBot by u/Icy_Physics4247",
            username="Icy_Physics4247"
        )
        
        self.subreddit = self.reddit.subreddit("formula1")
        
        # Kết nối tới Flume Source (Avro Source)
        self.flume_host = 'localhost'
        self.flume_port = 44444
        
        print(f"Connected to Reddit as: {self.reddit.user.me()}")
        print(f"Monitoring subreddit: r/{self.subreddit.display_name}")
    
    def format_post(self, submission):
        """Format post thành JSON để gửi tới Flume"""
        return {
            'type': 'post',
            'id': submission.id,
            'title': submission.title,
            'content': submission.selftext if submission.is_self else '',
            'score': submission.score,
            'flair': submission.link_flair_text or '',
            'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'subreddit': submission.subreddit.display_name,
            'author': str(submission.author) if submission.author else '[deleted]',
            'url': submission.url
        }
    
    def format_comment(self, comment, post_id):
        """Format comment thành JSON để gửi tới Flume"""
        return {
            'type': 'comment',
            'id': comment.id,
            'post_id': post_id,
            'content': comment.body,
            'score': comment.score,
            'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
            'author': str(comment.author) if comment.author else '[deleted]'
        }
    
    def send_to_flume(self, data):
        """
        Gửi dữ liệu tới Flume qua socket
        Trong production, nên sử dụng Avro RPC
        """
        try:
            # Tạo socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.flume_host, self.flume_port))
            
            # Gửi dữ liệu dưới dạng JSON
            message = json.dumps(data) + '\n'
            sock.sendall(message.encode('utf-8'))
            
            sock.close()
            return True
        except Exception as e:
            print(f"Error sending to Flume: {e}")
            return False
    
    def stream_posts(self):
        """Stream posts từ r/formula1"""
        print("\nStarting post stream...")
        print("=" * 60)
        
        try:
            for submission in self.subreddit.stream.submissions(skip_existing=False):
                try:
                    post_data = self.format_post(submission)
                    
                    print(f"\n[POST] {submission.title}")
                    print(f"  Score: {submission.score} | Flair: {submission.link_flair_text}")
                    print(f"  Time: {post_data['created_utc']}")
                    
                    # Gửi post tới Flume
                    if self.send_to_flume(post_data):
                        print("  ✓ Sent to Flume")
                    
                    # Lấy comments của post này
                    self.fetch_post_comments(submission)
                    
                except Exception as e:
                    print(f"Error processing post: {e}")
                    continue
                
                # Rate limiting
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nStopping stream...")
        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(30)  # Wait before retry
            self.stream_posts()  # Retry
    
    def fetch_post_comments(self, submission, limit=10):
        """Lấy comments mới nhất của một post"""
        try:
            submission.comments.replace_more(limit=0)
            comments = submission.comments.list()[:limit]
            
            for comment in comments:
                try:
                    comment_data = self.format_comment(comment, submission.id)
                    
                    print(f"    [COMMENT] by {comment_data['author']}: {comment_data['content'][:50]}...")
                    
                    # Gửi comment tới Flume
                    self.send_to_flume(comment_data)
                    
                except Exception as e:
                    print(f"    Error processing comment: {e}")
                    continue
                    
        except Exception as e:
            print(f"  Error fetching comments: {e}")
    
    def stream_comments(self):
        """Stream comments từ r/formula1"""
        print("\nStarting comment stream...")
        print("=" * 60)
        
        try:
            for comment in self.subreddit.stream.comments(skip_existing=False):
                try:
                    # Lấy post_id từ comment
                    post_id = comment.submission.id
                    comment_data = self.format_comment(comment, post_id)
                    
                    print(f"\n[COMMENT] on post {post_id[:8]}...")
                    print(f"  Author: {comment_data['author']}")
                    print(f"  Content: {comment_data['content'][:100]}...")
                    
                    # Gửi comment tới Flume
                    if self.send_to_flume(comment_data):
                        print("  ✓ Sent to Flume")
                    
                except Exception as e:
                    print(f"Error processing comment: {e}")
                    continue
                
                # Rate limiting
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nStopping stream...")
        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(30)  # Wait before retry
            self.stream_comments()  # Retry

def main():
    """Main function"""
    print("=" * 60)
    print("Reddit F1 Streamer - Powered by PRAW")
    print("=" * 60)
    
    streamer = RedditStreamer()
    
    # Chọn mode
    print("\nSelect streaming mode:")
    print("1. Stream posts only")
    print("2. Stream comments only")
    print("3. Stream both (recommended)")
    
    try:
        choice = input("\nYour choice (1-3): ").strip()
    except:
        choice = "1"
    
    print()
    
    if choice == "1":
        streamer.stream_posts()
    elif choice == "2":
        streamer.stream_comments()
    else:
        # Stream cả posts và comments (trong thực tế nên chạy 2 processes riêng)
        print("Streaming posts with their comments...")
        streamer.stream_posts()

if __name__ == "__main__":
    main()
