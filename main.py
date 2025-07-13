import os
import sys
import functions.get_file_content
import functions.get_files_info
import functions.write_file
import functions.run_python_file
from dotenv import load_dotenv
from google import genai
from google.genai import types


def call_function(function_call_part, verbose=False):
    available_functions = {
        "get_file_content": functions.get_file_content.get_file_content,
        "get_files_info": functions.get_files_info.get_files_info,
        "write_file": functions.write_file.write_file,
        "run_python_file": functions.run_python_file.run_python_file,
    }
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    function_name = function_call_part.name
    function_call_part.args["working_directory"] = "./calculator"

    if function_name not in available_functions:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    function_result = available_functions[function_name](**function_call_part.args)

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )



def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("No response content error")
        exit(1)

    user_prompt = sys.argv[1]
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)]),
    ]

    system_prompt = """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

    - List files and directories
    - Read file contents
    - Execute Python files with optional arguments
    - Write or overwrite files

    All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
    """

    api_key = os.environ.get("GEMINI_API_KEY")

    schema_get_files_info = types.FunctionDeclaration(
        name="get_files_info",
        description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "directory": types.Schema(
                    type=types.Type.STRING,
                    description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
                ),
            },
        ),
    )

    schema_get_file_content = types.FunctionDeclaration(
        name="get_file_content",
        description="Reads the content of a file, constrained to the working directory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(
                    type=types.Type.STRING,
                    description="The file to be read.",
                ),
            },
        ),
    )

    schema_run_python_file = types.FunctionDeclaration(
        name="run_python_file",
        description="Runs the python code from within the given file, constrained to the working directory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(
                    type=types.Type.STRING,
                    description="Run the code within the Python file.",
                ),
            },
        ),
    )

    schema_write_file = types.FunctionDeclaration(
        name="write_file",
        description="Writes to the given file, constrained to the working directory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(
                    type=types.Type.STRING,
                    description="The file to be written over.",
                ),
                "content": types.Schema(
                    type=types.Type.STRING,
                    description="The content to be written."
                ),
            },
        ),
    )

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True


    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_run_python_file,
            schema_write_file,
        ]
    )
    client = genai.Client(api_key=api_key)

    loop_count = 0

    while loop_count < 20:
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-001', 
                contents=messages,
                config=types.GenerateContentConfig(tools=[available_functions], system_instruction=system_prompt)
            )

            if response.function_calls:
                for function_call_part in response.function_calls:
                    function_call_result = call_function(function_call_part, verbose)
                    if not function_call_result.parts[0].function_response.response["result"]:
                        raise Exception("Fatal function call result error")
                    if verbose:
                        print(f"-> {function_call_result.parts[0].function_response.response["result"]}")
                    messages.append(function_call_result)

            if verbose:
                print("User prompt: " + user_prompt)
                print("Prompt tokens: " + str(response.usage_metadata.prompt_token_count))
                print("Response tokens: " + str(response.usage_metadata.candidates_token_count))

            if len(response.candidates) > 0:
                for candidate in response.candidates:
                    messages.append(candidate.content)

            if response.text:
                print(response.text)
                break

            loop_count += 1
        except Exception as e:
            print(f"Error encountered: {e}")

if __name__ == "__main__":
    main()