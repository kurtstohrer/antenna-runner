import os
import json
import time 
import shutil 

def write(path, data):
    """
    Write data to a file specified by path.

    :param path: The path to the file where data should be written.
    :param data: The data to write to the file.
    """
    try:
        with open(path, 'w') as file:
            file.write(data)
        return {"success": f"Data written to '{path}' successfully"}
    except OSError as error:
        return {"error": f"Error writing to file '{path}': {error}"}

def read(path):
    """
    Read and return the contents of a file specified by path.

    :param path: The path to the file to be read.
    :return: The contents of the file or an error message.
    """
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return {"error": f"File '{path}' not found"}
    except OSError as error:
        return {"error": f"Error reading file '{path}': {error}"}

def mkdir(path):
    try:
        os.mkdir(path)
        return { "success": f"Directory '{path}' created successfully"}
    except FileExistsError:
        return { "error": f"Directory '{path}' already exists"}
    except OSError as error:
        return { "error": f"Error creating directory '{path}': {error}"}

def touch(path):
    try:
        with open(path, 'a'):
            os.utime(path, None)
        return {"success": f"File '{path}' touched successfully"}
    except OSError as error:
        return {"error": f"Error touching file '{path}': {error}"}

def cp(source, destination):
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy(source, destination)
        return {"success": f"File or directory '{source}' copied to '{destination}' successfully"}
    except FileNotFoundError:
        return {"error": f"File or directory '{source}' not found"}
    except OSError as error:
        return {"error": f"Error copying file or directory '{source}' to '{destination}': {error}"}


def symlink(source, destination):
    try:
        os.symlink(source, destination)
        return {"success": f"Symlink '{source}' created successfully"}
    except FileNotFoundError:
        return {"error": f"File or directory '{source}' not found"}
    except OSError as error:
        return {"error": f"Error creating symlink '{source}': {error}"}
        
def list_dir(directory, ext=None):

    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if ext is None:
                files.append(os.path.join(root, filename))
            elif filename.endswith(ext):
                files.append(os.path.join(root, filename))
    return files

def rm(path):
    try:
        os.remove(path)
        return {"success": f"File '{path}' removed successfully"}
    except FileNotFoundError:
        return {"error": f"File '{path}' not found"}
    except OSError as error:
        return {"error": f"Error removing file '{path}': {error}"}

def rmdir(path, recursive=False):
    try:
        if recursive:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
        return {"success": f"Directory '{path}' removed successfully"}
    except FileNotFoundError:
        return {"error": f"Directory '{path}' not found"}
    except OSError as error:
        return {"error": f"Error removing directory '{path}': {error}"}

def list_files_and_directories(directory, recursive=False, basepath=False):
    """Return a list of files and directories in the given directory with metadata."""
    items = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                full_path = os.path.abspath(entry.path)
                if basepath:
                    path = full_path.replace(basepath,"")
                else:
                    path = full_path.replace(os.getcwd(),"")
                if entry.is_file():
                    item = {
                        "name": entry.name,
                        "type": "file",
                        "size": entry.stat().st_size,  # Size in bytes
                        "extension": os.path.splitext(entry.name)[1][1:],  # File extension without the dot
                        "last_modified": time.ctime(entry.stat().st_mtime),  # Last modified timestamp
                        "path": path  # Full path to the file
                    }
                elif entry.is_dir():
                    item = {
                        "name": entry.name,
                        "type": "directory",
                        "path": path  # Full path to the directory
                    }
                    if recursive:
                        item["files"] = list_files_and_directories(os.path.join(directory, entry.name), recursive=True, basepath=basepath)
                else:
                    item = {
                        "name": entry.name,
                        "type": "unknown",
                        "path": path  # Full path, even if type is unknown
                    }
                
                items.append(item)
        return items
    except Exception as e:
        return [{"error": f"An error occurred: {e}"}]



async def package_directory(source_dir, output_path, package_name):
    """
    Packages the specified directory into a ZIP file.

    :param source_dir: Path to the directory to be packaged.
    :param output_filename: The name of the output ZIP file (without extension).
    """
    # Creating the full path for the output file
    output_path = os.path.join(os.getcwd(), output_path)
    output_filename = os.path.join(os.getcwd(), package_name)
    # Use shutil to create a zip archive
    shutil.make_archive(output_filename, 'zip', source_dir)