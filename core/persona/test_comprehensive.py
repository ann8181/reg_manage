#!/usr/bin/env python3
"""
Persona System Comprehensive Test Suite
"""
import sys
import os
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona_system import (
    PersonaSystem, create_persona_system,
    IdentityGenerator, FingerprintGenerator,
    IdentityQualityScorer, ProxyQualityChecker,
    AccountManager, ProxyPoolManager,
    PersonaSelector, TaskContext
)

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def record(self, name: str, passed: bool, error: str = None):
        if passed:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            self.errors.append((name, error))
            print(f"  [FAIL] {name}: {error}")
    
    def summary(self):
        print(f"\n{'='*60}")
        print(f"Total: {self.passed + self.failed}, Passed: {self.passed}, Failed: {self.failed}")
        if self.errors:
            print("\nFailed Tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        return self.failed == 0


def test_identity_generator():
    print("\n[Test] IdentityGenerator")
    results = TestResults()
    
    gen = IdentityGenerator()
    
    # Test 1: Generate single identity
    identity = gen.generate(country="US", gender="Male", age_range=(25, 35))
    results.record(
        "Generate single identity",
        all([
            identity.get("id"),
            identity.get("profile", {}).get("name", {}).get("full"),
            identity.get("profile", {}).get("demographics", {}).get("age"),
            identity.get("profile", {}).get("location", {}).get("city"),
            identity.get("profile", {}).get("browser_fingerprint", {}).get("user_agent")
        ])
    )
    
    # Test 2: Generate batch identities
    batch = gen.generate_batch(count=5, country="US")
    results.record(
        "Generate batch identities",
        len(batch) == 5 and all(i.get("id") for i in batch)
    )
    
    # Test 3: Identity has valid quality score
    results.record(
        "Quality score calculated",
        0 <= identity.get("quality_score", -1) <= 100
    )
    
    # Test 4: Fingerprint uniqueness
    fingerprints = [i.get("profile", {}).get("browser_fingerprint", {}).get("canvas_hash") for i in batch]
    results.record(
        "Fingerprints are unique",
        len(fingerprints) == len(set(fingerprints))
    )
    
    # Test 5: Age range validation
    ages = [i.get("profile", {}).get("demographics", {}).get("age") for i in batch]
    results.record(
        "Ages within specified range (22-45)",
        all(22 <= age <= 45 for age in ages)
    )
    
    return results.summary()


def test_fingerprint_generator():
    print("\n[Test] FingerprintGenerator")
    results = TestResults()
    
    fp_gen = FingerprintGenerator()
    
    # Test 1: Generate fingerprint
    fp = fp_gen.generate()
    results.record(
        "Generate fingerprint",
        all([fp.get("user_agent"), fp.get("canvas_hash"), fp.get("audio_hash")])
    )
    
    # Test 2: Fingerprint has required fields
    required_fields = ["user_agent", "screen_resolution", "timezone", "language", "platform"]
    results.record(
        "Fingerprint has all required fields",
        all(fp.get(field) for field in required_fields)
    )
    
    # Test 3: Generate unique fingerprints
    fps = [fp_gen.generate() for _ in range(10)]
    canvas_hashes = [f.get("canvas_hash") for f in fps]
    results.record(
        "Canvas hashes are unique",
        len(canvas_hashes) == len(set(canvas_hashes))
    )
    
    # Test 4: User agent validity
    valid_uas = [f.get("user_agent").startswith("Mozilla/") for f in fps]
    results.record(
        "User agents are valid Mozilla format",
        all(valid_uas)
    )
    
    return results.summary()


def test_quality_scorer():
    print("\n[Test] IdentityQualityScorer")
    results = TestResults()
    
    scorer = IdentityQualityScorer()
    gen = IdentityGenerator()
    
    identity = gen.generate()
    
    # Test 1: Score calculation
    score = scorer.calculate_score(identity)
    results.record(
        "Score calculated correctly (0-100)",
        0 <= score <= 100
    )
    
    # Test 2: Grade assignment
    grade = scorer.get_quality_grade(score)
    valid_grades = ["A+", "A", "B", "C", "D", "F"]
    results.record(
        "Grade is valid",
        grade in valid_grades
    )
    
    # Test 3: Service validation
    validation = scorer.validate_for_service(identity, "github")
    results.record(
        "Service validation returns dict",
        isinstance(validation, dict) and len(validation) > 0
    )
    
    # Test 4: Low quality identity scoring
    bad_identity = {
        "profile": {
            "name": {"first": "X", "last": "Y", "full": "X Y"},
            "demographics": {"age": 10, "gender": "Unknown"},
            "location": {"city": "", "state": "", "zipcode": ""},
            "browser_fingerprint": {"user_agent": ""}
        }
    }
    bad_score = scorer.calculate_score(bad_identity)
    results.record(
        "Low quality identity gets low score",
        bad_score < 80
    )
    
    return results.summary()


def test_database_operations():
    print("\n[Test] Database Operations")
    results = TestResults()
    
    ps = create_persona_system("data/test_db")
    
    # Test 1: Add identity
    identity = ps.generate_identity(save=True)
    stored = ps.get_identity(identity["id"])
    results.record(
        "Identity stored and retrieved",
        stored is not None and stored.get("id") == identity["id"]
    )
    
    # Test 2: Get active identities
    active = ps.get_active_identities()
    results.record(
        "Get active identities",
        len(active) >= 1
    )
    
    # Test 3: Identity stats
    stats = ps.get_identity_stats()
    results.record(
        "Identity stats calculated",
        "total" in stats and "quality_distribution" in stats
    )
    
    # Test 4: Generate multiple and verify count
    ps.generate_batch_identities(count=3, save=True)
    stats2 = ps.get_identity_stats()
    results.record(
        "Batch generation increases count",
        stats2["total"] >= stats["total"] + 3
    )
    
    # Cleanup
    ps.clear_all_data(confirm=True)
    
    return results.summary()


def test_account_management():
    print("\n[Test] Account Management")
    results = TestResults()
    
    ps = create_persona_system("data/test_account")
    ps.clear_all_data(confirm=True)
    
    # Create identity first
    identity = ps.generate_identity(save=True)
    
    # Test 1: Create account
    account = ps.create_account(
        identity_id=identity["id"],
        service={"name": "github", "display_name": "GitHub", "category": "ai"},
        credentials={"email": "test@mail.com", "password": "pass123", "username": "testuser"}
    )
    results.record(
        "Account created",
        account.get("id") and account.get("identity_id") == identity["id"]
    )
    
    # Test 2: Get account
    retrieved = ps.get_account(account["id"])
    results.record(
        "Account retrieved",
        retrieved is not None and retrieved.get("credentials", {}).get("email") == "test@mail.com"
    )
    
    # Test 3: Get accounts by service
    github_accounts = ps.get_accounts_by_service("github")
    results.record(
        "Get accounts by service",
        len(github_accounts) >= 1
    )
    
    # Test 4: Get accounts by identity
    identity_accounts = ps.get_accounts_by_identity(identity["id"])
    results.record(
        "Get accounts by identity",
        len(identity_accounts) >= 1
    )
    
    # Test 5: Get available account (BEFORE locking)
    available = ps.get_available_account("github")
    results.record(
        "Get available account",
        available is not None and available.get("id") == account["id"]
    )
    
    # Test 6: Update account status
    success = ps.update_account_status(account["id"], "locked")
    results.record(
        "Update account status",
        success
    )
    
    # Cleanup
    ps.clear_all_data(confirm=True)
    
    return results.summary()


def test_proxy_management():
    print("\n[Test] Proxy Management")
    results = TestResults()
    
    ps = create_persona_system("data/test_proxy")
    ps.clear_all_data(confirm=True)
    
    # Test 1: Add proxy
    proxy = ps.add_proxy(
        host="192.168.1.1",
        port=8080,
        protocol="http",
        username="user",
        password="pass",
        country="US"
    )
    results.record(
        "Proxy added",
        proxy.get("id") and proxy.get("proxy", {}).get("host") == "192.168.1.1"
    )
    
    # Test 2: Add proxy from string
    proxy2 = ps.add_proxy_from_string("user2:pass2@10.0.0.1:3128", country="US")
    results.record(
        "Proxy added from string",
        proxy2 is not None and proxy2.get("proxy", {}).get("host") == "10.0.0.1"
    )
    
    # Test 3: Get available proxy (min_score=0 since proxy not quality-checked)
    available = ps.proxy_manager.get_best_proxy(country="US", min_score=0)
    results.record(
        "Get available proxy",
        available is not None
    )
    
    # Test 4: Proxy stats
    stats = ps.proxy_manager.get_stats()
    results.record(
        "Proxy stats calculated",
        "total" in stats and "available" in stats
    )
    
    # Cleanup
    ps.clear_all_data(confirm=True)
    
    return results.summary()


def test_persona_selector():
    print("\n[Test] Persona Selector")
    results = TestResults()
    
    ps = create_persona_system("data/test_selector")
    ps.clear_all_data(confirm=True)
    
    # Create multiple identities
    identities = ps.generate_batch_identities(count=3, save=True)
    
    # Create account for one identity
    identity = identities[0]
    ps.create_account(
        identity_id=identity["id"],
        service={"name": "github", "display_name": "GitHub", "category": "ai"},
        credentials={"email": "used@mail.com", "password": "pass"}
    )
    
    # Test 1: Isolation strategy
    selected = ps.select_identity_for_service("github", strategy="isolation")
    results.record(
        "Isolation strategy avoids used identity",
        selected is None or selected.get("id") != identity["id"]
    )
    
    # Test 2: Priority strategy
    selected = ps.select_identity_for_service("gitlab", strategy="priority")
    results.record(
        "Priority strategy returns identity",
        selected is not None
    )
    
    # Test 3: Random strategy
    selected = ps.select_identity_for_service("gitlab", strategy="random")
    results.record(
        "Random strategy returns identity",
        selected is not None
    )
    
    # Test 4: Select by specific ID
    selected = ps.select_identity_for_service("gitlab", strategy="isolation", identity_id=identities[1]["id"])
    results.record(
        "Select by specific ID",
        selected is not None and selected.get("id") == identities[1]["id"]
    )
    
    # Test 5: Regenerate when none available
    # Use all identities for github
    for i in range(2, len(identities)):
        ps.create_account(
            identity_id=identities[i]["id"],
            service={"name": "github", "display_name": "GitHub", "category": "ai"},
            credentials={"email": f"used{i}@mail.com", "password": "pass"}
        )
    new_identity = ps.select_identity_for_service("github", strategy="isolation", regenerate=True)
    results.record(
        "Regenerate when none available",
        new_identity is not None and new_identity.get("metadata", {}).get("source") == "local_generator"
    )
    
    # Cleanup
    ps.clear_all_data(confirm=True)
    
    return results.summary()


def test_task_context():
    print("\n[Test] Task Context")
    results = TestResults()
    
    # Test 1: Create task context
    context = TaskContext(
        task_id="test-001",
        task_type="account_registration",
        service="github"
    )
    results.record(
        "Task context created",
        context.task_id == "test-001" and context.status == "pending"
    )
    
    # Test 2: Assign identity
    identity = {"id": "identity-123", "profile": {"name": {"full": "Test User"}}}
    context.assign_identity(identity)
    results.record(
        "Identity assigned to context",
        context.identity is not None and len(context.steps) == 1
    )
    
    # Test 3: Mark as running
    context.mark_running()
    results.record(
        "Context marked running",
        context.status == "running"
    )
    
    # Test 4: Mark success
    context.mark_success()
    results.record(
        "Context marked success",
        context.status == "success" and context.completed_at is not None
    )
    
    # Test 5: To dict conversion
    context_dict = context.to_dict()
    results.record(
        "Context converted to dict",
        "task_id" in context_dict and "steps" in context_dict
    )
    
    return results.summary()


def test_system_integration():
    print("\n[Test] System Integration")
    results = TestResults()
    
    ps = create_persona_system("data/test_integration")
    ps.clear_all_data(confirm=True)
    
    # Full workflow: Generate identity -> Select for service -> Create account
    
    # Step 1: Generate batch identities
    identities = ps.generate_batch_identities(count=5, save=True)
    results.record(
        "Step 1: Batch generation",
        len(identities) == 5
    )
    
    # Step 2: Select identity for GitHub
    github_identity = ps.select_identity_for_service("github", strategy="isolation")
    results.record(
        "Step 2: Identity selection for GitHub",
        github_identity is not None
    )
    
    # Step 3: Create GitHub account
    github_account = ps.create_account(
        identity_id=github_identity["id"],
        service={"name": "github", "display_name": "GitHub", "category": "ai"},
        credentials={
            "email": f"github_user_{github_identity['id'][:8]}@mail.com",
            "password": "SecurePass123!",
            "username": f"github_{github_identity['id'][:8]}"
        }
    )
    results.record(
        "Step 3: Account creation",
        github_account is not None
    )
    
    # Step 4: Select different identity for GitHub (should be isolated)
    github_identity2 = ps.select_identity_for_service("github", strategy="isolation")
    results.record(
        "Step 4: Isolation (different identity for same service)",
        github_identity2 is None or github_identity2.get("id") != github_identity.get("id")
    )
    
    # Step 5: Get system stats
    stats = ps.get_system_stats()
    results.record(
        "Step 5: System stats",
        stats.get("identities", {}).get("total", 0) >= 5
    )
    
    # Step 6: Export data
    exported = ps.export_all_data()
    results.record(
        "Step 6: Data export",
        "identities" in exported and "accounts" in exported
    )
    
    # Cleanup
    ps.clear_all_data(confirm=True)
    
    return results.summary()


def run_all_tests():
    print("=" * 60)
    print("PERSONA SYSTEM COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_identity_generator()
    all_passed &= test_fingerprint_generator()
    all_passed &= test_quality_scorer()
    all_passed &= test_database_operations()
    all_passed &= test_account_management()
    all_passed &= test_proxy_management()
    all_passed &= test_persona_selector()
    all_passed &= test_task_context()
    all_passed &= test_system_integration()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED - See details above")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
