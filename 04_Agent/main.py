from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import json

load_dotenv()

API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv("base_url")

client = OpenAI(api_key=API_KEY,
                base_url=BASE_URL)
print(API_KEY,BASE_URL)

def run_command(cmd: str):
    result = os.system(cmd)
    return result

def create_file(input_string: str):
    """Create file from AI agent input - handles various formats"""
    try:  
        # Parse input (might be "filename" or "filename content")
        parts = input_string.split(' ', 1)
        filepath = parts[0]
        content = parts[1] if len(parts) > 1 else ""
        
        # For .py files, add default content if empty
        if filepath.endswith('.py') and not content:
            content = f"# {filepath}\n# Created by AI Cursor Agent\n\nprint('Hello from {filepath}!')\n"
        
        # Create directories if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Verify file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            return {
                "success": True,
                "message": f"✅ File '{filepath}' created successfully",
                "path": os.path.abspath(filepath),
                "size": f"{file_size} bytes"
            }
        else:
            return {
                "success": False,
                "error": f"❌ File '{filepath}' was not created"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"❌ Error creating file: {str(e)}"
        }

# result = create_file("test1.py")
# print(result)

def read_file(filepath:str):
    try:
        with open(filepath,'r',encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content, "size": len(content)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def edit_file(filepath:str, old_text:str,new_text:str):
    try:
        with open(filepath,'r',encoding='utf-8') as f:
            content=f.read()

        if old_text not in content:
            return {"success": False, "error": "Text not found in file"}
        
        updated_content = content.replace(old_text,new_text)

        with open(filepath,'w',encoding='utf-8') as f:
            f.write(updated_content)

        return {"success": True, "message": "File updated successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)} 
def delete_file(filepath: str, confirm: str = "false"):
    """Delete a file with optional confirmation - complete version"""
    try:
        import os
        
        # Get full path
        full_path = os.path.abspath(filepath)
        
        # Convert confirmation to boolean
        confirm_bool = confirm.lower() in ["true", "yes", "1", "confirm"]
        
        # Safety check for important files
        dangerous_extensions = ['.py', '.js', '.html', '.css', '.json', '.md']
        is_source_file = any(filepath.endswith(ext) for ext in dangerous_extensions)
        
        # Block deletion of source files without confirmation
        if is_source_file and not confirm_bool:
            return {
                "success": False,
                "requires_confirmation": True,
                "error": f"⚠️  '{filepath}' is a source code file and requires confirmation.",
                "message": "This file appears to contain source code. Deletion will be permanent.",
                "hint": "Use confirm=true to delete this file"
            }
        
        # Check if file exists and delete it
        if os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            os.remove(filepath)  # Actually delete the file
            return {
                "success": True,
                "message": f"✅ File '{filepath}' deleted successfully",
                "deleted_path": full_path,
                "file_size": f"{file_size} bytes"
            }
        else:
            return {
                "success": False,
                "error": f"❌ File '{filepath}' does not exist or is not a file"
            }
            
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: Cannot delete '{filepath}'"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting file: {str(e)}"
        }




def list_files(directory: str = "."):
    """List files and directories"""
    try:
        items = []
        for item in Path(directory).iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        return {"success": True, "items": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

available_tools = {
    "run_command": run_command,
    "create_file": create_file,
    "read_file": read_file,
    "edit_file": edit_file,
    "delete_file": delete_file, 
    "list_files": list_files
}
# result = delete_file("testing.py", "true") 
# print(result)
SYSTEM_PROMPT = f"""
     You are an helpfull AI Assistant who is specialized in resolving user query.
     You work on start, plan, action,observe mode.

     For the given user query and available tools, plan the step by step execution, based on the planning, select the relevant tool from the available tool. Based on the tool selection you perform an action to call the tool.

     Wait for the observation and based on the observation from the tool call resolve the user query.

  
      Rules:
    -Follow the output JSON format.
    -Always perform one step at a time and wait for the next input
    -Carefully analyse the user query
    -CRITICAL: Respond with ONLY ONE JSON object per message. Never send multiple JSON objects.


    Output JSON Format:
    {{
       "step": "string",
       "content":"string",
       "function":"The name of function if the step is action",
       "input":"The input parameter for the function",
    }}

     Available Tools:
    - "run_command": Takes linux command as a string and executes the command and returns the output after executing it.
    - "create_file": Create a file.
    - "read_file": Read file contents  
    - "edit_file": Replace text in a file
    - "delete_file": Delete a file (takes filepath as input)
    - "list_files": List all the files in the directory
    Example:
    User Query: What is the capital of India?
    Output:{{"step":"plan", "content":"The user is interested in finding the capital of India" }}
    Output:{{"step":"plan", "content":"From the available tools I should call " }}
    Output:{{"step":"action", "function":"get_weather","input":"new york" }}
    Output:{{"step":"observe", "output":"India"}}
    Output:{{"step":"output", "content":"The weather for new york seems to be 12 degrees"}}

    Example for creating a file:
    User Query: Create a file named test.py?
    Output:{{"step":"plan", "content":"The user is interested in creating a file" }}
    Output:{{"step":"plan", "content":"From the available tools I should call create_file " }}
    Output:{{"step":"action", "function":"create_file","input":"test.py" }}
    Output:{{"step":"observe", "output":"Confirm if the file is created or not"}}
    Output:{{"step":"output", "content":"test.py is created successfully"}}

    Example for deleting a file or folder:
    User Query: Delete a testing.py file
    Output:{{"step":"plan", "content":"The user is interested in deleting a testing.py file" }}
    Output:{{"step":"plan", "content":"From the available tools I should call delete_file " }}
    Output:{{"step":"action", "function":"delete_file","input":"testing.py confirm=true" }}
    Output:{{"step":"observe", "output":"Confirm if the file is deleted or not"}}
    Output:{{"step":"output", "content":"The file is deleted successfully"}}

"""

messages= [
    {"role":"system", "content":SYSTEM_PROMPT}
]

while True:
    try:
        query = input("> ")
        
        # Exit condition
        if query.lower().strip() in ['exit', 'quit', 'bye']:
            print("👋 Goodbye!")
            break
            
        messages.append({"role": "user", "content": query})
       

        while True:
            try:
                response = client.chat.completions.create(
                    model="sonar-pro",
                    # Remove response_format for Perplexity API
                    # response_format={"type": "json_object"},
                    messages=messages
                )

                content = response.choices[0].message.content
                messages.append({"role": "assistant", "content": content})
                
                # Safe JSON parsing
                try:
                    parsed_response = json.loads(content)
                except json.JSONDecodeError:
                    # Handle non-JSON responses
                    print(f"🤖: {content}")
                    break

                step = parsed_response.get("step")

                if step == "plan":
                    print(f"🧠: {parsed_response.get('content')}")
                    messages.append({"role": "user", "content": "Continue with the next step"})
                    continue

                elif step == "action":
                    tool_name = parsed_response.get("function")
                    tool_input = parsed_response.get("input")

                    print(f"🛠️: Calling Tool: {tool_name} with input: {tool_input}")
                    if tool_name in available_tools:
                        output = available_tools[tool_name](tool_input)
                        messages.append({
                            "role": "user", 
                            "content": json.dumps({"step": "observe", "output": output})
                        })
                        continue
                    else:
                        print(f"❌ Tool '{tool_name}' not available")
                        break

                elif step == "observe":
                    print("👁️: Processing observation...")
                    continue

                elif step == "output":
                    print(f"🤖: {parsed_response.get('content')}")
                    break
                    
                else:
                    print(f"🤖: {content}")
                    break
                    
            except Exception as e:
                print(f"❌ API Error: {e}")
                break
                
    except KeyboardInterrupt:
        print("\n👋 Interrupted! Goodbye!")
        break
    except Exception as e:
        print(f"❌ Unexpected error: {e}")