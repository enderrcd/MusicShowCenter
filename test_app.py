import unittest
from app import app, get_db_connection, session
from flask import url_for
from unittest.mock import patch, MagicMock
import pymysql  # 添加 pymysql 模块导入

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = '123'
        self.app = app.test_client()
        self.app.testing = True
        self.ctx = app.app_context()
        self.ctx.push()
        # 添加应用上下文设置
        app.config['SERVER_NAME'] = 'localhost'
        app.config['APPLICATION_ROOT'] = '/'
        app.config['PREFERRED_URL_SCHEME'] = 'http'

    def tearDown(self):
        self.ctx.pop()

    def test_root_redirect(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/main')

    @patch('app.get_db_connection')
    def test_login_success(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'username': 'testuser', 'is_admin': 0, 'id': 1}

        response = self.app.post('/login', data=dict(username='testuser', password='testpass'), follow_redirects=True)
        with self.app.session_transaction() as sess:
            flashes = list(sess['_flashes'])
        self.assertIn(('message', '登录成功！'), flashes)
        print("Login Success Data:", mock_cursor.fetchone.return_value)  # 打印登录成功的数据

    @patch('app.get_db_connection')
    def test_login_failure(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        response = self.app.post('/login', data=dict(username='testuser', password='wrongpass'), follow_redirects=True)
        with self.app.session_transaction() as sess:
            flashes = list(sess['_flashes'])
        self.assertIn(('message', '用户名或密码错误'), flashes)
        print("Login Failure Data:", mock_cursor.fetchone.return_value)  # 打印登录失败的数据

    @patch('app.get_db_connection')
    def test_login_database_error(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = pymysql.MySQLError("Database error")

        response = self.app.post('/login', data=dict(username='testuser', password='testpass'), follow_redirects=True)
        with self.app.session_transaction() as sess:
            flashes = list(sess['_flashes'])
        self.assertIn(('message', '发生错误: Database error'), flashes)
        print("Login Database Error:", mock_cursor.execute.side_effect)  # 打印数据库错误信息

    def test_logout(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['is_admin'] = 0
            sess['id'] = 1

        response = self.app.get('/logout', follow_redirects=True)
        with self.app.session_transaction() as sess:
            flashes = list(sess['_flashes'])
        self.assertIn(('message', 'Logged out'), flashes)
        print("Logout Session Data:", sess)  # 打印注销时的会话数据

    @patch('app.get_db_connection')
    def test_register_success(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        response = self.app.post('/register', data=dict(username='newuser', password='newpass'), follow_redirects=True)
        with self.app.session_transaction() as sess:
            flashes = list(sess['_flashes'])
        self.assertIn(('message', '注册成功！'), flashes)
        print("Register Success Data:", mock_cursor.execute.call_args)  # 打印注册成功的数据

    @patch('app.get_db_connection')
    def test_register_failure(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = pymysql.MySQLError("Database error")

        response = self.app.post('/register', data=dict(username='newuser', password='newpass'), follow_redirects=True)
        with self.app.session_transaction() as sess:
            flashes = list(sess['_flashes'])
        self.assertIn(('message', '注册失败，请重试'), flashes)
        print("Register Failure Data:", mock_cursor.execute.side_effect)  # 打印注册失败的数据

    @patch('app.get_db_connection')
    def test_forum_access_denied(self, mock_get_db_connection):
        response = self.app.get('/forum', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data)
        print("Forum Access Denied Response:", response.data)  # 打印论坛访问被拒绝的响应数据

    @patch('app.get_db_connection')
    def test_forum_access_granted(self, mock_get_db_connection):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['is_admin'] = 0
            sess['id'] = 1

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        response = self.app.get('/forum', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xe8\xae\xba\xe5\x9d\x9b', response.data)  # 匹配中文“论坛”
        print("Forum Access Granted Data:", mock_cursor.fetchall.return_value)  # 打印论坛访问成功的数据

    @patch('app.get_db_connection')
    def test_user_setting_access_denied(self, mock_get_db_connection):
        response = self.app.get('/user_setting', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data)
        print("User Setting Access Denied Response:", response.data)  # 打印用户设置访问被拒绝的响应数据

    @patch('app.get_db_connection')
    def test_user_setting_access_granted(self, mock_get_db_connection):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['is_admin'] = 0
            sess['id'] = 1

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        response = self.app.get('/user_setting', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'user_setting', response.data)
        print("User Setting Access Granted Data:", mock_cursor.fetchall.return_value)  # 打印用户设置访问成功的数据

if __name__ == '__main__':
    unittest.main()