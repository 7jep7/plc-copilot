#!/usr/bin/env python3
"""
Check what files are currently in our OpenAI vector store and file storage.
"""

import os
from openai import OpenAI

def main():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    vector_store_id = "vs_68cba48e219c8191acc9d25d32cf8130"
    
    print("=== OpenAI Vector Store Files ===")
    try:
        # Try different ways to access vector stores
        try:
            # Try the newer API
            vector_store = client.beta.vector_stores.retrieve(vector_store_id)
            print(f"Vector Store: {vector_store.name}")
            print(f"File counts: {vector_store.file_counts}")
            
            # List files in vector store
            vector_files = client.beta.vector_stores.files.list(vector_store_id)
            print(f"Files in vector store ({len(vector_files.data)}):")
            for vf in vector_files.data:
                print(f"  - {vf.id} (status: {vf.status})")
            print()
            
        except AttributeError:
            print("Vector store API not available in this client version")
        except Exception as vs_error:
            print(f"Vector store error: {vs_error}")
                
    except Exception as e:
        print(f"Error accessing vector store: {e}")
    
    print("\n=== All OpenAI Files ===")
    try:
        # List all files in account
        all_files = client.files.list()
        print(f"Total files in account: {len(all_files.data)}")
        for file_obj in all_files.data:
            print(f"  - {file_obj.id}: {file_obj.filename} ({file_obj.purpose}, {file_obj.bytes} bytes)")
    except Exception as e:
        print(f"Error listing all files: {e}")

if __name__ == "__main__":
    main()