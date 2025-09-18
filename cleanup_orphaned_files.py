#!/usr/bin/env python3
"""
Manual cleanup script for orphaned OpenAI files.
Run this to delete old test files that weren't tracked by sessions.
"""

import os
from openai import OpenAI

def main():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("=== OpenAI Files Cleanup ===")
    try:
        # List all files
        all_files = client.files.list()
        print(f"Total files in account: {len(all_files.data)}")
        
        # Show files and ask for confirmation
        print("\nFiles to potentially delete:")
        for i, file_obj in enumerate(all_files.data, 1):
            print(f"{i:2d}. {file_obj.id}: {file_obj.filename} ({file_obj.bytes} bytes)")
        
        print(f"\nFound {len(all_files.data)} files")
        
        # Ask for confirmation
        response = input("\nDelete ALL files? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
        
        # Delete all files
        deleted_count = 0
        for file_obj in all_files.data:
            try:
                client.files.delete(file_obj.id)
                print(f"✓ Deleted: {file_obj.filename} ({file_obj.id})")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {file_obj.filename}: {e}")
        
        print(f"\nCleanup complete: {deleted_count}/{len(all_files.data)} files deleted")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()