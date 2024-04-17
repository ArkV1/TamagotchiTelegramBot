import ast
import os
import sys

def gather_local_imports(file_path):
    """Parse the Python file and gather local import file paths."""
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
    
    # Assuming the script is located in project_root/tools
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_imports = set()  # Use a set to avoid duplicates

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                module_name = alias.name if isinstance(node, ast.Import) else node.module
                if module_name:
                    # Modify the path resolution to start from the project root
                    module_path = module_name.replace('.', os.sep) + '.py'
                    full_path = os.path.join(project_root, module_path)
                    if os.path.isfile(full_path):
                        local_imports.add(full_path)
    
    return list(local_imports)

def compile_code(main_file_path, local_import_paths):
    """Compile the content of the main file and its local imports."""
    code_blocks = []

    # Include the main file's content with a header
    with open(main_file_path, 'r', encoding='utf-8') as file:
        code_blocks.append(f"# Code from {os.path.basename(main_file_path)}\n{file.read()}\n")

    # Include the content from local imports with headers
    for path in local_import_paths:
        with open(path, 'r', encoding='utf-8') as file:
            code_blocks.append(f"# Code from {os.path.basename(path)}\n{file.read()}\n")
    
    return "\n".join(code_blocks)

def main():
    if len(sys.argv) > 1:
        main_file_path = sys.argv[1]
    else:
        main_file_path = input("Enter the full path to the Python file: ")

    local_import_paths = gather_local_imports(main_file_path)
    combined_code = compile_code(main_file_path, local_import_paths)

    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
    output_file_path = os.path.join(script_dir, 'gathered_code.txt')  # Save the output in the script's directory
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(combined_code)
    
    print(f"Combined code has been saved to {output_file_path}")

if __name__ == "__main__":
    main()
