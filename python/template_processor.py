#!/usr/bin/env python3
import argparse
import re
import os

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def process_template(template_path, output_path, context_vars):
    template_content = read_file(template_path)
    
    # Process each context variable
    for var_name, file_path in context_vars.items():
        file_content = read_file(file_path)
        # Replace {{var_name}} with file_content
        template_content = template_content.replace(f"{{{{{var_name}}}}}", file_content)
    
    # Write to output file
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as file:
            file.write(template_content)
        print(f"Output written to {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Process a template with context variables')
    parser.add_argument('--template', required=True, help='Path to template file')
    parser.add_argument('--output', required=True, help='Path to output file')
    parser.add_argument('--context', action='append', help='Context variables in format name=file_path')
    
    args = parser.parse_args()
    
    # Parse context variables
    context_vars = {}
    if args.context:
        for context_arg in args.context:
            var_name, file_path = context_arg.split('=', 1)
            context_vars[var_name] = file_path
    
    process_template(args.template, args.output, context_vars)

if __name__ == "__main__":
    main()
