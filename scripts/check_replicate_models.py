#!/usr/bin/env python3
"""Check and verify Replicate video models.

Combines model verification and listing functionality.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import replicate  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.services.video_generation import VIDEO_MODEL  # noqa: E402

# Common text-to-video models to check
MODELS_TO_CHECK = [
    "anotherjesse/zeroscope-v2-xl",  # Current model (~$0.035/run)
    "lucataco/animate-diff",  # AnimateDiff
]


def verify_current_model():
    """Verify the current video model exists and is accessible."""
    settings = get_settings()
    
    if not settings.replicate_api_token:
        print("❌ REPLICATE_API_TOKEN not configured in .env")
        print("   Add: REPLICATE_API_TOKEN=your_token_here")
        return False
    
    try:
        client = replicate.Client(api_token=settings.replicate_api_token)
        
        print(f"🔍 Checking current model: {VIDEO_MODEL}")
        print("-" * 60)
        
        try:
            model = client.models.get(VIDEO_MODEL)
            print(f"✅ Model found: {model.name}")
            print(f"   Owner: {model.owner}")
            print(f"   Description: {model.description[:100] if model.description else 'N/A'}...")
            
            if model.latest_version:
                version = model.latest_version
                print(f"   Latest version: {version.id}")
                print(f"   Created: {version.created_at}")
                
                # Check input schema
                if hasattr(version, 'openapi_schema') and version.openapi_schema:
                    inputs = version.openapi_schema.get('components', {}).get('schemas', {}).get('Input', {}).get('properties', {})
                    if inputs:
                        print(f"\n   Input parameters:")
                        for param, details in list(inputs.items())[:10]:  # Show first 10
                            param_type = details.get('type', 'unknown')
                            param_desc = details.get('description', '')
                            print(f"     - {param}: {param_type} - {param_desc[:50]}")
                
                return True
            else:
                print("❌ Model has no versions")
                return False
                
        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                print(f"❌ Model not found: {VIDEO_MODEL}")
                print("\n💡 Try searching for text-to-video models:")
                print("   Visit: https://replicate.com/explore?query=text+to+video")
            else:
                print(f"❌ Error: {error_str}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying model: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_alternative_models():
    """List alternative text-to-video models."""
    settings = get_settings()
    if not settings.replicate_api_token:
        print("❌ REPLICATE_API_TOKEN not configured")
        return
    
    print("\n🔍 Checking alternative models...")
    print("=" * 60)
    
    results = []
    for model_name in MODELS_TO_CHECK:
        if model_name == VIDEO_MODEL:
            continue  # Skip current model
        
        try:
            client = replicate.Client(api_token=settings.replicate_api_token)
            model = client.models.get(model_name)
            
            if model.latest_version:
                version = model.latest_version
                results.append({
                    "name": model_name,
                    "owner": model.owner,
                    "description": model.description[:80] if model.description else "N/A",
                    "version": version.id[:20] + "...",
                })
        except Exception:
            pass  # Model doesn't exist or error
    
    if results:
        print("\n✅ Alternative models:")
        for r in results:
            print(f"  • {r['name']}")
            print(f"    Owner: {r['owner']}")
            print(f"    Description: {r['description']}")
            print(f"    Version: {r['version']}")
            print()
    else:
        print("\n⚠️  No alternative models found")
    
    print("💡 Check Replicate pricing: https://replicate.com/pricing")
    print("   Current model (Zeroscope v2 XL): ~$0.035 per run")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Replicate video models")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List alternative models in addition to verifying current model",
    )
    args = parser.parse_args()
    
    success = verify_current_model()
    
    if args.list:
        list_alternative_models()
    
    sys.exit(0 if success else 1)

