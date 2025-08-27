# 音艺智创 - 元宇宙音乐教育平台

## 项目概述
音艺智创是一个基于Web的元宇宙音乐教育平台，旨在提供创新的音乐学习体验。平台结合了传统音乐教育与现代技术，为用户提供丰富的学习资源、社区互动和智能辅助功能。

## 技术栈
- **前端**：HTML, CSS, JavaScript, Bootstrap 5
- **后端**：Python Flask
- **数据库**：MySQL
- **AI集成**：DeepSeek API

## 项目结构
- `app.py`：主应用程序文件，包含所有路由和业务逻辑
- `music.sql`：数据库结构文件
- `static/`：静态资源目录（图片、视频等媒体文件）
- `templates/`：HTML模板文件
- `test/`：测试文件目录
- `uwsgi.ini`：uWSGI配置文件（用于生产环境部署）

## 主要功能

### 用户系统
- 用户注册与登录
- 用户权限管理（普通用户/管理员）
- 用户设置与个人资料管理

### 学习功能
- 初级和高级音乐课程
- 音乐历史与理论学习
- 学习进度跟踪
- 在线测试与评估

### 社区功能
- 论坛讨论
- 发布帖子和评论
- 内容管理（发布、编辑、删除）
- 用户互动

### AI智能助手
- 基于DeepSeek API的智能对话
- 音乐学习辅助
- 问答功能

## 安装与运行

### 环境要求
- Python 3.6+
- MySQL 8.0+
- 必要的Python包（见下文）

### 安装步骤
1. 克隆项目到本地
```
git clone [项目仓库URL]
```

2. 安装依赖
```
pip install flask pymysql openai
```

3. 导入数据库
```
mysql -u [用户名] -p < music.sql
```

4. 配置数据库连接
编辑`app.py`中的数据库连接参数：
```python
def get_db_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="[你的MySQL用户名]",
        password="[你的MySQL密码]",
        database="music",
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
```

5. 配置DeepSeek API（如需使用AI功能）
编辑`app.py`中的API密钥：
```python
DEEPSEEK_API_KEY = "[你的DeepSeek API密钥]"
```

6. 运行应用
```
python app.py
```

### 生产环境部署
使用uWSGI和Nginx进行部署：
```
uwsgi --ini uwsgi.ini
```

## 管理员账户
默认管理员账户：
- 用户名：root
- 密码：123
