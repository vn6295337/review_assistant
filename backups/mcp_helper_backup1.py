#!/usr/bin/env python3
"""
mcp_helper.py - Multi-Context Prompt Helper for generating prompts with context
"""

import argparse
import os
import json
import re
from pathlib import Path
import sys

class MultiContextPrompt:
    def __init__(self, name=None):
        self.name = name or "unnamed_prompt"
        self.template = ""
        self.variables = {}
        self.context_blocks = {}
    
    def load_template(self, template_path):
        """Load a template from a file."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
            return True
        except Exception as e:
            print(f"Error loading template from {template_path}: {e}", file=sys.stderr)
            return False
    
    def set_variable(self, key, value):
        """Set a variable for the template."""
        self.variables[key] = value
    
    def add_context_block(self, key, content):
        """Add a context block to the prompt."""
        self.context_blocks[key] = content
    
    def load_context_from_file(self, file_path, key):
        """Load context from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    # Try to load as JSON
                    data = json.load(f)
                    
                    # Check if data is a list of chunks
                    if isinstance(data, list):
                        # Concatenate content from chunks
                        content = ""
                        for i, chunk in enumerate(data):
                            if 'content' in chunk:
                                content += f"\n--- Chunk {i+1} ---\n"
                                content += chunk['content']
                                content += "\n\n"
                        
                        self.add_context_block(key, content)
                    else:
                        # Format as formatted JSON
                        self.add_context_block(key, json.dumps(data, indent=2))
                    
                except json.JSONDecodeError:
                    # If not JSON, use as raw text
                    f.seek(0)  # Reset file pointer
                    self.add_context_block(key, f.read())
            
            return True
        except Exception as e:
            print(f"Error loading context from {file_path}: {e}", file=sys.stderr)
            return False
    
    def generate(self):
        """Generate the final prompt."""
        # Start with the template
        result = self.template
        
        # Replace variables
        for key, value in self.variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)
        
        # Replace context blocks
        for key, content in self.context_blocks.items():
            result = result.replace(f"{{{{{key}}}}}", content)
        
        return result
    
    def save(self, output_path):
        """Save the prompt to a file."""
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.generate())
            
            return True
        except Exception as e:
            print(f"Error saving prompt to {output_path}: {e}", file=sys.stderr)
            return False

def parse_var_arg(var_arg):
    """Parse variable argument in the format key=value."""
    if '=' not in var_arg:
        print(f"Invalid variable format: {var_arg}. Expected format: key=value", file=sys.stderr)
        return None, None
    
    parts = var_arg.split('=', 1)
    return parts[0], parts[1]

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Multi-Context Prompt Helper')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new prompt')
    create_parser.add_argument('--name', help='Name of the prompt')
    create_parser.add_argument('--template', required=True, help='Path to the template file')
    create_parser.add_argument('--output', required=True, help='Path to save the generated prompt')
    create_parser.add_argument('--var', action='append', help='Variables in the format key=value')
    create_parser.add_argument('--context-file', nargs=2, action='append', help='Add context from file: path key')
    create_parser.add_argument('--context', nargs=2, action='append', help='Add context directly: key content')
    
    # Add context command
    add_context_parser = subparsers.add_parser('add-context', help='Add context to a prompt')
    add_context_parser.add_argument('--prompt', required=True, help='Path to the prompt file')
    add_context_parser.add_argument('--key', required=True, help='Context key')
    add_context_parser.add_argument('--content', help='Context content')
    add_context_parser.add_argument('--file', help='Path to file containing context content')
    add_context_parser.add_argument('--output', help='Path to save the updated prompt')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available templates')
    list_parser.add_argument('--dir', required=True, help='Directory containing templates')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate a prompt from template')
    generate_parser.add_argument('--template', required=True, help='Path to the template file')
    generate_parser.add_argument('--output', required=True, help='Path to save the generated prompt')
    generate_parser.add_argument('--var', action='append', help='Variables in the format key=value')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export a prompt to a file')
    export_parser.add_argument('--prompt', required=True, help='Path to the prompt file')
    export_parser.add_argument('--output', required=True, help='Path to save the exported prompt')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import a prompt from a file')
    import_parser.add_argument('--file', required=True, help='Path to the file to import')
    import_parser.add_argument('--output', required=True, help='Path to save the imported prompt')
    
    return parser.parse_args()

def create_command_handler(args):
    """Handle the create command."""
    # Create a new prompt
    prompt = MultiContextPrompt(args.name)
    
    # Load the template
    if not prompt.load_template(args.template):
        print(f"Failed to load template from {args.template}", file=sys.stderr)
        return False
    
    # Set variables
    if args.var:
        for var_arg in args.var:
            key, value = parse_var_arg(var_arg)
            if key is not None:
                prompt.set_variable(key, value)
    
    # Add context from files
    if args.context_file:
        for file_path, key in args.context_file:
            if not prompt.load_context_from_file(file_path, key):
                print(f"Failed to load context from {file_path}", file=sys.stderr)
                return False
    
    # Add direct context
    if args.context:
        for key, content in args.context:
            prompt.add_context_block(key, content)
    
    # Save the prompt
    if not prompt.save(args.output):
        print(f"Failed to save prompt to {args.output}", file=sys.stderr)
        return False
    
    print(f"Prompt '{args.name}' created and saved to {args.output}")
    return True

def add_context_command_handler(args):
    """Handle the add-context command."""
    # Load the existing prompt
    with open(args.prompt, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a new prompt
    prompt = MultiContextPrompt()
    prompt.template = content
    
    # Add content from file or direct content
    if args.file:
        if not prompt.load_context_from_file(args.file, args.key):
            print(f"Failed to load context from {args.file}", file=sys.stderr)
            return False
    elif args.content:
        prompt.add_context_block(args.key, args.content)
    else:
        print("Either --file or --content must be specified", file=sys.stderr)
        return False
    
    # Save the prompt
    output_path = args.output or args.prompt
    if not prompt.save(output_path):
        print(f"Failed to save prompt to {output_path}", file=sys.stderr)
        return False
    
    print(f"Context '{args.key}' added to prompt and saved to {output_path}")
    return True

def list_command_handler(args):
    """Handle the list command."""
    template_dir = Path(args.dir)
    
    if not template_dir.exists() or not template_dir.is_dir():
        print(f"Template directory {args.dir} does not exist or is not a directory", file=sys.stderr)
        return False
    
    templates = list(template_dir.glob('*.md'))
    
    print(f"Found {len(templates)} templates in {args.dir}:")
    for template in templates:
        print(f"- {template.name}")
    
    return True

def generate_command_handler(args):
    """Handle the generate command."""
    # Create a new prompt
    prompt = MultiContextPrompt()
    
    # Load the template
    if not prompt.load_template(args.template):
        print(f"Failed to load template from {args.template}", file=sys.stderr)
        return False
    
    # Set variables
    if args.var:
        for var_arg in args.var:
            key, value = parse_var_arg(var_arg)
            if key is not None:
                prompt.set_variable(key, value)
    
    # Save the prompt
    if not prompt.save(args.output):
        print(f"Failed to save prompt to {args.output}", file=sys.stderr)
        return False
    
    print(f"Prompt generated and saved to {args.output}")
    return True

def export_command_handler(args):
    """Handle the export command."""
    # Load the existing prompt
    try:
        with open(args.prompt, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Save to output file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Prompt exported to {args.output}")
        return True
    except Exception as e:
        print(f"Error exporting prompt: {e}", file=sys.stderr)
        return False

def import_command_handler(args):
    """Handle the import command."""
    # Load the file
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Save to output file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"File imported to {args.output}")
        return True
    except Exception as e:
        print(f"Error importing file: {e}", file=sys.stderr)
        return False

def main():
    """Main function."""
    args = parse_args()
    
    if args.command == 'create':
        success = create_command_handler(args)
    elif args.command == 'add-context':
        success = add_context_command_handler(args)
    elif args.command == 'list':
        success = list_command_handler(args)
    elif args.command == 'generate':
        success = generate_command_handler(args)
    elif args.command == 'export':
        success = export_command_handler(args)
    elif args.command == 'import':
        success = import_command_handler(args)
    else:
        print("Invalid or missing command. Use --help for usage information.", file=sys.stderr)
        sys.exit(1)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
