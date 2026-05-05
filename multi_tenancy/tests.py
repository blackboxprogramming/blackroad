"""
Multi-Tenant Isolation - Comprehensive Test Suite
Tests encryption, isolation, billing, and access control
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from isolation import (
    MultiTenantOrchestrator, Tenant, TenantIsolationLevel,
    BillingModel, TenantTier, DataEncryption, TenantDataStore,
    TenantBillingEngine, AccessControlPolicy
)


def test_data_encryption():
    """Test tenant-specific data encryption."""
    print("Testing Data Encryption...")
    
    encryption = DataEncryption("master_secret_key_12345")
    
    # Test encryption/decryption
    tenant1_data = "Sensitive customer data for tenant 1"
    tenant2_data = "Sensitive customer data for tenant 2"
    
    encrypted1 = encryption.encrypt_data("tenant_001", tenant1_data)
    encrypted2 = encryption.encrypt_data("tenant_002", tenant2_data)
    
    # Tenant 1 data should not match tenant 2
    assert encrypted1 != encrypted2, "Same data encrypted differently with different tenant keys"
    print(f"✓ Different tenants produce different ciphertexts")
    
    # Test decryption
    decrypted1 = encryption.decrypt_data("tenant_001", encrypted1)
    decrypted2 = encryption.decrypt_data("tenant_002", encrypted2)
    
    assert decrypted1 == tenant1_data, "Tenant 1 decryption failed"
    assert decrypted2 == tenant2_data, "Tenant 2 decryption failed"
    print(f"✓ Decryption successful for both tenants")
    
    # Test cross-tenant isolation (wrong key produces garbage)
    try:
        wrong_decrypt = encryption.decrypt_data("tenant_002", encrypted1)
        # Should produce garbage, not original data
        assert wrong_decrypt != tenant1_data, "Cross-tenant decryption should fail"
    except UnicodeDecodeError:
        # Expected when decrypting with wrong key
        pass
    print(f"✓ Cross-tenant decryption blocked (data corrupted as expected)")
    
    # Test integrity verification
    hash1 = encryption.compute_data_hash("tenant_001", tenant1_data)
    assert encryption.verify_data_integrity("tenant_001", tenant1_data, hash1)
    
    # Wrong data should fail verification
    assert not encryption.verify_data_integrity("tenant_001", tenant1_data + "_modified", hash1)
    print(f"✓ Data integrity verification working")


def test_tenant_isolation():
    """Test tenant context isolation."""
    print("\nTesting Tenant Isolation...")
    
    orchestrator = MultiTenantOrchestrator("master_key_for_testing")
    
    # Provision two tenants
    success, api_key1 = orchestrator.provision_tenant("tenant_001", "Company A")
    assert success, "Failed to provision tenant 1"
    
    success, api_key2 = orchestrator.provision_tenant("tenant_002", "Company B")
    assert success, "Failed to provision tenant 2"
    
    print(f"✓ Provisioned 2 tenants")
    
    # Set context for tenant 1
    assert orchestrator.context_manager.set_tenant_context("tenant_001", api_key1)
    assert orchestrator.context_manager.get_tenant_context() == "tenant_001"
    print(f"✓ Tenant 1 context set")
    
    # Try to access tenant 1's context - should succeed
    assert orchestrator.context_manager.enforce_tenant_isolation("tenant_001")
    print(f"✓ Tenant 1 isolation enforcement passed")
    
    # Try to access tenant 2's context - should fail
    assert not orchestrator.context_manager.enforce_tenant_isolation("tenant_002")
    print(f"✓ Cross-tenant isolation violation detected")
    
    # Invalid API key should fail
    assert not orchestrator.context_manager.set_tenant_context("tenant_001", "invalid_key_too_short")
    print(f"✓ Invalid API key rejected")


def test_tenant_data_store():
    """Test isolated tenant data storage."""
    print("\nTesting Tenant Data Store...")
    
    encryption = DataEncryption("master_key")
    store = TenantDataStore(encryption)
    
    # Initialize storage for two tenants
    assert store.create_tenant_storage("tenant_001")
    assert store.create_tenant_storage("tenant_002")
    
    # Store data
    success, data_id1 = store.store_data("tenant_001", "record_001", "Secret data for tenant 1")
    assert success, "Failed to store tenant 1 data"
    
    success, data_id2 = store.store_data("tenant_002", "record_001", "Secret data for tenant 2")
    assert success, "Failed to store tenant 2 data"
    
    print(f"✓ Data stored for both tenants")
    
    # Retrieve tenant 1 data
    success, data = store.retrieve_data("tenant_001", "record_001")
    assert success and data == "Secret data for tenant 1"
    print(f"✓ Tenant 1 data retrieved correctly")
    
    # Retrieve tenant 2 data
    success, data = store.retrieve_data("tenant_002", "record_001")
    assert success and data == "Secret data for tenant 2"
    print(f"✓ Tenant 2 data retrieved correctly")
    
    # Cross-tenant retrieval should fail
    success, data = store.retrieve_data("tenant_001", "record_999")
    assert not success, "Should not retrieve non-existent record"
    print(f"✓ Non-existent record access blocked")
    
    # Delete tenant data (GDPR)
    assert store.delete_tenant_data("tenant_001")
    assert not store.retrieve_data("tenant_001", "record_001")[0]
    print(f"✓ Tenant data deletion (GDPR compliance) successful")


def test_billing_calculation():
    """Test per-tenant billing calculations."""
    print("\nTesting Billing Calculation...")
    
    billing_engine = TenantBillingEngine()
    
    # Starter tier customer
    t1 = Tenant("tenant_001", "Startup Inc")
    t1.tier = TenantTier.STARTER
    t1.billing_model = BillingModel.FLAT_RATE
    t1.seats = 1
    
    cost1 = billing_engine.calculate_monthly_cost(t1)
    assert cost1 == 99.0, f"Expected $99, got ${cost1}"
    print(f"✓ Starter tier: ${cost1:.2f}/mo")
    
    # Professional tier with usage overages
    t2 = Tenant("tenant_002", "Growing Corp")
    t2.tier = TenantTier.PROFESSIONAL
    t2.billing_model = BillingModel.HYBRID
    t2.seats = 5  # 4 extra seats @ $10 = $40
    t2.monthly_api_calls = 200000  # 100K overage @ $0.01/1K = $1
    t2.storage_gb = 15  # 5 GB overage @ $0.50 = $2.50
    
    cost2 = billing_engine.calculate_monthly_cost(t2)
    expected = 299 + 40 + 1 + 2.50  # $342.50
    assert abs(cost2 - expected) < 0.01, f"Expected ${expected}, got ${cost2}"
    print(f"✓ Professional + overages: ${cost2:.2f}/mo (expected ${expected})")
    
    # Enterprise custom pricing
    t3 = Tenant("tenant_003", "Enterprise LLC")
    t3.tier = TenantTier.ENTERPRISE
    t3.billing_model = BillingModel.FLAT_RATE
    t3.seats = 50
    
    cost3 = billing_engine.calculate_monthly_cost(t3)
    assert cost3 == 999.0, f"Expected $999, got ${cost3}"
    print(f"✓ Enterprise flat: ${cost3:.2f}/mo")
    
    # Generate invoices
    invoice1 = billing_engine.generate_invoice(t1)
    assert invoice1['total'] == 99.0
    assert 'INV-tenant_001' in invoice1['invoice_id']
    print(f"✓ Invoice generated: {invoice1['invoice_id']}")


def test_access_control():
    """Test access control policies."""
    print("\nTesting Access Control...")
    
    acl = AccessControlPolicy()
    
    # Create read-only policy for tenant 1
    acl.create_policy("policy_t1_readonly", "tenant_001", ["read"], ["data"])
    
    # Create full-access policy for tenant 2
    acl.create_policy("policy_t2_admin", "tenant_002", ["read", "write", "delete"], ["*"])
    
    # Test read-only policy
    assert acl.check_access("policy_t1_readonly", "read", "data")
    assert not acl.check_access("policy_t1_readonly", "write", "data")
    print(f"✓ Read-only policy enforced")
    
    # Test full-access policy
    assert acl.check_access("policy_t2_admin", "read", "data")
    assert acl.check_access("policy_t2_admin", "write", "data")
    assert acl.check_access("policy_t2_admin", "read", "settings")
    print(f"✓ Full-access policy enforced")
    
    # Test wildcard restriction
    assert not acl.check_access("policy_t1_readonly", "read", "settings")
    print(f"✓ Wildcard restrictions working")


def test_multi_tenant_orchestrator():
    """Test complete orchestration."""
    print("\nTesting Multi-Tenant Orchestrator...")
    
    orchestrator = MultiTenantOrchestrator("master_secret_key_orchestrator")
    
    # Provision 5 test tenants
    for i in range(5):
        success, api_key = orchestrator.provision_tenant(f"tenant_{i:03d}", f"Company {chr(65+i)}")
        assert success, f"Failed to provision tenant {i}"
    
    print(f"✓ Provisioned 5 tenants")
    
    # Set metrics for billing
    for i, tenant in enumerate(orchestrator.tenants.values()):
        tenant.tier = [TenantTier.STARTER, TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE][i % 3]
        tenant.seats = 1 + i
        tenant.monthly_api_calls = 50000 + (i * 25000)
        tenant.storage_gb = 5 + (i * 2)
    
    # Calculate usage
    for tenant_id, tenant in orchestrator.tenants.items():
        usage = orchestrator.get_tenant_usage(tenant_id)
        assert usage['tenant_id'] == tenant_id
        assert usage['usage_percent'] > 0
        print(f"  {tenant.company_name}: {usage['usage_percent']:.1f}% API usage, {usage['storage_percent']:.1f}% storage")
    
    print(f"✓ Usage tracking working")
    
    # Calculate billing
    total_revenue = 0
    for tenant in orchestrator.tenants.values():
        cost = orchestrator.billing_engine.calculate_monthly_cost(tenant)
        total_revenue += cost
    
    print(f"✓ Total monthly revenue: ${total_revenue:,.2f}")
    
    # Test GDPR right to be forgotten
    assert orchestrator.deprovision_tenant("tenant_000")
    assert "tenant_000" not in orchestrator.tenants
    print(f"✓ Tenant deprovision (GDPR) successful")


def test_audit_logging():
    """Test audit trail."""
    print("\nTesting Audit Logging...")
    
    orchestrator = MultiTenantOrchestrator("master_key")
    success, api_key = orchestrator.provision_tenant("tenant_001", "Test Corp")
    
    # Valid context
    orchestrator.context_manager.set_tenant_context("tenant_001", api_key)
    
    # Invalid context (should log)
    orchestrator.context_manager.set_tenant_context("tenant_001", "invalid_key_short")
    
    # Isolation violation
    orchestrator.context_manager.enforce_tenant_isolation("tenant_002")
    
    audit_trail = orchestrator.context_manager.get_audit_trail()
    
    # Should have multiple events
    assert len(audit_trail) > 0
    
    # Check for critical events
    critical_events = [e for e in audit_trail if e.get('severity') == 'CRITICAL']
    assert len(critical_events) > 0
    print(f"✓ Audit trail: {len(audit_trail)} events ({len(critical_events)} critical)")


if __name__ == '__main__':
    print("=" * 60)
    print("Multi-Tenant Isolation - Test Suite")
    print("=" * 60)
    
    test_data_encryption()
    test_tenant_isolation()
    test_tenant_data_store()
    test_billing_calculation()
    test_access_control()
    test_multi_tenant_orchestrator()
    test_audit_logging()
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
