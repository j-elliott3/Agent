import os

def get_files_info(working_directory, directory=None):
    try:
        if directory == None:
            directory = working_directory

        target_dir = os.path.abspath(os.path.join(working_directory, directory))
        if not target_dir.startswith(os.path.abspath(working_directory)):
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
        
        if not os.path.isdir(target_dir):
            return f'Error: "{directory}" is not a directory'
    
        result = []
        contents = os.listdir(target_dir)
        for i in contents:
            path = os.path.join(target_dir, i)
            filesize = os.path.getsize(path)
            isdirectory = os.path.isdir(path)
            result.append(f'- {i}: file_size={filesize} bytes, is_dir={isdirectory}')

        return "\n".join(result)
    except Exception as e:
       return f'Error: {e}'