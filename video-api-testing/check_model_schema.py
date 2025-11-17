#!/usr/bin/env python3
"""
Check a Replicate model's schema to see what parameters it accepts and their defaults.
"""

import argparse
import json
import os
import sys

import replicate
from dotenv import load_dotenv

load_dotenv()


def get_model_schema(model_name: str):
    """Get the OpenAPI schema for a Replicate model."""
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found in environment")
        sys.exit(1)
    
    try:
        client = replicate.Client(api_token=api_token)
        model = client.models.get(model_name)
        version = model.latest_version
        
        schema = version.openapi_schema
        return schema
    except Exception as e:
        print(f"❌ Error getting model schema: {e}")
        return None


def print_schema_info(schema: dict, model_name: str):
    """Print formatted schema information."""
    if not schema:
        return
    
    print(f"\n📋 Model: {model_name}\n")
    
    # Get input schema
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    
    # Find the input schema (usually named like "Input" or similar)
    input_schema = None
    for schema_name, schema_def in schemas.items():
        if "input" in schema_name.lower() or "Input" in schema_name:
            input_schema = schema_def
            break
    
    if not input_schema:
        # Try to find it in the paths
        paths = schema.get("paths", {})
        for path, methods in paths.items():
            if "post" in methods:
                post_method = methods["post"]
                request_body = post_method.get("requestBody", {})
                content = request_body.get("content", {})
                json_content = content.get("application/json", {})
                input_schema = json_content.get("schema", {})
                break
    
    if input_schema and "properties" in input_schema:
        properties = input_schema["properties"]
        required = input_schema.get("required", [])
        
        print("📥 Input Parameters:\n")
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "unknown")
            default = param_info.get("default", None)
            description = param_info.get("description", "")
            is_required = param_name in required
            
            req_marker = " (required)" if is_required else ""
            default_str = f" (default: {default})" if default is not None else ""
            
            print(f"  {param_name}: {param_type}{req_marker}{default_str}")
            if description:
                print(f"    {description}")
            print()
    else:
        print("⚠️  Could not find input schema. Showing raw schema structure:\n")
        print(json.dumps(schema, indent=2)[:1000] + "...")


def main():
    parser = argparse.ArgumentParser(
        description="Check a Replicate model's schema and parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_model_schema.py anotherjesse/zeroscope-v2-xl
  python check_model_schema.py minimax/hailuo-2.3
        """
    )
    
    parser.add_argument("model", help="Replicate model identifier (e.g., anotherjesse/zeroscope-v2-xl)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON schema")
    
    args = parser.parse_args()
    
    schema = get_model_schema(args.model)
    
    if not schema:
        sys.exit(1)
    
    if args.json:
        print(json.dumps(schema, indent=2))
    else:
        print_schema_info(schema, args.model)


if __name__ == "__main__":
    main()

