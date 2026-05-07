import subprocess
import ollama

def run_shell_command(command: str) -> str:
    """
    Executes a shell command and returns the output or error.
    Args:
        command: The full shell command string to execute.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return str(e)


# Initial prompt
messages = [{'role': 'user', 'content': 'What files are in my current directory?'}]

# Step 1: Send prompt with tools
response = ollama.chat(
    model='dolphin-llama3:8b', 
    messages=messages, 
    tools=[run_shell_command]
)

# Step 2: Handle the tool call request
if response.message.tool_calls:
    for tool in response.message.tool_calls:
        # Execute the function with model-provided arguments
        output = run_shell_command(tool.function.arguments['command'])
        
        # Add tool result to conversation history
        messages.append(response.message)
        messages.append({'role': 'tool', 'content': output, 'name': tool.function.name})

# Step 3: Get final response from the model
final_response = ollama.chat(model='dolphin-llama3:8b', messages=messages)
print(final_response.message.content)
