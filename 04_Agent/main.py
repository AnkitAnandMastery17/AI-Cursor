from openai import OpenAI
from dotenv import load_dotenv
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


available_tools = {
    "run_command": run_command
}

SYSTEM_PROMPT = f"""
     You are an helpfull AI Assistant who is specialized in resolving user query.
     You work on start, plan, action,observe mode.

     For the given user query and available tools, plan the step by step execution, based on the planning, select the relevant tool from the available tool. Based on the tool selection you perform an action to call the tool.

     Wait for the observation and based on the observation from the tool call resolve the user query.

     Rules:
    - Follow the output JSON format.
    -Always perform one step at a time and wait for the next input
    -Carefully analyse the user query

    Output JSON Format:
    {{
       "step": "string",
       "content":"string",
       "function":"The name of function if the step is action",
       "input":"The input parameter for the function",
    }}

     Available Tools:
    - "run_command": Takes linux command as a string and executes the command and returns the output after executing it.

    Example:
    User Query: What is the weather of new york?
    Output:{{"step":"plan", "content":"The user is interested in weather data of new york" }}
    Output:{{"step":"plan", "content":"From the available tools I should call get_weather" }}
    Output:{{"step":"action", "function":"get_weather","input":"new york" }}
    Output:{{"step":"observe", "output":"12 Degree cel"}}
    Output:{{"step":"output", "content":"The weather for new york seems to be 12 degrees"}}

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
                    # Add user message to continue conversation
                    messages.append({"role": "user", "content": "Continue with the next step"})
                    continue

                elif step == "action":
                    tool_name = parsed_response.get("function")
                    tool_input = parsed_response.get("input")

                    print(f"🛠️: Calling Tool: {tool_name} with input: {tool_input}")

                    # Fixed tool check
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
                    # Handle observe step (was missing)
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