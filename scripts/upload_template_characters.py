#!/usr/bin/env python3
"""Upload template character images to S3.

This script uploads all template character images from the local img/characters/
directory to S3 at the template-characters/ path.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.services.storage import upload_bytes_to_s3

# Template character mapping: local filename -> S3 key
TEMPLATE_CHARACTERS = [
    {
        "local": "character1-pose1.png",
        "s3_key": "template-characters/character1-pose1.png",
    },
    {
        "local": "character1-pose2.png",
        "s3_key": "template-characters/character1-pose2.png",
    },
    {
        "local": "character2-pose1.png",
        "s3_key": "template-characters/character2-pose1.png",
    },
    {
        "local": "character2-pose2.png",
        "s3_key": "template-characters/character2-pose2.png",
    },
    {
        "local": "character3-pose1.png",
        "s3_key": "template-characters/character3-pose1.png",
    },
    {
        "local": "character3-pose2.png",
        "s3_key": "template-characters/character3-pose2.png",
    },
    {
        "local": "character4-pose1.png",
        "s3_key": "template-characters/character4-pose1.png",
    },
    {
        "local": "character4-pose2.png",
        "s3_key": "template-characters/character4-pose2.png",
    },
]


def main():
    """Upload all template character images to S3."""
    settings = get_settings()
    img_dir = Path(__file__).parent.parent / "img" / "characters"
    
    if not img_dir.exists():
        print(f"Error: Image directory not found: {img_dir}")
        sys.exit(1)
    
    print(f"Uploading template character images to S3 bucket: {settings.s3_bucket_name}")
    print(f"Source directory: {img_dir}\n")
    
    uploaded = 0
    failed = 0
    
    for char_info in TEMPLATE_CHARACTERS:
        local_file = img_dir / char_info["local"]
        s3_key = char_info["s3_key"]
        
        if not local_file.exists():
            print(f"⚠️  Skipping {char_info['local']}: file not found")
            failed += 1
            continue
        
        try:
            # Read image bytes
            with open(local_file, "rb") as f:
                image_bytes = f.read()
            
            # Upload to S3
            upload_bytes_to_s3(
                bucket_name=settings.s3_bucket_name,
                key=s3_key,
                data=image_bytes,
                content_type="image/png",
            )
            
            print(f"✅ Uploaded {char_info['local']} -> {s3_key}")
            uploaded += 1
        except Exception as e:
            print(f"❌ Failed to upload {char_info['local']}: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Upload complete: {uploaded} succeeded, {failed} failed")
    print(f"{'='*60}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

