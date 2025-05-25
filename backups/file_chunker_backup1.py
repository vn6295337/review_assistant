#!/usr/bin/env python3
"""
File chunker for code and text documents.
Splits large files into smaller overlapping chunks for processing with LLMs.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import hashlib
import textwrap
import glob

def get_file_list(source, extensions=None):
    """Get list of files to process with directory exclusions."""
    file_list = []
    source_path = Path(source)
    
    # Directories to skip - add any large directories you want to exclude
    EXCLUDED_DIRS = {'venv', 'outputs', 'scripts', '__pycache__', '.git', 'node_modules', 'env', 'dist', 'build'}

    # Parse extensions if provided
    if extensions:
        ext_list = extensions.split(',')
        ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
    else:
        ext_list = None

    print(f"Looking for files in: {source_path.absolute()}")
    
    if source_path.is_dir():
        try:
            for root, dirs, files in os.walk(str(source_path.absolute())):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]
                
                for file in files:
                    try:
                        file_path = Path(os.path.join(root, file))
                        
                        # Skip hidden files
                        if file.startswith('.'):
                            continue
                            
                        # Apply extension filter if provided
                        if ext_list and file_path.suffix not in ext_list:
                            continue
                        
                        print(f"Found file: {file_path}")
                        file_list.append(file_path)
                    except Exception as e:
                        print(f"Error processing file {file}: {str(e)}", file=sys.stderr)
        except Exception as e:
            print(f"Error walking directory {source_path}: {str(e)}", file=sys.stderr)
            sys.exit(1)

    elif source_path.is_file():
        if ext_list and source_path.suffix not in ext_list:
            return []
        file_list.append(source_path)
    else:
        print(f"Error: Source '{source}' is not a valid file or directory", file=sys.stderr)
        sys.exit(1)
        
    print(f"Found {len(file_list)} files to process")
    for f in file_list:
        print(f"  {f}")
        
    return file_list

def chunk_file(file_path, max_chunk_size=1000, overlap=100):
    """
    Break a file into overlapping chunks with improved memory efficiency.
    Uses a streaming approach to avoid loading the entire file into memory.
    """
    try:
        # Generate a unique ID for the file
        file_id = hashlib.md5(str(file_path).encode()).hexdigest()
        
        chunks = []
        
        # Process the file in a streaming fashion
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = ""
            chunk_id = 0
            
            # Read the file line by line to avoid loading everything into memory
            for line in f:
                content += line
                
                # Once we've accumulated enough content, create a chunk
                if len(content.split()) >= max_chunk_size:
                    # Create the chunk
                    chunk = {
                        "id": f"{file_id}_{chunk_id}",
                        "file": str(file_path),
                        "content": content,
                        "chunk_id": chunk_id
                    }
                    chunks.append(chunk)
                    
                    # Keep overlap for next chunk
                    content = textwrap.dedent('\n'.join(content.split('\n')[-overlap:]) if overlap > 0 else "")
                    chunk_id += 1
            
            # Add the final chunk if there's any content left
            if content.strip():
                chunk = {
                    "id": f"{file_id}_{chunk_id}",
                    "file": str(file_path),
                    "content": content,
                    "chunk_id": chunk_id
                }
                chunks.append(chunk)
        
        # Print success message
        print(f"Successfully chunked {file_path} into {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
        return []

def write_chunks(chunks, output_dir):
    """Write chunks to JSON files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for chunk in chunks:
        chunk_file = output_path / f"{chunk['id']}.json"
        
        # Write chunks one at a time to minimize memory usage
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Chunk files into smaller pieces.')
    parser.add_argument('source', help='Source file or directory')
    parser.add_argument('--output', required=True, help='Output directory for chunks')
    parser.add_argument('--extensions', help='Comma-separated list of file extensions to process')
    parser.add_argument('--chunk-size', type=int, default=500, help='Maximum chunk size in words')
    parser.add_argument('--overlap', type=int, default=50, help='Overlap between chunks in words')
    parser.add_argument('--verbose', action='store_true', help='Print verbose output')
    
    args = parser.parse_args()
    
    print(f"Starting file chunker...")
    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print(f"Extensions: {args.extensions}")
    print(f"Chunk size: {args.chunk_size}")
    print(f"Overlap: {args.overlap}")
    
    # Get files to process
    file_list = get_file_list(args.source, args.extensions)
    
    if not file_list:
        print("No files found to process.", file=sys.stderr)
        sys.exit(1)
    
    # Process files one by one to save memory
    for i, file_path in enumerate(file_list):
        print(f"Processing {i+1}/{len(file_list)}: {file_path}...")
        
        try:
            # Process each file individually to minimize memory usage
            chunks = chunk_file(file_path, args.chunk_size, args.overlap)
            
            if chunks:
                # Write chunks to disk immediately after processing each file
                write_chunks(chunks, args.output)
                print(f"Written {len(chunks)} chunks to {args.output}")
                # Clear chunks to free memory
                chunks = None
            else:
                print(f"No chunks generated for {file_path}")
        except Exception as e:
            print(f"\nError processing {file_path}: {str(e)}", file=sys.stderr)
    
    print("\nDone chunking files.")

if __name__ == '__main__':
    main()
