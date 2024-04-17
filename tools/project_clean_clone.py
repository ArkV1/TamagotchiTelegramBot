import os
import shutil

def clone_project(source_path, destination_path, exclude_patterns):
  """
  Clones a Python project from source to destination, excluding files 
  matching the provided patterns.

  Args:
      source_path (str): Path to the source project directory.
      destination_path (str): Path to the destination directory.
      exclude_patterns (list): List of file patterns to exclude.
  """
  # Create destination directory if it doesn't exist
  if not os.path.exists(destination_path):
    os.makedirs(destination_path)

  for root, dirs, files in os.walk(source_path):
    # Exclude directories matching patterns
    dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

    for filename in files:
      if not any(pattern in filename for pattern in exclude_patterns):
        # Construct full paths
        source_file = os.path.join(root, filename)
        dest_file = os.path.join(destination_path, os.path.relpath(source_file, source_path))

        # Create necessary subdirectories in destination
        dest_dir = os.path.dirname(dest_file)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Copy file
        shutil.copy2(source_file, dest_file)

# Example usage
if __name__ == "__main__":
  source_path = r"c:\Projects\Python\TelegramBot"  # Replace with your project path
  destination_path = r"c:\Projects\Python\TelegramBotClean"  # Replace with desired destination path
  exclude_patterns = [".git", ".venv", "__pycache__"]  # Add more patterns as needed

  clone_project(source_path, destination_path, exclude_patterns)
  print(f"Project cloned successfully to: {destination_path}")