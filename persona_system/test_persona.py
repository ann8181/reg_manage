#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona_system import create_persona_system

def test_basic_usage():
    print("=== Persona System Basic Test ===\n")
    
    ps = create_persona_system("data/persona_test")
    
    print("1. Generate Single Identity:")
    identity = ps.generate_identity(country="US", gender="Male", age_range=(25, 40))
    print(f"   Name: {identity['profile']['name']['full']}")
    print(f"   Age: {identity['profile']['demographics']['age']}")
    print(f"   Location: {identity['profile']['location']['city']}, {identity['profile']['location']['state']}")
    print(f"   Quality Score: {identity['quality_score']}")
    print(f"   Fingerprint: {identity['profile']['browser_fingerprint']['user_agent'][:60]}...")
    print()
    
    print("2. Generate Batch Identities:")
    identities = ps.generate_batch_identities(count=3, country="US", age_range=(22, 35))
    for i in identities:
        print(f"   - {i['profile']['name']['full']} (Score: {i['quality_score']})")
    print()
    
    print("3. System Stats:")
    stats = ps.get_system_stats()
    print(f"   Total Identities: {stats['identities']['total']}")
    print(f"   Total Accounts: {stats['accounts']['total']}")
    print(f"   Total Proxies: {stats['proxies']['total']}")
    print()
    
    print("4. Create Account:")
    account = ps.create_account(
        identity_id=identity['id'],
        service={
            "name": "github",
            "display_name": "GitHub",
            "category": "ai"
        },
        credentials={
            "email": f"user_{identity['id'][:8]}@mail.com",
            "password": "SecurePass123!",
            "username": f"githubuser_{identity['id'][:8]}"
        }
    )
    print(f"   Account ID: {account['id']}")
    print(f"   Service: {account['service']['name']}")
    print(f"   Email: {account['credentials']['email']}")
    print()
    
    print("5. Get Accounts by Service:")
    github_accounts = ps.get_accounts_by_service("github")
    print(f"   GitHub Accounts: {len(github_accounts)}")
    print()
    
    print("6. Identity Selection for Service:")
    selected = ps.select_identity_for_service("github", strategy="isolation")
    if selected:
        print(f"   Selected: {selected['profile']['name']['full']}")
    else:
        print("   No identity available (all used for GitHub)")
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_basic_usage()
