#!/usr/bin/env python3
"""
File Summarizer Script

This script processes chunked JSON files and extracts their content for summarization.
It's part of a local RAG workflow to handle large content files efficiently.
"""

import os
import json
import argparse


def summarize_chunk(input_file, output_dir):
    """
    Extract content from a JSON chunk file and save as a summary.

    Args:
        input_file (str): Path to the input JSON chunk file
        output_dir (str): Directory to save the summary output

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.basename(input_file)
        output_file = os.path.join(output_dir, f"summary_{base_name}")

        with open(input_file, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)

        content = chunk_data.get('content')
        if content is None:
            print(f"⚠ Error: 'content' field missing in {input_file}")
            return False

        chunk_id = chunk_data.get('chunk_id', 'unknown')
        source_file = chunk_data.get('file', 'unknown')
        chunk_id_str = chunk_data.get('id', 'unknown')

        lines = content.strip().splitlines()
        preview = "\n".join(lines[:20])              # first 20 lines
        preview = preview.lstrip("{` ")              # strip leading { or ``` if present

        plain_text_summary = (
            f"### Chunk {chunk_id} — {os.path.basename(source_file)}\n\n"
            f"{preview}\n\n…"
        )

        summary_data = {
            "source_file": input_file,
            "summary": plain_text_summary
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)

        print(f"✓ Summary created: {output_file}")
        return True

    except Exception as e:
        print(f"⚠ Error processing {input_file}: {e}")
        return False


def process_directory(input_dir, output_dir, verbose=False):
    """
    Process all JSON files in a directory.

    Args:
        input_dir (str): Directory containing JSON chunk files
        output_dir (str): Directory to save summary files
        verbose (bool): Whether to print verbose output

    Returns:
        int: Number of successfully processed files
    """
    if verbose:
        print(f"Processing directory: {input_dir}")
        print(f"Output directory: {output_dir}")

    if not os.path.isdir(input_dir):
        print(f"⚠ Input directory does not exist: {input_dir}")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success_count = 0
    file_count = 0

    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('.json'):
            file_count += 1
            input_file = os.path.join(input_dir, filename)
            if summarize_chunk(input_file, output_dir):
                success_count += 1

    if verbose:
        print("\nSummary Generation Complete")
        print(f"Processed {file_count} files")
        print(f"Successfully summarized {success_count} files")

    return success_count


def main():
    parser = argparse.ArgumentParser(
        description='Generate summaries from JSON chunk files'
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing chunked JSON files')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory to save summaries')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    args = parser.parse_args()

    process_directory(args.input_dir, args.output_dir, args.verbose)


if __name__ == '__main__':
    main()
