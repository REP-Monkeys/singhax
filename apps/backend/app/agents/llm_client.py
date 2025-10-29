"""LLM client for conversational agents."""

from typing import Optional, Dict, Any, List
from groq import Groq
from openai import OpenAI

from app.core.config import settings


class LLMClient:
    """Client for LLM interactions using Groq or OpenAI."""
    
    def __init__(self, provider: str = "groq", model: Optional[str] = None):
        """Initialize LLM client.
        
        Args:
            provider: LLM provider ("groq" or "openai")
            model: Model name to use (defaults to config settings)
        """
        self.provider = provider
        self.model = model or settings.model_name
        
        if provider == "groq":
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY not set in environment")
            self.client = Groq(api_key=settings.groq_api_key)
        elif provider == "openai":
            self.client = OpenAI()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Generate completion from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"ERROR: LLM generation failed: {e}")
            return "I'm having trouble processing your request. Please try again."
    
    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Generate completion with conversation history.
        
        Args:
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API
            
        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"ERROR: LLM generation failed: {e}")
            return "I'm having trouble processing your request. Please try again."
    
    def detect_intent(
        self,
        user_input: str,
        available_intents: List[str]
    ) -> Dict[str, Any]:
        """Detect user intent from input.
        
        Args:
            user_input: User's message
            available_intents: List of possible intents
            
        Returns:
            Dict with "intent" and "confidence" keys
        """
        intents_str = ", ".join(available_intents)
        
        system_prompt = f"""You are an intent classifier for a travel insurance assistant.
Given a user message, classify it into one of these intents: {intents_str}

Respond with ONLY the intent name, nothing else."""
        
        prompt = f"Classify this message: {user_input}"
        
        detected_intent = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=50
        ).strip().lower()
        
        # Simple confidence score based on keyword matching
        confidence = 0.7
        if detected_intent in available_intents:
            confidence = 0.8
        
        return {
            "intent": detected_intent,
            "confidence": confidence
        }
    
    def extract_information(
        self,
        user_input: str,
        fields_to_extract: List[str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured information from user input.
        
        Args:
            user_input: User's message
            fields_to_extract: List of field names to extract
            context: Additional context for extraction
            
        Returns:
            Dict with extracted field values
        """
        fields_str = ", ".join(fields_to_extract)
        
        system_prompt = f"""You are an information extraction assistant for travel insurance.
Extract the following information from the user's message: {fields_str}

{context or ''}

Respond in JSON format with the field names as keys. If a field is not found, use null."""
        
        prompt = f"Extract information from: {user_input}"
        
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=300
        )
        
        # Try to parse JSON response
        try:
            import json
            extracted = json.loads(response)
            return extracted
        except:
            print(f"WARNING: Failed to parse extraction response: {response}")
            return {}


# Global LLM client instance (lazy-loaded)
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client instance.
    
    Returns:
        LLMClient instance
    """
    global _llm_client
    
    if _llm_client is None:
        try:
            _llm_client = LLMClient(provider="groq")
            print("INFO: LLM client initialized with Groq")
        except ValueError as e:
            print(f"WARNING: {e} - LLM features will be limited")
            _llm_client = None
    
    return _llm_client


def is_llm_available() -> bool:
    """Check if LLM client is available.
    
    Returns:
        True if LLM client is available, False otherwise
    """
    return settings.groq_api_key is not None or settings.openai_api_key is not None



