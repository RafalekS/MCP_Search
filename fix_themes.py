#!/usr/bin/env python3
"""Fix theme files by removing unsupported top_fg_color property"""

import json
import glob

def fix_theme(filepath):
    """Remove top_fg_color from a theme file"""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Remove top_fg_color from CTkFrame if it exists
    if 'CTkFrame' in data and 'top_fg_color' in data['CTkFrame']:
        del data['CTkFrame']['top_fg_color']
        print(f"Fixed: {filepath}")

        # Write back with proper formatting
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

# Fix all theme files
fixed = 0
for theme_file in glob.glob('themes/*.json'):
    if fix_theme(theme_file):
        fixed += 1

print(f"\nFixed {fixed} theme files")
