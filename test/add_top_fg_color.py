#!/usr/bin/env python3
"""Add top_fg_color to all theme JSON files for CustomTkinter compatibility"""
import json
import os
from pathlib import Path

def add_top_fg_color_to_theme(theme_path):
    """Add top_fg_color to a theme file if it's missing"""
    with open(theme_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check if CTkFrame exists and needs top_fg_color
    if 'CTkFrame' in data:
        if 'top_fg_color' not in data['CTkFrame']:
            # Use the same value as fg_color or set to transparent
            if 'fg_color' in data['CTkFrame']:
                data['CTkFrame']['top_fg_color'] = data['CTkFrame']['fg_color']
            else:
                data['CTkFrame']['top_fg_color'] = ["transparent", "transparent"]

            # Write back to file
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return True
    return False

def main():
    themes_dir = Path('themes')
    if not themes_dir.exists():
        print(f"Themes directory not found: {themes_dir}")
        return

    count = 0
    for theme_file in themes_dir.glob('*.json'):
        if add_top_fg_color_to_theme(theme_file):
            print(f"Added top_fg_color to {theme_file.name}")
            count += 1
        else:
            print(f"Skipped {theme_file.name} (already has top_fg_color or no CTkFrame)")

    print(f"\nProcessed {count} theme files")

if __name__ == '__main__':
    main()
