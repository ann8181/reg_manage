#!/usr/bin/env python3
"""
PersonaLite (傻瓜化API) 测试
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona_system.simple_api import create_persona

def test_simple_api():
    print("=" * 60)
    print("PersonaLite Simple API Test")
    print("=" * 60)
    
    ps = create_persona("data/test_simple")
    
    print("\n1. 一句话创建身份:")
    identity = ps.create_identity(country="US", gender="Male")
    print(f"   姓名: {identity['profile']['name']['full']}")
    print(f"   年龄: {identity['profile']['demographics']['age']}")
    print(f"   城市: {identity['profile']['location']['city']}")
    
    print("\n2. 一句话注册服务:")
    result = ps.register_service("github")
    print(f"   邮箱: {result['email']}")
    print(f"   密码: {result['password']}")
    print(f"   成功: {result['success']}")
    
    print("\n3. 一句话获取已注册账号:")
    account = ps.get_account_decrypted("github")
    if account:
        print(f"   邮箱: {account['credentials']['email']}")
        print(f"   密码: {account['credentials']['password']}")
    
    print("\n4. 注册多个服务:")
    for service in ["claude", "gpt", "cursor"]:
        result = ps.register_service(service)
        print(f"   {service}: {result['email']}")
    
    print("\n5. 获取统计:")
    stats = ps.get_stats()
    print(f"   身份总数: {stats['total_identities']}")
    print(f"   活跃身份: {stats['active_identities']}")
    print(f"   账号总数: {stats['total_accounts']}")
    print(f"   代理总数: {stats['total_proxies']}")
    print(f"   服务分布: {stats['accounts_by_service']}")
    
    print("\n6. 自动化准备:")
    setup = ps.auto_setup("twitter")
    print(f"   准备就绪: {setup['ready']}")
    if setup['identity']:
        print(f"   身份: {setup['identity']['profile']['name']['full']}")
    if setup['proxy']:
        print(f"   代理: {setup['proxy']['proxy']['host']}:{setup['proxy']['proxy']['port']}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_simple_api()
