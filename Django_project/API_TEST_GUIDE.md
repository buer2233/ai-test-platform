# API测试脚本使用指南

本目录包含多个API测试脚本，用于测试后端API功能。

## 测试脚本列表

### 1. `generate_api_test_report.py` - 完整测试报告生成器
**用途**: 生成完整的API测试报告（JSON格式）
**使用方法**:
```bash
cd Django_project
python generate_api_test_report.py
```

**输出**:
- 控制台: 测试进度和摘要
- 文件: `api_test_report.json` (详细测试数据)

**测试内容**:
- 所有核心API端点（23个）
- 分类统计
- 响应时间测量
- 数据验证

### 2. `final_api_test.py` - 快速测试脚本
**用途**: 快速测试主要API功能
**使用方法**:
```bash
cd Django_project
python final_api_test.py
```

**输出**: 控制台测试结果

**测试内容**:
- 核心CRUD操作
- 完整数据流程测试
- 自动清理测试数据

### 3. `check_auth_setup.py` - 认证检查工具
**用途**: 检查认证设置和Token获取
**使用方法**:
```bash
cd Django_project
python check_auth_setup.py
```

**输出**: 当前用户和Token信息

### 4. `comprehensive_api_test.py` - 综合测试（旧版）
**用途**: 早期版本的完整测试脚本
**注意**: 已被`generate_api_test_report.py`取代

### 5. `test_all_viewsets.py` - ViewSet操作测试
**用途**: 测试所有ViewSet的自定义操作
**使用方法**:
```bash
cd Django_project
python test_all_viewsets.py
```

## 测试结果文件

### `api_test_report.json`
完整的测试报告JSON文件，包含：
- 每个端点的详细信息
- 响应时间
- 响应数据
- 错误信息（如果有）

### `API_TEST_REPORT.md`
人类可读的测试报告Markdown文档

## 运行所有测试

### 运行完整测试套件
```bash
cd Django_project

# 1. 检查认证
python check_auth_setup.py

# 2. 运行完整测试
python generate_api_test_report.py

# 3. 查看报告
# - JSON报告: api_test_report.json
# - Markdown报告: API_TEST_REPORT.md
```

## 测试覆盖的API端点

### 认证 (Auth)
- GET /api/v1/api-automation/auth/user/

### 项目管理 (Project)
- GET /api/v1/api-automation/projects/
- GET /api/v1/api-automation/projects/{id}/
- POST /api/v1/api-automation/projects/{id}/clone/

### 集合管理 (Collection)
- GET /api/v1/api-automation/collections/
- GET /api/v1/api-automation/collections/{id}/
- GET /api/v1/api-automation/collections/{id}/test_cases/

### 测试用例 (TestCase)
- GET /api/v1/api-automation/test-cases/
- GET /api/v1/api-automation/test-cases/{id}/
- POST /api/v1/api-automation/test-cases/{id}/clone/

### 环境 (Environment)
- GET /api/v1/api-automation/environments/
- GET /api/v1/api-automation/environments/{id}/
- GET /api/v1/api-automation/environments/{id}/test_connection/
- POST /api/v1/api-automation/environments/{id}/set-default/

### 执行 (Execution)
- GET /api/v1/api-automation/executions/
- GET /api/v1/api-automation/executions/{id}/

### 报告 (Report)
- GET /api/v1/api-automation/reports/

### Dashboard
- GET /api/v1/api-automation/dashboard/
- GET /api/v1/api-automation/dashboard/environment_reports/
- GET /api/v1/api-automation/dashboard/collection_reports/

### 断言 (Assertion - 嵌套)
- GET /api/v1/api-automation/test-cases/{id}/assertions/

### 数据提取 (Extraction - 嵌套)
- GET /api/v1/api-automation/test-cases/{id}/extractions/

### HTTP执行器
- GET /api/v1/api-automation/test-execute/history/

## 自定义测试

### 创建新的测试脚本
```python
import os
import django
import requests

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

# 获取认证token
User = get_user_model()
admin = User.objects.get(username='admin')
token = Token.objects.get(user=admin)

# 配置请求
BASE_URL = "http://127.0.0.1:8000"
headers = {'Authorization': f'Token {token.key}'}

# 执行测试
response = requests.get(f"{BASE_URL}/api/v1/api-automation/projects/", headers=headers)
print(response.json())
```

## 测试最佳实践

### 1. 运行测试前确保
- Django服务正在运行 (`python manage.py runserver`)
- 数据库已迁移 (`python manage.py migrate`)
- admin用户存在

### 2. 测试数据清理
测试脚本会自动清理创建的测试数据，但建议：
- 定期检查数据库中的测试数据
- 使用单独的测试数据库进行自动化测试

### 3. 持续集成
可以将这些测试脚本集成到CI/CD流程中：
```bash
# 在CI/CD中运行
python manage.py test
python generate_api_test_report.py
# 检查测试通过率
```

## 常见问题

### Q: 如何修改测试的服务器地址？
A: 修改脚本中的`BASE_URL`变量：
```python
BASE_URL = "http://your-server:port"
```

### Q: 如何使用不同的用户进行测试？
A: 修改获取用户的代码：
```python
user = User.objects.get(username='your_username')
token = Token.objects.get(user=user)
```

### Q: 测试失败怎么办？
A: 查看详细的错误信息：
1. 检查`api_test_report.json`中的详细错误
2. 查看Django日志文件
3. 使用Django调试工具

## 相关文档
- API完整测试报告: `API_TEST_REPORT.md`
- 项目开发文档: `../develop_document/`
- 测试用例文档: `../test_case/`

---

**最后更新**: 2025-12-24
**维护者**: Claude Code
