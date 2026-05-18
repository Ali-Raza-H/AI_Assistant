# AI Assistant

An AI-powered assistant built with Python that utilizes **Ollama** for large language model (LLM) processing. The assistant is designed to handle user queries and execute tools, such as running shell commands, through a structured routing system.
## Future Vision: The Jarvis Ecosystem

The ultimate goal of this project is to create a fully autonomous, Jarvis-style ecosystem. It will serve as a centralized hub for system control, professional productivity, and environmental awareness, powered by a suite of specialized tools.

### 🗺️ The Roadmap to Jarvis

#### 🧠 1. Advanced Intelligence & Tooling
- **Multi-Tool Orchestration:** Moving beyond basic shell commands to a system where the AI can chain multiple specialized tools (API integrations, database queries, automation scripts) to solve complex tasks.
- **Long-term Memory:** Implementing a vector database to allow the assistant to remember user preferences, past projects, and specific instructions indefinitely.

#### 🎙️ 2. Multimodal Communication (Senses)
- **STT (Speech-to-Text):** Implementing high-accuracy, low-latency voice recognition for natural conversation.
- **TTS (Text-to-Speech):** Giving Jarvis a custom, expressive voice with emotional intelligence.
- **Visual Perception:** 
    - **Screen Watching:** Real-time analysis of the user's workspace to provide context-aware assistance.
    - **Camera Integration:** Facial recognition and object detection for physical environment awareness.

#### 📁 3. System & Environment Control
- **Unified File Manager:** Advanced autonomous file read/write operations, organization, and search across local and cloud storage.
- **Network Controller:** Monitoring and managing network traffic, security auditing, and controlling connected IoT devices (lights, thermostats, etc.).
- **Location & Geo-Intelligence:** Integration with Maps and GPS for location-based reminders, weather awareness, and navigation assistance.

#### 🎨 4. Professional Expertise
- **Design Studio:** A toolset for generating UI/UX assets, editing images, and assisting in professional design workflows.
- **The Architect (Coding):** A specialized coding agent capable of full-repo refactoring, autonomous testing, and deployment management.

#### 📱 5. The Ecosystem Bridge
- **Custom Mobile App:** A dedicated mobile application (Flutter/React Native) to provide a seamless interface to Jarvis while on the go.
- **Cross-Platform Sync:** Ensuring that context and history are perfectly synced between the desktop "brain" and the mobile "companion."

## Project Structure

### Backend
The backend is written in Python and is responsible for managing the AI's logic, tool execution, and communication with Ollama.

- **`main.py`**: The entry point for the application. It provides a simple command-line interface (CLI) for interacting with the assistant.
- **`agent/`**: Contains core logic for the assistant, including system prompts and configuration for the routing mechanism.
- **`llm/`**: Manages communication with the Ollama API. It handles both the decision-making process (routing) and the generation of final responses.
- **`tools/`**: Contains modular tool implementations.
    - `runBashCommands.py`: Executes shell commands provided by the AI.
    - `toolManager.py`: Routes AI decisions to the appropriate tool function.
    - `chatHistoryTools.py`: Manages the persistence of chat history in JSON format.
- **`schemas/`**: Stores JSON definitions for tools and chat history structures.

### Frontend
The frontend directory structure is initialized for a cross-platform application (likely using Electron), including directories for `main`, `preload`, and `render` processes.

## Features
- **Intelligent Routing**: Uses a "router" LLM call to decide whether to respond directly or use a specific tool.
- **Shell Command Execution**: Capability to run system commands and return output (currently supports Windows shell commands).
- **Persistent Chat History**: Saves conversations to a local JSON file to maintain context across sessions.

## Getting Started

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) installed and running.
- The `dolphin-llama3:8b` model pulled in Ollama:
  ```bash
  ollama pull dolphin-llama3:8b
  ```

### Installation
1. Clone the repository.
2. Install required Python packages:
   ```bash
   pip install ollama
   ```

### Running the Assistant
You can start the assistant by running the provided batch file in the root directory:
```bash
./run.bat
```

## Current Status
- **Backend**: Core logic is implemented but requires refinement for error handling and improved tool-result feedback to the LLM.
- **Frontend**: Directory structure is set up but implementation is in progress.
