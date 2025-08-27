from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory,jsonify
import random
import re
import pymysql
from openai import OpenAI

import logging
app = Flask(__name__)
app.secret_key = '123'



logging.basicConfig(level=logging.INFO)

def get_db_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="ENDER",
        password="20050614RCD",
        database="music",
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


# 配置 DeepSeek API 参数
DEEPSEEK_API_KEY = "sk-ebfb06c37c6d433394e111c218b42d96"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 初始化 DeepSeek 客户端
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def generate_response(user_input):
    try:
        # 构造消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ]

        # 调用 DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用 deepseek-chat 模型
            messages=messages,
            stream=False,  # 非流式响应
        )

        # 提取生成的文本
        if response.choices and len(response.choices) > 0:
            generated_text = response.choices[0].message.content.strip()

            # 去除 Markdown 格式，但保留换行符
            generated_text = re.sub(r'\*\*(.*?)\*\*', r'\1', generated_text)
            generated_text = re.sub(r'\*(.*?)\*', r'\1', generated_text)
            generated_text = re.sub(r'#+\s*', '', generated_text)
            generated_text = re.sub(r'-\s*', '', generated_text)
            generated_text = re.sub(r'`(.*?)`', r'\1', generated_text)
            generated_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', generated_text)

            # 保留换行符
            generated_text = generated_text.replace('\n', '\n')

            result = {'generated_text': generated_text}
        else:
            logging.error(f"Unexpected API response format: {response}")
            result = {"error": "Failed to generate text."}

        return jsonify(result)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "An internal error occurred."})



@app.route("/")
def root():
    return redirect(url_for('main'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash('用户名和密码不能为空')
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "SELECT * FROM user_data WHERE username=%s AND password=%s"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            session['id'] = user['id']
            flash('登录成功！')
            return redirect(url_for('main'))
        else:
            flash('用户名或密码错误')
            return redirect(url_for('login'))

    except pymysql.MySQLError as e:
        flash(f"发生错误: {str(e)}")
        return redirect(url_for('login'))
    finally:
        conn.close()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash('用户名和密码不能为空')
        return redirect(url_for('register'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO user_data(username, password) VALUES(%s, %s)"
        cursor.execute(sql, (username, password))
        conn.commit()
        flash('注册成功！')
        return redirect(url_for('login'))
    except pymysql.MySQLError as e:
        flash('注册失败，请重试')
        return redirect(url_for('register'))
    finally:
        conn.close()

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    session.pop('id', None)
    flash('Logged out')
    return redirect(url_for('main'))

@app.route("/main")
def main():
    return render_template("main.html")

@app.route('/forum')
def forum():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT posts.*, user_data.username FROM posts JOIN user_data ON posts.user_id = user_data.id")
        posts = cursor.fetchall()
        return render_template('forum.html', posts=posts)
    except pymysql.MySQLError as e:
        flash(f"发生错误: {str(e)}")
        return redirect(url_for('forum'))
    finally:
        conn.close()


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not title or not body:
            flash('Title and content cannot be empty')
            return redirect(url_for('create_post'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query user's is_muted status
            cursor.execute("SELECT id, is_muted FROM user_data WHERE username=%s", [session['username']])
            user = cursor.fetchone()

            if user['is_muted']:
                flash('You are muted and cannot post')
                return redirect(url_for('create_post'))  # 确保返回的响应包含预期的字符串

            # Insert new post
            cursor.execute("INSERT INTO posts(title, body, user_id) VALUES(%s, %s, %s)", (title, body, user['id']))
            conn.commit()
            flash('Post created successfully!')
            return redirect(url_for('forum'))
        except pymysql.MySQLError as e:
            flash(f"An error occurred: {str(e)}")
            return redirect(url_for('create_post'))
        finally:
            conn.close()
    return render_template('create_post.html')


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get post and author information
        cursor.execute("SELECT posts.*, user_data.username AS author_username FROM posts JOIN user_data ON posts.user_id = user_data.id WHERE posts.id=%s", [post_id])
        post = cursor.fetchone()

        if request.method == 'POST':
            comment_body = request.form['body']

            if not comment_body:
                flash('Comment content cannot be empty')
                return redirect(url_for('view_post', post_id=post_id))

            # Query user's is_muted status
            cursor.execute("SELECT id, is_muted FROM user_data WHERE username=%s", [session['username']])
            user = cursor.fetchone()

            if user['is_muted']:
                flash('You are muted and cannot comment')
                return redirect(url_for('view_post', post_id=post_id))

            # Insert new comment
            cursor.execute("INSERT INTO comments(body, post_id, user_id) VALUES(%s, %s, %s)",
                           (comment_body, post_id, user['id']))
            conn.commit()
            flash('Comment posted successfully!')
            return redirect(url_for('view_post', post_id=post_id))

        # Get comments
        cursor.execute(
            "SELECT comments.*, user_data.username FROM comments JOIN user_data ON comments.user_id = user_data.id WHERE post_id=%s",
            [post_id])
        comments = cursor.fetchall()
        return render_template('post.html', post=post, comments=comments)
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('view_post', post_id=post_id))
    finally:
        conn.close()

@app.route("/overview")
def overview():
    return render_template("overview.html")

@app.route("/news")
def news():
    return render_template("news.html")

@app.route("/learn")
def learn():
    return render_template("learn.html")

@app.route("/begin")
def begin():
    return render_template("begin.html")

@app.route("/low_music")
def low_music():
    return render_template("low_music.html")

@app.route("/high_music")
def high_music():
    return render_template("high_music.html")


@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/user_setting", methods=["GET", "POST"])
def user_setting():
    if 'username' not in session:
        return redirect(url_for('login'))

    is_admin = session.get('is_admin', False)  # Check and provide default value

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if is_admin:
            # Admin can see all users, posts, and comments
            cursor.execute("SELECT * FROM user_data")
            users = cursor.fetchall()
            cursor.execute("SELECT posts.*, user_data.username FROM posts JOIN user_data ON posts.user_id = user_data.id")
            posts = cursor.fetchall()
            cursor.execute("SELECT comments.*, user_data.username FROM comments JOIN user_data ON comments.user_id = user_data.id")
            comments = cursor.fetchall()
        else:
            # Regular user can only see their own posts and comments
            cursor.execute("SELECT id FROM user_data WHERE username=%s", [session['username']])
            user = cursor.fetchone()
            cursor.execute("SELECT * FROM posts WHERE user_id=%s", [user['id']])
            posts = cursor.fetchall()
            cursor.execute("SELECT * FROM comments WHERE user_id=%s", [user['id']])
            comments = cursor.fetchall()
            users = []

        return render_template('user_setting.html', users=users, posts=posts, comments=comments, is_admin=is_admin)

    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('user_setting'))
    finally:
        conn.close()

@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if session.get('is_admin'):
            cursor.execute("DELETE FROM comments WHERE post_id=%s", [post_id])

        cursor.execute("DELETE FROM posts WHERE id=%s", [post_id])
        conn.commit()
        flash('Post deleted successfully!')
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))

@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM comments WHERE id=%s", [comment_id])
        conn.commit()
        flash('Comment deleted successfully!')
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))

@app.route("/mute_user/<int:user_id>", methods=["POST"])
def mute_user(user_id):
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE user_data SET is_muted=1 WHERE id=%s", [user_id])
        conn.commit()
        flash('User muted successfully!')
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))

@app.route("/unmute_user/<int:user_id>", methods=["POST"])
def unmute_user(user_id):
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE user_data SET is_muted=0 WHERE id=%s", [user_id])
        conn.commit()
        flash('User unmuted successfully!')
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))

@app.route("/promote_user/<int:user_id>", methods=["POST"])
def promote_user(user_id):
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE user_data SET is_admin=1 WHERE id=%s", [user_id])
        conn.commit()
        flash('User promoted to admin successfully!')
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))

@app.route("/demote_user/<int:user_id>", methods=["POST"])
def demote_user(user_id):
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE user_data SET is_admin=0 WHERE id=%s", [user_id])
        conn.commit()
        flash('User demoted to regular user successfully!')
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))

@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if 'username' not in session or (not session.get('is_admin') and user_id != session.get('id')):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if user_id == session.get('id') and session.get('username') == 'root':
            flash('Root user cannot delete themselves')
            return redirect(url_for('user_setting'))

        cursor.execute("DELETE FROM comments WHERE user_id=%s", [user_id])
        cursor.execute("DELETE FROM posts WHERE user_id=%s", [user_id])
        cursor.execute("DELETE FROM user_data WHERE id=%s", [user_id])
        conn.commit()
        flash('User deleted successfully!')

        if user_id == session.get('id'):
            session.pop('username', None)
            session.pop('is_admin', None)
            session.pop('id', None)
            flash('Logged out')
            return redirect(url_for('logout'))
    except pymysql.MySQLError as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('user_setting'))


@app.route("/new_1")
def new_1():
    return render_template("new_1.html")

@app.route("/new_2")
def new_2():
    return render_template("new_2.html")

@app.route("/new_3")
def new_3():
    return render_template("new_3.html")

@app.route("/new_4")
def new_4():
    return render_template("new_4.html")
@app.route('/xiazai')
def xiazai():
    return render_template("xiazai.html")

@app.route('/verify', methods=['POST'])
def verify():
    user_input = request.form.get('code')
    if user_input == '1234':  # 验证码为1234
        return send_from_directory('/root/webproject/web-learning/', 'project.zip', as_attachment=True)
    else:
        return redirect(url_for('xiazai', error="Invalid code"))

@app.route('/test',methods=["POST","GET"])
def test():
    return render_template("test.html")


@app.route('/get_questions')
def get_questions():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取所有题目ID
            cursor.execute("SELECT id FROM questions")
            all_ids = [row['id'] for row in cursor.fetchall()]

            # 随机选择10个不重复的ID
            selected_ids = random.sample(all_ids, min(10, len(all_ids)))

            # 获取这10道题的完整信息
            format_strings = ','.join(['%s'] * len(selected_ids))
            cursor.execute(f"SELECT * FROM questions WHERE id IN ({format_strings})", selected_ids)
            questions = cursor.fetchall()

            # 为每个问题添加一个唯一标识符（用于前端提交时识别）
            for i, question in enumerate(questions):
                question['question_id'] = f"q_{i}"

        return jsonify({'questions': questions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    try:
        data = request.json
        user_answers = data.get('answers', {})

        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取所有问题的正确答案
            question_ids = [qid.replace('q_', '') for qid in user_answers.keys()]
            format_strings = ','.join(['%s'] * len(question_ids))
            cursor.execute(f"SELECT id, answer FROM questions WHERE id IN ({format_strings})", question_ids)
            correct_answers = {}
            for row in cursor.fetchall():
                if row is not None and 'answer' in row:  # 添加None检查和字段存在检查
                    correct_answers[str(row['id'])] = row['answer']

            # 计算得分
            score = 0
            results = {}

            for q_id, user_answer in user_answers.items():
                db_id = q_id.replace('q_', '')
                if db_id in correct_answers:
                    if user_answer:  # 检查用户是否提交了答案
                        is_correct = (user_answer == correct_answers[db_id])
                        results[q_id] = {
                            'correct': is_correct,
                            'correct_answer': correct_answers[db_id]
                        }
                        if is_correct:
                            score += 10
                    else:
                        results[q_id] = {
                            'correct': False,
                            'correct_answer': correct_answers[db_id],
                            'message': '未提交本题答案'
                        }
                else:
                    results[q_id] = {
                        'correct': False,
                        'message': '未提交本题答案'
                    }

        return jsonify({
            'score': score,
            'total': len(user_answers) * 10,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_input = data.get('text')
    return generate_response(user_input)

@app.route('/charfront')
def charfront():
    return render_template('chatfront.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == "__main__":
    app.run(debug=True)




















