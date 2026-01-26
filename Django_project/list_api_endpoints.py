"""
列出所有API端点
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver
from django.conf import settings

print("="*80)
print("所有API端点")
print("="*80)

resolver = get_resolver()

patterns = []
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'url_patterns'):
        # 这是一个包含其他URLconf的对象
        for sub_pattern in pattern.url_patterns:
            if hasattr(sub_pattern, 'url_patterns'):
                # 嵌套的URL patterns
                for sub_sub_pattern in sub_pattern.url_patterns:
                    if hasattr(sub_sub_pattern, 'pattern'):
                        patterns.append(str(sub_sub_pattern.pattern))
            elif hasattr(sub_pattern, 'pattern'):
                patterns.append(str(sub_pattern.pattern))
    elif hasattr(pattern, 'pattern'):
        patterns.append(str(pattern.pattern))

# 只显示api-automation相关的端点
api_patterns = sorted([p for p in patterns if 'api-automation' in p])

for pattern in api_patterns:
    print(pattern)

print("\n" + "="*80)
print(f"总计 {len(api_patterns)} 个api-automation端点")
print("="*80)
