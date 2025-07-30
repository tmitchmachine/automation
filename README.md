# AI Code Automation Assistant

A local AI assistant that can work across multiple codebases on your machine to automatically improve code based on high-level goals.

## Features

- **Multi-repo support**: Configure multiple local repositories to work with
- **Goal-driven automation**: Provide high-level goals like "refactor for readability", "add tests", "improve performance"
- **AI-powered improvements**: Uses multiple AI providers (Gemini, OpenAI, Ollama, Hugging Face, Claude) to generate suggestions
- **Automatic application**: Applies improvements directly to files
- **CLI interface**: Chat with the assistant through command line
- **Modular design**: Easy to extend with git integration, PR creation, scheduling


# Activate virtual environment first
source venv/bin/activate

# Then run any of these commands:
python main.py interactive    # Start interactive mode
python main.py status        # Show current status
python main.py test          # Test AI connections
python main.py init          # Initialize directories

## Project Structure

```
ai-code-helper/
├── src/
│   ├── __init__.py
│   ├── task_manager.py      # Handles goals and task orchestration
│   ├── repo_scanner.py      # Reads files by extension
│   ├── ai_interface.py      # Calls multiple AI providers
│   ├── file_writer.py       # Applies changes to files
│   └── cli.py              # CLI interface and main loop
├── config/
│   └── settings.yaml        # Configuration for repos and AI providers
├── tests/
│   └── __init__.py
├── requirements.txt
├── env.example              # Environment variables template
└── main.py                 # Entry point
```

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your API keys
   nano .env
   ```

3. **Configure your repositories** in `config/settings.yaml`

4. **Run the assistant**:
   ```bash
   python main.py
   ```

## AI Providers & Costs

The assistant supports multiple AI providers with different cost structures:

### 🆓 **Free Options (Recommended)**

#### **Google Gemini** ⭐ **BEST FREE OPTION**
- **Cost**: Free tier available
- **Setup**: Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Quality**: Excellent for code improvement
- **Default**: Enabled by default

#### **OpenAI GPT-3.5** ⭐ **GREAT FREE OPTION**
- **Cost**: Free tier available
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Quality**: Very good for code tasks
- **Default**: Enabled by default

#### **Ollama (Local)** ⭐ **COMPLETELY FREE**
- **Cost**: 100% free (runs on your computer)
- **Setup**: Install [Ollama](https://ollama.ai/) and run locally
- **Quality**: Good, but requires more setup
- **Default**: Enabled by default

#### **Hugging Face**
- **Cost**: Free tier available
- **Setup**: Get API key from [Hugging Face](https://huggingface.co/settings/tokens)
- **Quality**: Variable depending on model
- **Default**: Enabled by default

### **Paid Options**
- **Anthropic Claude**: $5+ per month (disabled by default)
- **OpenAI GPT-4**: Paid tier of OpenAI

## Environment Variables

### GitHub Repository Connection

The application includes a GitHub repository connection feature that allows you to clone and manage GitHub repositories locally. To use this feature:

1. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5001`

5. Enter your GitHub repository URL and Personal Access Token to connect to a repository

The application will clone the repository to a local `repos` directory and provide status updates.

## Environment Variables

The assistant requires API keys for AI providers. Create a `.env` file in the project root:

```bash
# Required: Google Gemini API Key (FREE)
# Get from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Required: OpenAI API Key (FREE)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Hugging Face API Key (FREE)
# Get from: https://huggingface.co/settings/tokens
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Optional: Anthropic Claude API Key (PAID - $5+)
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Override default AI provider
DEFAULT_AI_PROVIDER=gemini

# Optional: Logging level
LOG_LEVEL=INFO
```

### Getting API Keys

- **Gemini API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) and create a new API key
- **OpenAI API Key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys) and create a new API key
- **Hugging Face API Key**: Visit [Hugging Face](https://huggingface.co/settings/tokens) and create a new token
- **Claude API Key**: Visit [Anthropic Console](https://console.anthropic.com/) and create a new API key

### Ollama Setup (Completely Free)

If you want to use Ollama (runs locally, no API costs):

1. **Install Ollama**: Visit [ollama.ai](https://ollama.ai/) and install
2. **Pull a model**: `ollama pull codellama`
3. **Start Ollama**: `ollama serve`
4. **No API key needed** - it runs on your computer!

## Usage

### Basic Usage
```bash
# Start interactive mode
python main.py

# Run a specific goal on a repo
python main.py run --repo my-project --goal "add tests"

# Test AI connections
python main.py test

# Show status
python main.py status
```

### Goals Examples
- "refactor for readability"
- "add comprehensive tests"
- "improve performance"
- "fix security vulnerabilities"
- "add type hints"
- "optimize imports"

## Configuration

Edit `config/settings.yaml` to configure:
- Repository paths

## Deployment

### Using Docker

1. Build the Docker image:
```bash
docker build -t project-automation .
```

2. Run the Docker container:
```bash
docker run -d -p 5001:5001 -e GA_API_KEY=your_key -e GA_PROPERTY_ID=your_id -e GITHUB_TOKEN=your_token project-automation
```

### Deploying to Production

1. Set up your production environment:
```bash
# Create virtual environment and install dependencies
python -m venv /path/to/venv
source /path/to/venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export GA_API_KEY=your_key
export GA_PROPERTY_ID=your_id
export GITHUB_TOKEN=your_token
```

2. Configure WSGI server (e.g., Gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

3. Set up reverse proxy (e.g., Nginx):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Usage

1. Connect Google Analytics:
   - Enter your Google Analytics API key and Property ID
   - The application will validate the connection

2. Connect GitHub Repository:
   - Enter your GitHub repository URL
   - Enter your GitHub Personal Access Token
   - Select or create a branch for the project

3. Set Project Objective:
   - Enter a detailed prompt/objective for the AI to optimize
   - Examples:
     - "Optimize performance for mobile devices"
     - "Increase conversion rates on checkout page"
     - "Reduce bounce rate on landing pages"

4. Monitor Changes:
   - View real-time analytics metrics
   - Track AI-generated code changes
   - Monitor progress towards your objective

## Security

- Never commit your API keys or tokens to version control
- Use environment variables for sensitive information
- Regularly rotate your API keys and tokens
- Enable two-factor authentication on your GitHub account
- AI provider settings (Gemini, OpenAI, Ollama, Hugging Face, Claude)
- File extensions to process
- Backup settings
- Git integration options

### AI Provider Configuration

The system supports multiple AI providers with different configurations:

```yaml
ai_providers:
  # Google Gemini (FREE TIER AVAILABLE)
  gemini:
    enabled: true
    model: "gemini-pro"
    
  # OpenAI GPT (FREE TIER AVAILABLE)
  openai:
    enabled: true
    model: "gpt-3.5-turbo"
    
  # Ollama (COMPLETELY FREE - runs locally)
  ollama:
    enabled: true
    model: "codellama"
    
  # Hugging Face (FREE TIER AVAILABLE)
  huggingface:
    enabled: true
    model: "microsoft/DialoGPT-medium"
    
  # Anthropic Claude (PAID - $5+ per month)
  claude:
    enabled: false  # Disabled by default due to cost
```

## Architecture

The project is built with a modular architecture:

- **Task Manager**: Orchestrates the improvement process
- **Repo Scanner**: Discovers and reads code files
- **AI Interface**: Communicates with multiple AI providers
- **File Writer**: Safely applies changes with backups
- **CLI**: Provides user interface and control

## Extending

The modular design makes it easy to add:
- Git integration for commits and PRs
- Scheduling capabilities
- Additional AI providers
- Custom file processors
- Web interface

## Cost Comparison

| Provider | Cost | Setup Difficulty | Quality |
|----------|------|------------------|---------|
| **Gemini** | Free tier | Easy | ⭐⭐⭐⭐⭐ |
| **OpenAI GPT-3.5** | Free tier | Easy | ⭐⭐⭐⭐ |
| **Ollama** | Completely free | Medium | ⭐⭐⭐ |
| **Hugging Face** | Free tier | Easy | ⭐⭐⭐ |
| **Claude** | $5+ per month | Easy | ⭐⭐⭐⭐⭐ |

**Recommendation**: Start with **Gemini** - it's free and works excellently for code improvement! 🎉 