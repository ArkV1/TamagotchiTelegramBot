import os

def list_directory_contents(dir_path, project_root, indent_level=0, exclude_dirs=['.git', '.venv'], is_last=True):
    # Exclude specified directories
    path_parts = dir_path.split(os.sep)
    if any(ex_dir in path_parts for ex_dir in exclude_dirs):
        return
    
    # Calculate indentation and branching characters
    indent = '│   ' * (indent_level - 1) + ('└── ' if is_last else '├── ')

    # Print the current directory name with proper formatting
    if indent_level > 0:  # Avoid printing the root project directory name
        print(indent + os.path.basename(dir_path))
    
    items = [item for item in sorted(os.listdir(dir_path)) if item not in exclude_dirs]
    for index, item in enumerate(items):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            # Recursively list contents of directories, adjusting indent based on item position
            next_is_last = index == (len(items) - 1)
            list_directory_contents(item_path, project_root, indent_level + 1, exclude_dirs, next_is_last)
        else:
            # For files, just print the name with indentation
            item_indent = '│   ' * indent_level + ('└── ' if index == (len(items) - 1) else '├── ')
            print(item_indent + item)

# Use the current working directory as the project root
project_root = os.getcwd()

print(os.path.basename(project_root))
list_directory_contents(project_root, project_root)
