#!/usr/bin/env python3
"""
chunk_searcher.py - Search through chunked code files using keyword matching
"""

import argparse
import os
import json
import re
from pathlib import Path
import sys

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Search through chunked code files')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for keywords in chunks')
    search_parser.add_argument('chunks_dir', help='Directory containing chunk files')
    search_parser.add_argument('query', help='Search query string')
    search_parser.add_argument('--output', help='Output file for search results (JSON)')
    search_parser.add_argument('--extensions', help='Comma-separated list of file extensions to search')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results to return')
    search_parser.add_argument('--context', type=int, default=0, help='Number of context lines before and after match')
    
    return parser.parse_args()

def load_chunks(chunks_dir, extensions=None):
    """Load all chunks from the chunks directory."""
    chunks = []
    chunks_dir = Path(chunks_dir)
    
    # Filter by extensions if specified
    if extensions:
        ext_list = extensions.split(',')
        # Make sure each extension starts with a dot
        ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
    else:
        ext_list = None
    
    # Walk through the chunks directory
    for root, _, files in os.walk(chunks_dir):
        for file in files:
            # Skip non-JSON files
            if not file.endswith('.json'):
                continue
            
            # Skip files that don't match the specified extensions
            if ext_list:
                file_path = Path(file)
                original_ext = file_path.stem.split('.')[-1]  # Assuming chunks are named like "file.py.chunk.json"
                if f'.{original_ext}' not in ext_list:
                    continue
            
            # Load the chunk
            try:
                with open(Path(root) / file, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                    chunks.append(chunk_data)
            except Exception as e:
                print(f"Error loading chunk file {file}: {e}", file=sys.stderr)
    
    return chunks

def search_chunks(chunks, query, limit=10):
    """Search for the query in the chunks."""
    # Split the query into keywords
    keywords = query.lower().split()
    
    # Define a scoring function for chunks
    def score_chunk(chunk):
        content = chunk.get('content', '').lower()
        
        # Count occurrences of each keyword
        scores = [content.count(keyword) for keyword in keywords]
        
        # If any keyword is not found, return 0
        if 0 in scores:
            return 0
        
        # Return the sum of occurrences
        return sum(scores)
    
    # Score all chunks
    scored_chunks = [(chunk, score_chunk(chunk)) for chunk in chunks]
    
    # Filter out chunks with zero score
    scored_chunks = [(chunk, score) for chunk, score in scored_chunks if score > 0]
    
    # Sort by score in descending order
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    # Return the top N chunks
    return [chunk for chunk, _ in scored_chunks[:limit]]

def highlight_matches(content, query, context=0):
    """Highlight matches in the content."""
    keywords = query.lower().split()
    lines = content.split('\n')
    result = []
    
    # Track which lines to include
    include_lines = set()
    
    # Find lines containing keywords
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in keywords):
            # Add the line and context lines
            for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                include_lines.add(j)
    
    # Create the highlighted content
    for i, line in enumerate(lines):
        if i in include_lines:
            # Highlight the keywords
            highlighted_line = line
            for keyword in keywords:
                pattern = re.compile(f'({re.escape(keyword)})', re.IGNORECASE)
                highlighted_line = pattern.sub(r'**\1**', highlighted_line)
            
            result.append(highlighted_line)
    
    return '\n'.join(result)

def search_command_handler(args):
    """Handle the search command."""
    # Load chunks
    print(f"Loading chunks from {args.chunks_dir}...")
    chunks = load_chunks(args.chunks_dir, args.extensions)
    print(f"Loaded {len(chunks)} chunks")
    
    # Search for the query
    print(f"Searching for '{args.query}'...")
    results = search_chunks(chunks, args.query, args.limit)
    print(f"Found {len(results)} matching chunks")
    
    # Highlight matches
    for chunk in results:
        chunk['highlighted_content'] = highlight_matches(chunk['content'], args.query, args.context)
    
    # Display results
    for i, chunk in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"File: {chunk.get('file_path', 'Unknown')}")
        print(f"Chunk: {chunk.get('chunk_id', 'Unknown')}")
        print("\nContent:")
        print(chunk['highlighted_content'])
    
    # Save results to file if specified
    if args.output:
        try:
            output_dir = Path(args.output).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {args.output}")
        except Exception as e:
            print(f"Error saving results to {args.output}: {e}", file=sys.stderr)
            return False
    
    return True

def main():
    """Main function."""
    args = parse_args()
    
    if args.command == 'create':
        success = create_command_handler(args)
        if not success:
            sys.exit(1)
    elif args.command == 'search':
        success = search_command_handler(args)
        if not success:
            sys.exit(1)
    else:
        print("Invalid or missing command. Use --help for usage information.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
