
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.append("/home/kali/Desktop/$$$/kali-mcp-toolkit/python")

from execution_layer.types import EvidenceBundle, SafeAction, SafeActionType
from execution_layer.manifest import ManifestGenerator

def verify_manifest_logic():
    print("Verifying Manifest Logic with Failure Counts...")
    
    # 1. Create dummy evidence bundle with failure_count
    bundle = EvidenceBundle(
        bundle_id="test_bundle",
        execution_id="test_exec",
        failure_count=3,
    ).finalize()
    
    print(f"Bundle Hash: {bundle.bundle_hash}")
    
    # 2. Generate manifest
    generator = ManifestGenerator()
    manifest = generator.generate(
        execution_id="test_exec",
        evidence_bundle=bundle,
        actions=[],
    )
    
    print(f"Manifest Hash: {manifest.manifest_hash}")
    print(f"Manifest Failure Count: {manifest.failure_count}")
    
    assert manifest.failure_count == 3, "Failure count not propagated to manifest"
    
    # 3. Verify chain
    try:
        generator.verify_chain(manifest, bundle)
        print("✅ Chain Verified Successfully")
    except Exception as e:
        print(f"❌ Chain Verification Failed: {e}")
        sys.exit(1)
        
    # 4. Verify serialization
    data = manifest.to_dict()
    assert data["failure_count"] == 3, "Failure count missing from serialized data"
    print("✅ Serialization Verified")

if __name__ == "__main__":
    verify_manifest_logic()
