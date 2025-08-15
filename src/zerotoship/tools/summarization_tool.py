"""
Summarization Tool for ZeroToShip.
Provides cost-effective text summarization using local LLM with cloud fallback.
"""

import os
import requests
from crewai.tools import BaseTool
from openai import OpenAI
from typing import Dict, Any
from pydantic import BaseModel, Field

class SummarizationArgs(BaseModel):
    """Arguments for the Summarization Tool."""
    text: str = Field(..., description="The text to summarize")
    max_length: int = Field(default=150, description="Maximum length of the summary")

class SummarizationTool(BaseTool):
    """Hybrid summarization tool using local LLM with cloud fallback."""
    
    name: str = "Context Summarizer"
    description: str = "Summarizes long text using a local LLM (Ollama) with a cloud fallback (OpenAI)."
    args_schema: type[BaseModel] = SummarizationArgs

    def _run(self, text: str, max_length: int = 150) -> str:
        """
        Summarize text using local LLM first, fallback to OpenAI if needed.
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summarized text
        """
        # First, try the local, cost-effective Ollama model
        try:
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            prompt = f"Summarize this text in {max_length} words or less: {text}"
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": max_length * 2
                    }
                },
                timeout=30  # 30-second timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("response"):
                return result["response"].strip()
            else:
                raise Exception("No response from Ollama")
                
        except Exception as e:
            # If Ollama fails or times out, fall back to OpenAI
            print(f"🔄 Ollama failed: {e}. Falling back to OpenAI.")
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a helpful assistant that creates concise summaries of {max_length} words or less."
                        },
                        {
                            "role": "user", 
                            "content": f"Summarize this text: {text}"
                        }
                    ],
                    max_tokens=max_length * 2,
                    temperature=0.3
                )
                return completion.choices[0].message.content.strip()
                
            except Exception as openai_e:
                error_msg = f"Both Ollama and OpenAI failed. Ollama error: {e}. OpenAI error: {openai_e}"
                print(f"❌ {error_msg}")
                return f"Summarization failed: {error_msg}"

    async def _arun(self, text: str, max_length: int = 150) -> str:
        """Async version of the summarization tool."""
        # For now, just call the sync version
        # In a production environment, you might want to use async HTTP clients
        return self._run(text, max_length)
