"""
Helper script to lookup Factorio API documentation.

Usage:
    cd /d D:\factorio_llm
    conda activate factorio
    python scripts/api_lookup.py SurfaceIdentification
    python scripts/api_lookup.py LuaForce get_item_production_statistics
"""

import json
import sys

API_PATH = r'D:\factorio_llm\api_archive\files\runtime-api.json'


def load_api():
    with open(API_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def lookup_concept(data, name):
    for concept in data.get('concepts', []):
        if concept.get('name') == name:
            return concept
    return None


def lookup_class(data, class_name, member_name=None):
    for cls in data.get('classes', []):
        if cls.get('name') == class_name:
            if member_name:
                # Look for method
                for m in cls.get('methods', []):
                    if m.get('name') == member_name:
                        return {'type': 'method', 'data': m}
                # Look for attribute
                for a in cls.get('attributes', []):
                    if a.get('name') == member_name:
                        return {'type': 'attribute', 'data': a}
                return None
            return cls
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python api_lookup.py <name> [member]")
        print("Examples:")
        print("  python api_lookup.py SurfaceIdentification")
        print("  python api_lookup.py LuaForce get_item_production_statistics")
        sys.exit(1)

    data = load_api()
    name = sys.argv[1]
    member = sys.argv[2] if len(sys.argv) > 2 else None

    # Try as concept first
    result = lookup_concept(data, name)
    if result:
        print(f"CONCEPT: {name}")
        print(json.dumps(result, indent=2))
        return

    # Try as class
    result = lookup_class(data, name, member)
    if result:
        if member:
            print(f"{result['type'].upper()}: {name}.{member}")
            print(json.dumps(result['data'], indent=2))
        else:
            print(f"CLASS: {name}")
            print(f"Methods: {[m['name'] for m in result.get('methods', [])]}")
            print(f"Attributes: {[a['name'] for a in result.get('attributes', [])]}")
        return

    print(f"Not found: {name}")


if __name__ == '__main__':
    main()
