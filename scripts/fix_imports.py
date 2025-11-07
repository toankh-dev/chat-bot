#!/usr/bin/env python3
"""
Script to replace all 'src.' imports with relative imports.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace 'from src.' with 'from '
        content = re.sub(r'from src\.', 'from ', content)
        
        # Replace 'import src.' with 'import '
        content = re.sub(r'import src\.', 'import ', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def fix_all_imports():
    """Fix imports in all Python files in src directory."""
    src_dir = Path(__file__).parent.parent / 'src'
    python_files = list(src_dir.rglob('*.py'))
    
    fixed_count = 0
    total_count = len(python_files)
    
    print(f"Processing {total_count} Python files...")
    
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Complete! Fixed {fixed_count} out of {total_count} files.")

if __name__ == "__main__":
    fix_all_imports()