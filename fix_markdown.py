#!/usr/bin/env python3
"""
Markdown Lint Fixer for ZeroToShip Project
==========================================

This script automatically fixes common markdownlint errors in all .md files
throughout the project.
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Tuple

def fix_markdown_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Fix markdownlint errors in a single file.
    
    Returns:
        Tuple of (file_was_modified, list_of_fixes_applied)
    """
    fixes_applied = []
    was_modified = False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix 1: Add blank lines after headings
        content = re.sub(r'^(#{1,6}\s+.*?)$\n(?!\n)', r'\1\n\n', content, flags=re.MULTILINE)
        
        # Fix 2: Add blank lines before lists
        content = re.sub(r'([^\n])\n([-*+]\s)', r'\1\n\n\2', content)
        
        # Fix 3: Add blank lines after lists
        content = re.sub(r'([^\n])\n\n([^-\n])', r'\1\n\n\2', content)
        
        # Fix 4: Add blank lines before code blocks
        content = re.sub(r'([^\n])\n(```)', r'\1\n\n\2', content)
        
        # Fix 5: Add blank lines after code blocks
        content = re.sub(r'(```\n[^`]*```)\n([^-\n])', r'\1\n\n\2', content)
        
        # Fix 6: Add blank lines before numbered lists
        content = re.sub(r'([^\n])\n(\d+\.\s)', r'\1\n\n\2', content)
        
        # Fix 7: Add blank lines before bold/italic sections
        content = re.sub(r'([^\n])\n(\*\*[^*]+\*\*:)', r'\1\n\n\2', content)
        
        # Fix 8: Add blank lines before tables
        content = re.sub(r'([^\n])\n(\|.*\|)', r'\1\n\n\2', content)
        
        # Fix 9: Add blank lines after tables
        content = re.sub(r'(\|.*\|)\n([^|\n])', r'\1\n\n\2', content)
        
        # Fix 10: Add blank lines before horizontal rules
        content = re.sub(r'([^\n])\n(---+)', r'\1\n\n\2', content)
        
        # Fix 11: Add blank lines after horizontal rules
        content = re.sub(r'(---+)\n([^-\n])', r'\1\n\n\2', content)
        
        # Fix 12: Add blank lines before blockquotes
        content = re.sub(r'([^\n])\n(>\s)', r'\1\n\n\2', content)
        
        # Fix 13: Add blank lines after blockquotes
        content = re.sub(r'(>\s.*)\n([^>\n])', r'\1\n\n\2', content)
        
        # Fix 14: Ensure proper spacing around headers with emojis
        content = re.sub(r'^(#{1,6}\s+[^\n]*?)\n([^-\n])', r'\1\n\n\2', content, flags=re.MULTILINE)
        
        # Fix 15: Add blank lines before subsections
        content = re.sub(r'([^\n])\n(###\s)', r'\1\n\n\2', content)
        
        # Fix 16: Add blank lines before subsubsections
        content = re.sub(r'([^\n])\n(####\s)', r'\1\n\n\2', content)
        
        # Fix 17: Add blank lines before subsubsubsections
        content = re.sub(r'([^\n])\n(#####\s)', r'\1\n\n\2', content)
        
        # Fix 18: Add blank lines before subsubsubsubsections
        content = re.sub(r'([^\n])\n(######\s)', r'\1\n\n\2', content)
        
        # Fix 19: Ensure proper spacing around code blocks with language specifiers
        content = re.sub(r'([^\n])\n(```\w+)', r'\1\n\n\2', content)
        
        # Fix 20: Add blank lines before configuration sections
        content = re.sub(r'([^\n])\n(##\s+Configuration)', r'\1\n\n\2', content)
        
        # Fix 21: Add blank lines before usage sections
        content = re.sub(r'([^\n])\n(##\s+Usage)', r'\1\n\n\2', content)
        
        # Fix 22: Add blank lines before testing sections
        content = re.sub(r'([^\n])\n(##\s+Testing)', r'\1\n\n\2', content)
        
        # Fix 23: Add blank lines before deployment sections
        content = re.sub(r'([^\n])\n(##\s+Deployment)', r'\1\n\n\2', content)
        
        # Fix 24: Add blank lines before troubleshooting sections
        content = re.sub(r'([^\n])\n(##\s+Troubleshooting)', r'\1\n\n\2', content)
        
        # Fix 25: Add blank lines before contributing sections
        content = re.sub(r'([^\n])\n(##\s+Contributing)', r'\1\n\n\2', content)
        
        # Fix 26: Add blank lines before license sections
        content = re.sub(r'([^\n])\n(##\s+License)', r'\1\n\n\2', content)
        
        # Fix 27: Add blank lines before support sections
        content = re.sub(r'([^\n])\n(##\s+Support)', r'\1\n\n\2', content)
        
        # Fix 28: Add blank lines before roadmap sections
        content = re.sub(r'([^\n])\n(##\s+Roadmap)', r'\1\n\n\2', content)
        
        # Fix 29: Add blank lines before conclusion sections
        content = re.sub(r'([^\n])\n(##\s+Conclusion)', r'\1\n\n\2', content)
        
        # Fix 30: Add blank lines before architecture sections
        content = re.sub(r'([^\n])\n(##\s+Architecture)', r'\1\n\n\2', content)
        
        # Fix 31: Add blank lines before security sections
        content = re.sub(r'([^\n])\n(##\s+Security)', r'\1\n\n\2', content)
        
        # Fix 32: Add blank lines before monitoring sections
        content = re.sub(r'([^\n])\n(##\s+Monitoring)', r'\1\n\n\2', content)
        
        # Fix 33: Add blank lines before API sections
        content = re.sub(r'([^\n])\n(##\s+API)', r'\1\n\n\2', content)
        
        # Fix 34: Add blank lines before interfaces sections
        content = re.sub(r'([^\n])\n(##\s+Interfaces)', r'\1\n\n\2', content)
        
        # Fix 35: Add blank lines before implementation sections
        content = re.sub(r'([^\n])\n(##\s+Implementation)', r'\1\n\n\2', content)
        
        # Fix 36: Add blank lines before outputs sections
        content = re.sub(r'([^\n])\n(##\s+Outputs)', r'\1\n\n\2', content)
        
        # Fix 37: Add blank lines before validation sections
        content = re.sub(r'([^\n])\n(##\s+Validation)', r'\1\n\n\2', content)
        
        # Fix 38: Add blank lines before tools sections
        content = re.sub(r'([^\n])\n(##\s+Tools)', r'\1\n\n\2', content)
        
        # Fix 39: Add blank lines before integrations sections
        content = re.sub(r'([^\n])\n(##\s+Integrations)', r'\1\n\n\2', content)
        
        # Fix 40: Add blank lines before data models sections
        content = re.sub(r'([^\n])\n(##\s+Data Models)', r'\1\n\n\2', content)
        
        # Fix 41: Add blank lines before compliance sections
        content = re.sub(r'([^\n])\n(##\s+Compliance)', r'\1\n\n\2', content)
        
        # Fix 42: Add blank lines before infrastructure sections
        content = re.sub(r'([^\n])\n(##\s+Infrastructure)', r'\1\n\n\2', content)
        
        # Fix 43: Add blank lines before environment sections
        content = re.sub(r'([^\n])\n(##\s+Environment)', r'\1\n\n\2', content)
        
        # Fix 44: Add blank lines before setup sections
        content = re.sub(r'([^\n])\n(##\s+Setup)', r'\1\n\n\2', content)
        
        # Fix 45: Add blank lines before installation sections
        content = re.sub(r'([^\n])\n(##\s+Installation)', r'\1\n\n\2', content)
        
        # Fix 46: Add blank lines before prerequisites sections
        content = re.sub(r'([^\n])\n(##\s+Prerequisites)', r'\1\n\n\2', content)
        
        # Fix 47: Add blank lines before quick start sections
        content = re.sub(r'([^\n])\n(##\s+Quick Start)', r'\1\n\n\2', content)
        
        # Fix 48: Add blank lines before manual deployment sections
        content = re.sub(r'([^\n])\n(##\s+Manual Deployment)', r'\1\n\n\2', content)
        
        # Fix 49: Add blank lines before resource requirements sections
        content = re.sub(r'([^\n])\n(##\s+Resource Requirements)', r'\1\n\n\2', content)
        
        # Fix 50: Add blank lines before storage sections
        content = re.sub(r'([^\n])\n(##\s+Storage)', r'\1\n\n\2', content)
        
        # Remove multiple consecutive blank lines (keep max 2)
        content = re.sub(r'\n{3,}', r'\n\n', content)
        
        # Ensure file ends with a single newline
        content = content.rstrip() + '\n'
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            was_modified = True
            fixes_applied.append(f"Fixed markdown formatting in {file_path}")
        
    except Exception as e:
        fixes_applied.append(f"Error processing {file_path}: {str(e)}")
    
    return was_modified, fixes_applied

def find_markdown_files() -> List[str]:
    """Find all .md files in the project."""
    md_files = []
    
    # Common directories to search
    search_dirs = [
        '.',
        'docs',
        'k8s',
        'src',
        'tests',
        'scripts'
    ]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            pattern = os.path.join(search_dir, '**/*.md')
            md_files.extend(glob.glob(pattern, recursive=True))
    
    # Also check root directory
    md_files.extend(glob.glob('*.md'))
    
    # Remove duplicates and sort
    md_files = sorted(list(set(md_files)))
    
    return md_files

def main():
    """Main function to fix all markdown files."""
    print("🔧 ZeroToShip Markdown Lint Fixer")
    print("=" * 50)
    
    # Find all markdown files
    md_files = find_markdown_files()
    
    if not md_files:
        print("❌ No markdown files found in the project.")
        return
    
    print(f"📁 Found {len(md_files)} markdown files:")
    for file_path in md_files:
        print(f"   - {file_path}")
    
    print("\n🔧 Fixing markdown files...")
    
    total_fixes = 0
    modified_files = 0
    
    for file_path in md_files:
        was_modified, fixes = fix_markdown_file(file_path)
        if was_modified:
            modified_files += 1
            total_fixes += len(fixes)
            for fix in fixes:
                print(f"   ✅ {fix}")
    
    print(f"\n📊 Summary:")
    print(f"   - Files processed: {len(md_files)}")
    print(f"   - Files modified: {modified_files}")
    print(f"   - Total fixes applied: {total_fixes}")
    
    if modified_files > 0:
        print("\n✅ Markdown lint fixes completed successfully!")
    else:
        print("\n✨ All markdown files are already properly formatted!")

if __name__ == "__main__":
    main()
