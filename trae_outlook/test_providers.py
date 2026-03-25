import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from register import (
    TempMailAsiaProvider,
    TempMailAwslProvider,
    GuerrillaMailProvider,
    MailDropProvider,
)

def test_temp_mail_providers():
    print("=" * 60)
    print("Testing Temporary Email Providers")
    print("=" * 60)
    
    results = []
    
    print("\n[1/4] Testing TempMailAsiaProvider...")
    try:
        provider = TempMailAsiaProvider()
        email, password = provider.create_email()
        if email:
            print(f"    [OK] Created email: {email}")
            messages = provider.get_messages(email)
            print(f"    [OK] Get messages: {len(messages)} messages")
            results.append(("TempMailAsia", True, email))
        else:
            print(f"    [FAIL] Failed to create email")
            results.append(("TempMailAsia", False, None))
        provider.close()
    except Exception as e:
        print(f"    [FAIL] Error: {e}")
        results.append(("TempMailAsia", False, str(e)))
    
    print("\n[2/4] Testing TempMailAwslProvider...")
    try:
        provider = TempMailAwslProvider()
        email, password = provider.create_email()
        if email:
            print(f"    [OK] Created email: {email}")
            messages = provider.get_messages(email)
            print(f"    [OK] Get messages: {len(messages)} messages")
            results.append(("TempMailAwsl", True, email))
        else:
            print(f"    [FAIL] Failed to create email")
            results.append(("TempMailAwsl", False, None))
        provider.close()
    except Exception as e:
        print(f"    [FAIL] Error: {e}")
        results.append(("TempMailAwsl", False, str(e)))
    
    print("\n[3/4] Testing GuerrillaMailProvider...")
    try:
        provider = GuerrillaMailProvider()
        email, password = provider.create_email()
        if email:
            print(f"    [OK] Created email: {email}")
            messages = provider.get_messages(email)
            print(f"    [OK] Get messages: {len(messages)} messages")
            results.append(("GuerrillaMail", True, email))
        else:
            print(f"    [FAIL] Failed to create email")
            results.append(("GuerrillaMail", False, None))
        provider.close()
    except Exception as e:
        print(f"    [FAIL] Error: {e}")
        results.append(("GuerrillaMail", False, str(e)))
    
    print("\n[4/4] Testing MailDropProvider...")
    try:
        provider = MailDropProvider()
        email, password = provider.create_email()
        if email:
            print(f"    [OK] Created email: {email}")
            messages = provider.get_messages(email)
            print(f"    [OK] Get messages: {len(messages)} messages")
            results.append(("MailDrop", True, email))
        else:
            print(f"    [FAIL] Failed to create email")
            results.append(("MailDrop", False, None))
        provider.close()
    except Exception as e:
        print(f"    [FAIL] Error: {e}")
        results.append(("MailDrop", False, str(e)))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, success, info in results:
        status = "PASS" if success else "FAIL"
        info_str = info if info else ""
        print(f"  {name:20s}: [{status}] {info_str}")
    
    passed = sum(1 for _, s, _ in results if s)
    print(f"\nTotal: {passed}/{len(results)} passed")
    return all(s for _, s, _ in results)


def test_kiro_auth():
    print("\n" + "=" * 60)
    print("Testing Kiro Auth Client")
    print("=" * 60)
    
    try:
        from register import KiroAuthClient
        client = KiroAuthClient()
        device_data = client.get_device_code()
        if device_data:
            print(f"  [OK] Got device code")
            print(f"      verification_uri: {device_data.get('verification_uri', 'N/A')}")
            print(f"      user_code: {device_data.get('user_code', 'N/A')}")
            client.close()
            return True
        else:
            print(f"  [FAIL] Failed to get device code")
            client.close()
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_outlook_client():
    print("\n" + "=" * 60)
    print("Testing Outlook Mail Client (auth only)")
    print("=" * 60)
    
    try:
        from register import OutlookMailClient
        import asyncio
        
        client = OutlookMailClient("test@example.com", "testpassword")
        
        async def test():
            auth_url, code_verifier, redirect_uri, client_id, scopes = await client.authenticate()
            return True
        
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(test())
        loop.close()
        
        if result:
            print(f"  [OK] OAuth flow initialized successfully")
            return True
        else:
            print(f"  [FAIL] Failed to initialize OAuth flow")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


if __name__ == "__main__":
    all_passed = True
    
    all_passed &= test_temp_mail_providers()
    all_passed &= test_kiro_auth()
    all_passed &= test_outlook_client()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)