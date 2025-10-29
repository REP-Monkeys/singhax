"""LLM client for conversational AI with multi-provider support."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
import json

# Multi-provider imports
from groq import Groq
from openai import OpenAI


class GroqLLMClient:
    """Client for Groq LLM integration with intent classification and information extraction."""
    
    def __init__(self):
        """Initialize Groq LLM client with configuration from settings."""
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
            timeout=settings.groq_timeout,
        )
    
    def classify_intent(
        self,
        user_message: str,
        conversation_history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Classify user intent using LLM with fallback to keyword matching.
        
        Args:
            user_message: The current user message to classify
            conversation_history: Previous messages for context
            
        Returns:
            Dictionary with keys:
                - intent (str): Classified intent
                - confidence (float): Confidence score 0-1
                - reasoning (str): Explanation of classification
        """
        try:
            # Build system prompt for intent classification
            system_prompt = """You are an intent classifier for a travel insurance chatbot.

Classify the user's intent into ONE of these categories:
- "quote": User wants to get a travel insurance quote or price
- "policy_explanation": User has questions about policy coverage or terms
- "claims_guidance": User needs help filing or understanding claims
- "human_handoff": User explicitly requests to speak with a human agent
- "general_inquiry": Unclear intent or general questions

Respond with a JSON object containing:
{
    "intent": "<one of the categories above>",
    "confidence": <float between 0 and 1>,
    "reasoning": "<brief explanation>"
}

Be decisive. Use confidence > 0.7 for clear intents, 0.5-0.7 for moderate clarity, < 0.5 for very unclear."""
            
            # Include last 3 messages from history for context
            context_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            
            # Build message list
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(context_messages)
            messages.append(HumanMessage(content=user_message))
            
            # Invoke LLM
            response = self.llm.invoke(messages)
            
            # Parse JSON response
            result = json.loads(response.content)
            
            return {
                "intent": result.get("intent", "general_inquiry"),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "LLM classification")
            }
            
        except Exception as e:
            # Fallback to keyword-based classification
            return self._fallback_intent_classification(user_message)
    
    def _fallback_intent_classification(self, user_message: str) -> Dict[str, Any]:
        """Fallback keyword-based intent classification.
        
        Args:
            user_message: User message to classify
            
        Returns:
            Dictionary with intent, confidence, and reasoning
        """
        user_lower = user_message.lower()
        
        # Check for quote-related keywords
        if any(word in user_lower for word in ["quote", "price", "cost", "insurance", "how much"]):
            return {
                "intent": "quote",
                "confidence": 0.7,
                "reasoning": "Keyword-based classification"
            }
        
        # Check for policy-related keywords
        if any(word in user_lower for word in ["policy", "coverage", "what does", "covered", "include"]):
            return {
                "intent": "policy_explanation",
                "confidence": 0.7,
                "reasoning": "Keyword-based classification"
            }
        
        # Check for claims-related keywords
        if any(word in user_lower for word in ["claim", "file", "refund", "reimburse", "submit"]):
            return {
                "intent": "claims_guidance",
                "confidence": 0.7,
                "reasoning": "Keyword-based classification"
            }
        
        # Check for human handoff keywords
        if any(word in user_lower for word in ["human", "agent", "person", "support", "help me"]):
            return {
                "intent": "human_handoff",
                "confidence": 0.9,
                "reasoning": "Keyword-based classification"
            }
        
        # Default to general inquiry
        return {
            "intent": "general_inquiry",
            "confidence": 0.5,
            "reasoning": "Keyword-based classification (default)"
        }
    
    def extract_trip_info(
        self,
        user_message: str,
        current_slots: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract trip information using Groq function calling.
        
        Args:
            user_message: User message to extract information from
            current_slots: Dictionary of already collected information
            
        Returns:
            Dictionary with extracted fields (empty if nothing extracted)
        """
        try:
            # Define extraction function schema
            extraction_function = {
                "name": "extract_trip_information",
                "description": "Extract travel insurance quote information from user message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "Country name where the user is traveling"
                        },
                        "departure_date": {
                            "type": "string",
                            "description": "Trip start date in YYYY-MM-DD format"
                        },
                        "return_date": {
                            "type": "string",
                            "description": "Trip end date in YYYY-MM-DD format"
                        },
                        "travelers_ages": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of ages for all travelers"
                        },
                        "adventure_sports": {
                            "type": "boolean",
                            "description": "Whether planning adventure activities like skiing, diving, etc."
                        }
                    }
                }
            }
            
            # Build system prompt with current context
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            slots_summary = []
            for key, value in current_slots.items():
                if value is not None:
                    slots_summary.append(f"- {key}: {value}")
            
            slots_text = "\n".join(slots_summary) if slots_summary else "None collected yet"
            
            system_prompt = f"""You are extracting travel insurance information from user messages.

Current date: {current_date}

Information already collected:
{slots_text}

IMPORTANT RULES:
1. ONLY extract NEW information from the user's message
2. Do NOT override existing information unless the user is explicitly correcting it
3. For dates, be lenient with formats but always convert to YYYY-MM-DD
4. For travelers_ages, extract all mentioned ages as integers
5. If information is unclear or ambiguous, do NOT extract it
6. Return ONLY the fields that you can confidently extract from this message

Extract information and call the function with the extracted data."""
            
            # Bind tool and invoke
            llm_with_tools = self.llm.bind_tools([extraction_function])
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = llm_with_tools.invoke(messages)
            
            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Extract arguments from first tool call
                extracted = response.tool_calls[0].get('args', {})
                return extracted
            
            return {}
            
        except Exception as e:
            # On error, return empty dict
            return {}
    
    def generate_conversational_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[BaseMessage]
    ) -> str:
        """Generate natural language response using LLM.
        
        Args:
            system_prompt: System instructions for response generation
            user_message: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response as string
        """
        try:
            # Include last 5 messages from history for context
            context_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            
            # Build message list
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(context_messages)
            messages.append(HumanMessage(content=user_message))
            
            # Invoke LLM
            response = self.llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            # Fallback to generic response
            return "I'm having trouble generating a response. Could you please rephrase that?"


class MultiProviderLLMClient:
    """Multi-provider LLM client supporting both Groq and OpenAI."""
    
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
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=settings.openai_api_key)
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
            extracted = json.loads(response)
            return extracted
        except:
            print(f"WARNING: Failed to parse extraction response: {response}")
            return {}


# Global LLM client instance (lazy-loaded)
_llm_client: Optional[MultiProviderLLMClient] = None


def get_llm_client() -> Optional[MultiProviderLLMClient]:
    """Get or create global LLM client instance.
    
    Returns:
        MultiProviderLLMClient instance or None if unavailable
    """
    global _llm_client
    
    if _llm_client is None:
        try:
            # Try Groq first, fallback to OpenAI
            if settings.groq_api_key:
                _llm_client = MultiProviderLLMClient(provider="groq")
                print("INFO: LLM client initialized with Groq")
            elif settings.openai_api_key:
                _llm_client = MultiProviderLLMClient(provider="openai")
                print("INFO: LLM client initialized with OpenAI")
            else:
                print("WARNING: No LLM API keys configured - LLM features will be limited")
                _llm_client = None
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


