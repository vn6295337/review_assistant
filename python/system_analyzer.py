#!/usr/bin/env python3
"""
System Analyzer for RAG Assistant

This script analyzes the folder structure and files in the RAG Assistant directory
and generates a comprehensive report about the system architecture and components.

It extracts information about:
- Folder structure and organization
- Python scripts (docstrings, functions, dependencies)
- Shell scripts and workflows
- Dependencies used throughout the system
"""

import os
import sys
import re
import ast
import inspect
import importlib
import importlib.util
import pkgutil
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path

# Configuration
BASE_DIR = "/mnt/chromeos/removable/USB Drive/review_assistant"
OUTPUT_FILE = os.path.join(BASE_DIR, "system_analysis_report.txt")

# Updated directory structure configuration to match actual project layout
PYTHON_DIR = os.path.join(BASE_DIR, "python")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# Core files are now expected to be in the python directory
CORE_FILES = [
    "file_chunker.py",
    "file_summarizer.py",
    "chunk_searcher.py",
    "mcp_helper.py",
]

# Driver scripts that coordinate the system functionality
DRIVER_SCRIPTS = [
    "main.py", 
    "rag_assistant.py", 
    "simple_rag_assistant.py", 
    "system_analyzer.py"
]

def write_section(file, title: str, content: str = None) -> None:
    """Write a section to the report file with a title and optional content."""
    file.write(f"\n{'=' * 80}\n")
    file.write(f"{title.upper()}\n")
    file.write(f"{'=' * 80}\n\n")
    if content:
        file.write(f"{content}\n")

def analyze_folder_structure(base_dir: str) -> str:
    """Analyze and return the folder structure as a formatted string."""
    result = []
    
    def _print_dir(path, indent=0):
        if os.path.basename(path).startswith('.'):
            return
        result.append(f"{'  ' * indent}📁 {os.path.basename(path)}/")
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if item.startswith('.'):
                    continue
                if os.path.isdir(item_path):
                    _print_dir(item_path, indent + 1)
                else:
                    result.append(f"{'  ' * (indent + 1)}📄 {item}")
        except PermissionError:
            result.append(f"{'  ' * (indent + 1)}⚠️  [Permission denied]")
        except Exception as e:
            result.append(f"{'  ' * (indent + 1)}⚠️  [Error: {str(e)}]")
    
    try:
        if not os.path.exists(base_dir):
            return f"⚠️ Directory not found: {base_dir}"
        
        result.append(f"Directory structure of: {base_dir}\n")
        _print_dir(base_dir)
        return "\n".join(result)
    except Exception as e:
        return f"Error analyzing folder structure: {str(e)}"

def get_standard_library_modules() -> Set[str]:
    """
    Get a set of all standard library module names.
    This is more comprehensive than a hardcoded list.
    """
    stdlib_modules = set()
    
    # Get the standard library modules
    for module_info in pkgutil.iter_modules():
        if module_info.name not in ['__pycache__', '__main__']:
            stdlib_modules.add(module_info.name)
    
    # Add some common standard modules that might be missed
    common_stdlib = {
        'os', 'sys', 're', 'json', 'time', 'math', 'datetime', 'random',
        'collections', 'functools', 'itertools', 'pathlib', 'subprocess',
        'argparse', 'logging', 'hashlib', 'base64', 'shutil', 'tempfile',
        'copy', 'types', 'typing', 'warnings', 'contextlib', 'traceback',
        'threading', 'multiprocessing', 'uuid', 'unittest', 'inspect',
        'ast', 'importlib', 'platform', 'signal', 'socket', 'ssl', 'email',
        'http', 'urllib', 'xmlrpc', 'hmac', 'html', 'ftplib', 'textwrap',
        'pickle', 'shelve', 'zlib', 'zipfile', 'tarfile', 'csv', 'xml',
        'enum', 'io'
    }
    
    stdlib_modules.update(common_stdlib)
    return stdlib_modules

def extract_script_info(file_path: str) -> Dict[str, Any]:
    """Extract comprehensive information about a Python script."""
    info = {
        "description": "",
        "functions": [],
        "dependencies": [],
        "args_parser": None,
        "main_workflow": "",
        "classes": [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract docstring (description)
        module_docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if module_docstring_match:
            info["description"] = module_docstring_match.group(1).strip()
        
        # Parse the AST to extract functions, classes and imports
        try:
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        info["dependencies"].append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module if node.module else ""
                    for name in node.names:
                        if module_name:
                            info["dependencies"].append(f"{module_name}.{name.name}")
                        else:
                            info["dependencies"].append(name.name)
            
            # Extract function names and docstrings
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    func_info = {"name": node.name, "docstring": ""}
                    
                    # Get docstring if available
                    docstring = ast.get_docstring(node)
                    if docstring:
                        func_info["docstring"] = docstring
                    
                    # Check for decorators
                    if node.decorator_list:
                        decorators = []
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name):
                                decorators.append(f"@{decorator.id}")
                            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                                decorators.append(f"@{decorator.func.id}")
                        if decorators:
                            func_info["decorators"] = decorators
                    
                    info["functions"].append(func_info)
                    
                    # Check if this might be the main function
                    if node.name == "main" or node.name == "__main__":
                        info["main_workflow"] = f"Main function: {node.name}\n"
                
                # Extract class information
                elif isinstance(node, ast.ClassDef):
                    class_info = {"name": node.name, "docstring": "", "methods": []}
                    
                    # Get class docstring
                    docstring = ast.get_docstring(node)
                    if docstring:
                        class_info["docstring"] = docstring
                    
                    # Get base classes
                    if node.bases:
                        bases = []
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                bases.append(base.id)
                            elif isinstance(base, ast.Attribute):
                                bases.append(f"{base.value.id}.{base.attr}")
                        if bases:
                            class_info["bases"] = bases
                    
                    # Get class methods
                    for class_node in node.body:
                        if isinstance(class_node, ast.FunctionDef):
                            method_info = {"name": class_node.name, "docstring": ""}
                            method_docstring = ast.get_docstring(class_node)
                            if method_docstring:
                                method_info["docstring"] = method_docstring
                            class_info["methods"].append(method_info)
                    
                    info["classes"].append(class_info)
                
                # Look for argument parser
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if "ArgumentParser" in content and target.id in ["parser", "arg_parser", "argparser"]:
                                info["args_parser"] = "Uses argparse for command-line arguments"
        except SyntaxError:
            info["description"] += "\n[Warning: Could not parse the full script due to syntax error]"
        
        # Look for command line args via regex if AST parsing failed
        if not info["args_parser"] and "ArgumentParser" in content:
            info["args_parser"] = "Uses argparse for command-line arguments"
        
        # Look for main execution pattern
        if "__name__" in content and "__main__" in content:
            if not info["main_workflow"]:
                info["main_workflow"] = "Script has a __name__ == '__main__' block for direct execution"
            
        return info
    
    except Exception as e:
        return {"error": f"Error analyzing {os.path.basename(file_path)}: {str(e)}"}

def analyze_shell_script(file_path: str) -> Dict[str, Any]:
    """Analyze shell script to extract key information."""
    info = {
        "description": "",
        "commands": [],
        "functions": [],
        "usage": "",
        "python_calls": [],
        "environment_vars": [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract shebang
        shebang_match = re.search(r'^#!(.*)$', content)
        if shebang_match:
            info["shebang"] = shebang_match.group(1).strip()
        
        # Extract comments at the start (description)
        comment_block = re.search(r'^(?:#!.*\n)?(?:#\s*(.*?)(?=\n[^#]|\Z))', content, re.DOTALL | re.MULTILINE)
        if comment_block:
            info["description"] = comment_block.group(1).replace('#', '').strip()
        
        # Extract environment variables
        env_vars = re.findall(r'(?:^|\n)\s*([A-Z_][A-Z0-9_]*)=', content)
        for var in env_vars:
            if var not in info["environment_vars"]:
                info["environment_vars"].append(var)
        
        # Extract functions
        function_matches = re.finditer(r'function\s+(\w+)\s*\(\)\s*{([^}]*)}', content, re.DOTALL)
        for match in function_matches:
            func_name = match.group(1)
            func_body = match.group(2).strip()
            info["functions"].append({
                "name": func_name,
                "body": func_body
            })
        
        # Extract usage information
        usage_match = re.search(r'usage\(\)\s*{([^}]*)}', content, re.DOTALL | re.IGNORECASE)
        if usage_match:
            info["usage"] = usage_match.group(1).strip()
        elif "Usage:" in content:
            usage_line = re.search(r'# Usage:(.*?)(\n|$)', content)
            if usage_line:
                info["usage"] = usage_line.group(1).strip()
        
        # Extract key commands being executed
        python_calls = re.findall(r'python3?\s+([^\s&|;]+)(?:\s+([^\n&|;]+))?', content)
        for call in python_calls:
            script = call[0].strip()
            args = call[1].strip() if len(call) > 1 and call[1] else ""
            python_call = script
            if args:
                python_call = f"{script} {args}"
            if python_call not in info["python_calls"]:
                info["python_calls"].append(python_call)
                info["commands"].append(python_call)
        
        # Extract other shell commands
        shell_commands = re.findall(r'(?:^|\n)\s*([\w\.-]+)\s+', content)
        for cmd in shell_commands:
            if cmd not in ["function", "if", "then", "else", "fi", "for", "do", "done", "case", "esac", "while", "echo", "read"] and cmd not in info["commands"]:
                info["commands"].append(cmd)
        
        return info
    
    except Exception as e:
        return {"error": f"Error analyzing {os.path.basename(file_path)}: {str(e)}"}

def analyze_workflow() -> str:
    """Analyze the typical workflow based on script contents."""
    shell_script_path = os.path.join(SCRIPTS_DIR, "rag_assistant.sh")
    result = "Typical Workflow Analysis:\n\n"
    
    try:
        if os.path.exists(shell_script_path):
            shell_info = analyze_shell_script(shell_script_path)
            if "error" not in shell_info:
                if shell_info["usage"]:
                    result += f"Usage instructions from shell script:\n{shell_info['usage']}\n\n"
                
                if shell_info["functions"]:
                    result += "Available commands based on shell functions:\n"
                    for func in shell_info["functions"]:
                        result += f"- {func['name']}\n"
                    result += "\n"
                
                if shell_info["python_calls"]:
                    result += "Python scripts invoked by the shell script:\n"
                    for cmd in shell_info["python_calls"]:
                        result += f"- {cmd}\n"
                    result += "\n"
                    
                if shell_info["environment_vars"]:
                    result += "Environment variables used in the script:\n"
                    for var in shell_info["environment_vars"]:
                        result += f"- {var}\n"
                    result += "\n"
            else:
                result += f"{shell_info['error']}\n"
        else:
            result += "Main shell script not found at expected location.\n"
            
            # Try to infer workflow from existing Python scripts in python directory
            if os.path.exists(PYTHON_DIR):
                result += "\nInferred workflow based on available scripts in python directory:\n"
                
                # Check for core files
                for script_name in CORE_FILES:
                    script_path = os.path.join(PYTHON_DIR, script_name)
                    if os.path.exists(script_path):
                        info = extract_script_info(script_path)
                        if "description" in info and info["description"]:
                            result += f"- Using {script_name}:\n"
                            result += f"  Purpose: {info['description'].splitlines()[0]}\n\n"
                
                # Check for main driver scripts
                for script_name in DRIVER_SCRIPTS:
                    script_path = os.path.join(PYTHON_DIR, script_name)
                    if os.path.exists(script_path):
                        info = extract_script_info(script_path)
                        if "description" in info and info["description"]:
                            result += f"- Main Application: {script_name}\n"
                            result += f"  Purpose: {info['description'].splitlines()[0]}\n\n"
    
    except Exception as e:
        result += f"Error analyzing workflow: {str(e)}\n"
    
    return result

def analyze_dependencies() -> str:
    """Analyze dependencies required by the scripts."""
    all_deps = set()
    result = "Dependencies required by the system:\n\n"
    
    try:
        if os.path.exists(PYTHON_DIR):
            # Get standard library modules for better categorization
            stdlib_modules = get_standard_library_modules()
            
            # Collect all dependencies from Python files
            for file in os.listdir(PYTHON_DIR):
                if file.endswith('.py'):
                    script_path = os.path.join(PYTHON_DIR, file)
                    info = extract_script_info(script_path)
                    if "dependencies" in info:
                        for dep in info["dependencies"]:
                            # Get the top-level package
                            top_level = dep.split('.')[0]
                            all_deps.add(top_level)
            
            # Separate standard library modules from external dependencies
            external_deps = set()
            std_libs = set()
            
            for dep in all_deps:
                if dep in stdlib_modules:
                    std_libs.add(dep)
                else:
                    external_deps.add(dep)
            
            # Report external dependencies first
            result += "External Python libraries used:\n"
            if external_deps:
                for dep in sorted(external_deps):
                    result += f"- {dep}\n"
            else:
                result += "No external dependencies detected.\n"
                
            # Then report standard library modules used
            result += "\nStandard library modules used:\n"
            if std_libs:
                for dep in sorted(std_libs):
                    result += f"- {dep}\n"
            else:
                result += "No standard library modules detected.\n"
        else:
            result += "Python directory not found."
    except Exception as e:
        result += f"Error analyzing dependencies: {str(e)}"
    
    return result

def analyze_scripts() -> Dict[str, str]:
    """Analyze core Python scripts in the python directory."""
    script_analyses = {}
    
    try:
        if not os.path.exists(PYTHON_DIR):
            return {"error": f"Python directory not found: {PYTHON_DIR}"}
        
        # First analyze core files
        for script_name in CORE_FILES:
            script_path = os.path.join(PYTHON_DIR, script_name)
            if os.path.exists(script_path):
                info = extract_script_info(script_path)
                
                analysis = f"Core Script: {script_name}\n\n"
                
                if "error" in info:
                    analysis += f"{info['error']}\n"
                    script_analyses[script_name] = analysis
                    continue
                
                # Description
                if info["description"]:
                    analysis += f"Description:\n{info['description']}\n\n"
                
                # Command line args
                if info["args_parser"]:
                    analysis += f"Command line arguments: {info['args_parser']}\n\n"
                
                # Functions
                if info["functions"]:
                    analysis += "Functions:\n"
                    for func in info["functions"]:
                        analysis += f"- {func['name']}"
                        if func.get("docstring"):
                            first_line = func["docstring"].splitlines()[0]
                            analysis += f": {first_line}"
                        if func.get("decorators"):
                            analysis += f" [{', '.join(func['decorators'])}]"
                        analysis += "\n"
                    analysis += "\n"
                
                # Classes
                if info["classes"]:
                    analysis += "Classes:\n"
                    for cls in info["classes"]:
                        analysis += f"- {cls['name']}"
                        if cls.get("bases"):
                            analysis += f" (inherits from: {', '.join(cls['bases'])})"
                        if cls.get("docstring"):
                            first_line = cls["docstring"].splitlines()[0]
                            analysis += f": {first_line}"
                        analysis += "\n"
                        
                        if cls["methods"]:
                            analysis += "  Methods:\n"
                            for method in cls["methods"]:
                                analysis += f"  - {method['name']}"
                                if method.get("docstring"):
                                    first_line = method["docstring"].splitlines()[0]
                                    analysis += f": {first_line}"
                                analysis += "\n"
                    analysis += "\n"
                
                # Main workflow
                if info["main_workflow"]:
                    analysis += f"{info['main_workflow']}\n"
                
                script_analyses[script_name] = analysis
            else:
                script_analyses[script_name] = f"Script not found: {script_path}\n"
        
        # Then analyze driver scripts
        for script_name in DRIVER_SCRIPTS:
            script_path = os.path.join(PYTHON_DIR, script_name)
            if os.path.exists(script_path):
                info = extract_script_info(script_path)
                
                analysis = f"Driver Script: {script_name}\n\n"
                
                if "error" in info:
                    analysis += f"{info['error']}\n"
                    script_analyses[script_name] = analysis
                    continue
                
                # Description
                if info["description"]:
                    analysis += f"Description:\n{info['description']}\n\n"
                
                # Command line args
                if info["args_parser"]:
                    analysis += f"Command line arguments: {info['args_parser']}\n\n"
                
                # Main workflow
                if info["main_workflow"]:
                    analysis += f"{info['main_workflow']}\n\n"
                
                # Functions (summary)
                if info["functions"]:
                    analysis += f"Contains {len(info['functions'])} functions\n"
                
                # Classes (summary)
                if info["classes"]:
                    analysis += f"Contains {len(info['classes'])} classes\n"
                
                script_analyses[script_name] = analysis
    
    except Exception as e:
        script_analyses["error"] = f"Error analyzing scripts: {str(e)}"
    
    return script_analyses

def check_script_locations() -> str:
    """Check if scripts are in their expected locations and if any need to be moved."""
    result = "Script Location Analysis:\n\n"
    
    try:
        # Check if core files exist in python directory
        missing_in_python = []
        for script_name in CORE_FILES:
            if not os.path.exists(os.path.join(PYTHON_DIR, script_name)):
                missing_in_python.append(script_name)
        
        if missing_in_python:
            result += "Missing core files in python directory:\n"
            for script in missing_in_python:
                result += f"- {script}\n"
                
                # Check if they exist elsewhere
                for root, dirs, files in os.walk(BASE_DIR):
                    if script in files:
                        result += f"  Found at: {os.path.join(root, script)}\n"
            result += "\n"
        else:
            result += "✓ All core scripts are in the expected python directory.\n\n"
        
        # Check for shell scripts
        shell_scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')] if os.path.exists(SCRIPTS_DIR) else []
        if shell_scripts:
            result += "Shell scripts found in scripts directory:\n"
            for script in shell_scripts:
                result += f"- {script}\n"
        else:
            result += "No shell scripts found in scripts directory.\n"
    
    except Exception as e:
        result += f"Error checking script locations: {str(e)}\n"
    
    return result

def check_for_missing_dependencies() -> str:
    """Check if any required dependencies appear to be missing."""
    result = "Missing Dependencies Check:\n\n"
    
    try:
        # Get all referenced module imports
        all_imports = set()
        
        if os.path.exists(PYTHON_DIR):
            for file in os.listdir(PYTHON_DIR):
                if file.endswith('.py'):
                    script_path = os.path.join(PYTHON_DIR, file)
                    info = extract_script_info(script_path)
                    if "dependencies" in info:
                        for dep in info["dependencies"]:
                            top_level = dep.split('.')[0]
                            all_imports.add(top_level)
        
        # Filter out standard library modules
        stdlib_modules = get_standard_library_modules()
        external_imports = [imp for imp in all_imports if imp not in stdlib_modules]
        
        # Try to import each module to see if it's installed
        missing_modules = []
        for module_name in external_imports:
            try:
                # Skip modules that are part of the project
                if os.path.exists(os.path.join(PYTHON_DIR, f"{module_name}.py")):
                    continue
                
                # Try to import
                importlib.import_module(module_name)
                
            except ImportError:
                missing_modules.append(module_name)
        
        if missing_modules:
            result += "Potentially missing dependencies:\n"
            for module in sorted(missing_modules):
                result += f"- {module}\n"
        else:
            result += "No missing dependencies detected.\n"
    
    except Exception as e:
        result += f"Error checking for missing dependencies: {str(e)}\n"
    
    return result

def main():
    print(f"Analyzing system in {BASE_DIR}...")
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as report_file:
            # Write header
            report_file.write("RAG ASSISTANT SYSTEM ANALYSIS REPORT\n")
            report_file.write(f"Generated on: {os.popen('date').read().strip()}\n")
            
            # Folder structure
            write_section(report_file, "Folder Structure", analyze_folder_structure(BASE_DIR))
            
            # Check script locations
            write_section(report_file, "Script Location Analysis", check_script_locations())
            
            # Script analysis
            script_analyses = analyze_scripts()
            write_section(report_file, "Script Analysis")
            
            # First print core scripts
            for script_name in CORE_FILES:
                if script_name in script_analyses:
                    report_file.write(f"{'-' * 40}\n")
                    report_file.write(f"{script_analyses[script_name]}\n")
            
            # Then print driver scripts
            for script_name in DRIVER_SCRIPTS:
                if script_name in script_analyses:
                    report_file.write(f"{'-' * 40}\n")
                    report_file.write(f"{script_analyses[script_name]}\n")
            
            if "error" in script_analyses:
                report_file.write(f"Error: {script_analyses['error']}\n")
            
            # Shell script analysis
            shell_script_path = os.path.join(SCRIPTS_DIR, "rag_assistant.sh")
            if os.path.exists(shell_script_path):
                shell_info = analyze_shell_script(shell_script_path)
                write_section(report_file, "Shell Script Analysis")
                
                if "error" in shell_info:
                    report_file.write(f"{shell_info['error']}\n")
                else:
                    if shell_info["description"]:
                        report_file.write(f"Description:\n{shell_info['description']}\n\n")
                    
                    if shell_info["usage"]:
                        report_file.write(f"Usage:\n{shell_info['usage']}\n\n")
                    
                    if shell_info["functions"]:
                        report_file.write("Functions:\n")
                        for func in shell_info["functions"]:
                            report_file.write(f"- {func['name']}\n")
                            # First few lines of function to get an idea
                            func_preview = "\n".join(func["body"].splitlines()[:3])
                            report_file.write(f"  Preview: {func_preview}...\n\n")
            
            # Workflow analysis
            write_section(report_file, "Workflow Analysis", analyze_workflow())
            
            # Dependencies analysis
            write_section(report_file, "Dependencies Analysis", analyze_dependencies())
            
            # Check for missing dependencies
            write_section(report_file, "Dependency Check", check_for_missing_dependencies())
            
            print(f"Analysis complete! Report saved to {OUTPUT_FILE}")
    
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as report_file:
            report_file.write(f"Analysis failed with error: {str(e)}\n")

if __name__ == "__main__":
    main()
