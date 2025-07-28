"""
AI Interface - Communicates with multiple AI providers
"""

import logging
import os
import subprocess
import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from anthropic import Anthropic

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional imports for additional providers
try:
    import openai
except ImportError:
    openai = None

try:
    import requests
except ImportError:
    requests = None


class AIInterface:
    """Interface for communicating with AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.default_provider = config.get('default_provider', 'gemini')
        
        # Initialize AI providers
        self.gemini_client = None
        self.claude_client = None
        self.openai_client = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize AI provider clients"""
        ai_config = self.config.get('ai_providers', {})
        
        # Initialize Gemini (Free tier available)
        if ai_config.get('gemini', {}).get('enabled', False):
            try:
                api_key = self._get_api_key('GEMINI_API_KEY', ai_config['gemini'].get('api_key'))
                if api_key:
                    genai.configure(api_key=api_key)
                    self.gemini_client = genai.GenerativeModel(
                        ai_config['gemini'].get('model', 'gemini-pro')
                    )
                    self.logger.info("Gemini client initialized successfully")
                else:
                    self.logger.warning("Gemini API key not found")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
        
        # Initialize Claude (Paid - $5+)
        if ai_config.get('claude', {}).get('enabled', False):
            try:
                api_key = self._get_api_key('ANTHROPIC_API_KEY', ai_config['claude'].get('api_key'))
                if api_key:
                    self.claude_client = Anthropic(api_key=api_key)
                    self.logger.info("Claude client initialized successfully")
                else:
                    self.logger.warning("Claude API key not found")
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude client: {e}")
        
        # Initialize OpenAI (Free tier available)
        if ai_config.get('openai', {}).get('enabled', False) and openai:
            try:
                api_key = self._get_api_key('OPENAI_API_KEY', ai_config['openai'].get('api_key'))
                if api_key:
                    openai.api_key = api_key
                    self.openai_client = openai
                    self.logger.info("OpenAI client initialized successfully")
                else:
                    self.logger.warning("OpenAI API key not found")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def _get_api_key(self, env_var: str, config_key: str) -> Optional[str]:
        """Get API key from environment variable or config"""
        # Try environment variable first
        api_key = os.getenv(env_var)
        if api_key:
            return api_key
        
        # Try config key (remove ${} wrapper if present)
        if config_key and config_key.startswith('${') and config_key.endswith('}'):
            env_name = config_key[2:-1]
            return os.getenv(env_name)
        
        return config_key
    
    def get_suggestions(self, content: str, goal: str, file_path: str, provider: str = None) -> Optional[str]:
        """
        Get AI suggestions for improving code based on a goal
        
        Args:
            content: The code content to improve
            goal: The improvement goal (e.g., "add tests", "improve readability")
            file_path: Path to the file being processed
            provider: AI provider to use, uses default if None
        
        Returns:
            Improved code content, or None if no suggestions
        """
        if not provider:
            provider = self.default_provider
        
        try:
            if provider == 'gemini' and self.gemini_client:
                return self._get_gemini_suggestions(content, goal, file_path)
            elif provider == 'claude' and self.claude_client:
                return self._get_claude_suggestions(content, goal, file_path)
            elif provider == 'openai' and self.openai_client:
                return self._get_openai_suggestions(content, goal, file_path)
            elif provider == 'ollama':
                return self._get_ollama_suggestions(content, goal, file_path)
            elif provider == 'huggingface':
                return self._get_huggingface_suggestions(content, goal, file_path)
            else:
                self.logger.error(f"Provider '{provider}' not available")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting suggestions from {provider}: {e}")
            return None
    
    def _get_gemini_suggestions(self, content: str, goal: str, file_path: str) -> Optional[str]:
        """Get suggestions from Gemini (Free tier available)"""
        try:
            prompt = self._build_prompt(content, goal, file_path)
            
            response = self.gemini_client.generate_content(prompt)
            
            if response.text:
                improved_code = self._extract_code_from_response(response.text)
                if improved_code:
                    self.logger.info(f"Got Gemini suggestions for {file_path}")
                    return improved_code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Gemini suggestions: {e}")
            return None
    
    def _get_claude_suggestions(self, content: str, goal: str, file_path: str) -> Optional[str]:
        """Get suggestions from Claude (Paid - $5+)"""
        try:
            prompt = self._build_prompt(content, goal, file_path)
            
            response = self.claude_client.messages.create(
                model=self.config.get('ai_providers', {}).get('claude', {}).get('model', 'claude-3-sonnet-20240229'),
                max_tokens=self.config.get('ai_providers', {}).get('claude', {}).get('max_tokens', 4000),
                temperature=self.config.get('ai_providers', {}).get('claude', {}).get('temperature', 0.3),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            if response.content and len(response.content) > 0:
                response_text = response.content[0].text
                improved_code = self._extract_code_from_response(response_text)
                if improved_code:
                    self.logger.info(f"Got Claude suggestions for {file_path}")
                    return improved_code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Claude suggestions: {e}")
            return None
    
    def _get_openai_suggestions(self, content: str, goal: str, file_path: str) -> Optional[str]:
        """Get suggestions from OpenAI (Free tier available)"""
        try:
            prompt = self._build_prompt(content, goal, file_path)
            
            response = self.openai_client.ChatCompletion.create(
                model=self.config.get('ai_providers', {}).get('openai', {}).get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.get('ai_providers', {}).get('openai', {}).get('max_tokens', 4000),
                temperature=self.config.get('ai_providers', {}).get('openai', {}).get('temperature', 0.3)
            )
            
            if response.choices and len(response.choices) > 0:
                response_text = response.choices[0].message.content
                improved_code = self._extract_code_from_response(response_text)
                if improved_code:
                    self.logger.info(f"Got OpenAI suggestions for {file_path}")
                    return improved_code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting OpenAI suggestions: {e}")
            return None
    
    def _get_ollama_suggestions(self, content: str, goal: str, file_path: str) -> Optional[str]:
        """Get suggestions from Ollama (Free - runs locally)"""
        try:
            prompt = self._build_prompt(content, goal, file_path)
            model = self.config.get('ai_providers', {}).get('ollama', {}).get('model', 'codellama')
            
            # Call Ollama API
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                improved_code = self._extract_code_from_response(result.get('response', ''))
                if improved_code:
                    self.logger.info(f"Got Ollama suggestions for {file_path}")
                    return improved_code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Ollama suggestions: {e}")
            return None
    
    def _get_huggingface_suggestions(self, content: str, goal: str, file_path: str) -> Optional[str]:
        """Get suggestions from Hugging Face (Free tier available)"""
        try:
            prompt = self._build_prompt(content, goal, file_path)
            api_key = self._get_api_key('HUGGINGFACE_API_KEY', '')
            
            if not api_key:
                self.logger.warning("Hugging Face API key not found")
                return None
            
            headers = {"Authorization": f"Bearer {api_key}"}
            model = self.config.get('ai_providers', {}).get('huggingface', {}).get('model', 'microsoft/DialoGPT-medium')
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": prompt}
            )
            
            if response.status_code == 200:
                result = response.json()
                improved_code = self._extract_code_from_response(str(result))
                if improved_code:
                    self.logger.info(f"Got Hugging Face suggestions for {file_path}")
                    return improved_code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Hugging Face suggestions: {e}")
            return None
    
    def _build_prompt(self, content: str, goal: str, file_path: str) -> str:
        """Build a prompt for the AI provider"""
        file_extension = file_path.split('.')[-1] if '.' in file_path else ''
        
        prompt = f"""You are an expert code reviewer and refactoring assistant. 

TASK: {goal}

FILE: {file_path}
LANGUAGE: {file_extension}

ORIGINAL CODE:
```{file_extension}
{content}
```

INSTRUCTIONS:
1. Analyze the code and provide improvements based on the goal: "{goal}"
2. Return ONLY the improved code, no explanations or markdown formatting
3. Maintain the same functionality while improving the code
4. If the code is already optimal, return the original code unchanged
5. Ensure the code is syntactically correct and follows best practices

IMPROVED CODE:"""

        return prompt
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract code from AI response, handling various formats"""
        if not response:
            return None
        
        # Remove markdown code blocks if present
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block or not line.strip().startswith('```'):
                code_lines.append(line)
        
        result = '\n'.join(code_lines).strip()
        return result if result else None
    
    def test_connection(self, provider: str = None) -> bool:
        """Test connection to AI provider"""
        if not provider:
            provider = self.default_provider
        
        try:
            test_content = "def hello(): print('hello')"
            test_goal = "add docstring"
            test_file = "test.py"
            
            result = self.get_suggestions(test_content, test_goal, test_file, provider)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Connection test failed for {provider}: {e}")
            return False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        providers = []
        
        if self.gemini_client:
            providers.append('gemini')
        
        if self.claude_client:
            providers.append('claude')
        
        if self.openai_client:
            providers.append('openai')
        
        # Check for local providers
        if requests:
            try:
                # Test Ollama
                response = requests.get('http://localhost:11434/api/tags')
                if response.status_code == 200:
                    providers.append('ollama')
            except:
                pass
        
        providers.append('huggingface')  # Always available if API key provided
        
        return providers
    
    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available providers"""
        return {
            'gemini': {
                'name': 'Google Gemini',
                'cost': 'Free tier available',
                'setup': 'Get API key from Google AI Studio',
                'url': 'https://makersuite.google.com/app/apikey'
            },
            'openai': {
                'name': 'OpenAI GPT',
                'cost': 'Free tier available',
                'setup': 'Get API key from OpenAI',
                'url': 'https://platform.openai.com/api-keys'
            },
            'ollama': {
                'name': 'Ollama (Local)',
                'cost': 'Completely free',
                'setup': 'Install Ollama and run locally',
                'url': 'https://ollama.ai/'
            },
            'huggingface': {
                'name': 'Hugging Face',
                'cost': 'Free tier available',
                'setup': 'Get API key from Hugging Face',
                'url': 'https://huggingface.co/settings/tokens'
            },
            'claude': {
                'name': 'Anthropic Claude',
                'cost': 'Paid ($5+ per month)',
                'setup': 'Get API key from Anthropic',
                'url': 'https://console.anthropic.com/'
            }
        }
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        return self.config.get('ai_providers', {}).get(provider, {}) 