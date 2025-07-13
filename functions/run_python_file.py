import os
import subprocess

def run_python_file(working_directory, file_path):
    try:
        target_path = os.path.abspath(os.path.join(working_directory, file_path))
        if not target_path.startswith(os.path.abspath(working_directory)):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        
        if not os.path.exists(target_path):
            return f'Error: File "{file_path}" not found.'
        
        if not file_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'
        
        command = ["python3", file_path]
        run_object = subprocess.run(command, cwd=working_directory, capture_output=True, timeout=30)

        stdout = run_object.stdout.decode('utf-8')
        stderr = run_object.stderr.decode('utf-8')
        result = f'STDOUT: {stdout}\nSTDERR: {stderr}'

        if run_object.returncode != 0:
            return f'{result}\nProcess exited with code {run_object.returncode}'

        if not run_object.stdout and not run_object.stderr:
            return "No output produced."
        
        return result
    except Exception as e:
        return f'Error: executing Python file: {e}'

