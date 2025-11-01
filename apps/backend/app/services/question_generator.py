"""LLM-powered question generation service for natural, context-aware conversations."""

from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from datetime import date


class QuestionGenerator:
    """
    Generate natural, context-aware questions using LLM.
    
    Instead of fixed templates, questions reference previously collected information
    and adapt to the conversation flow, making interactions feel more human.
    """
    
    # System prompts for each field - these guide the LLM to ask appropriately
    PROMPTS = {
        "destination": """You are a friendly travel insurance assistant having a natural conversation.

Ask the user where they're traveling to. Be warm and conversational.

Context you have so far:
{collected_info}

Recent conversation:
{conversation_context}

Requirements:
- Ask for their destination country or city
- Reference their previous messages if relevant (e.g., "That sounds exciting! Where are you headed?")
- Keep it natural and friendly (1-2 sentences max)
- Don't repeat information they already gave you

Example good responses:
- "That sounds exciting! Where are you planning to travel?"
- "Great! Which country or city are you visiting?"
- "I'd love to help! Where's your destination?"
- "Where are you headed?"
""",

        "departure_date": """You are a friendly travel insurance assistant having a natural conversation.

Ask the user when their trip starts.

Context you have so far:
- Destination: {destination}
{collected_info}

Recent conversation:
{conversation_context}

Requirements:
- Ask for their departure date
- Reference their destination ({destination}) to make it personal
- Suggest YYYY-MM-DD format but keep it conversational
- Keep it warm and natural (1-2 sentences max)
- Acknowledge their destination choice if appropriate

Example good responses:
- "Nice! When do you depart for {destination}?"
- "Great choice! What date are you heading to {destination}?"
- "Perfect! When does your {destination} adventure begin? (YYYY-MM-DD format works best)"
- "When are you flying to {destination}? Please use YYYY-MM-DD format, like 2025-12-15"
""",

        "return_date": """You are a friendly travel insurance assistant having a natural conversation.

Ask when they return home.

Context you have so far:
- Destination: {destination}
- Departure: {departure_date}
{collected_info}

Recent conversation:
{conversation_context}

Requirements:
- Ask for their return date
- Reference their trip context naturally
- Suggest YYYY-MM-DD format
- Keep it conversational (1-2 sentences max)

Example good responses:
- "And when do you return from {destination}?"
- "Got it! What's your return date? (YYYY-MM-DD format please)"
- "Perfect! When do you come back? Use YYYY-MM-DD format, like 2025-12-22"
- "When are you returning to Singapore?"
""",

        "travelers": """You are a friendly travel insurance assistant having a natural conversation.

Ask about travelers and their ages.

Context you have so far:
- Destination: {destination}
- Dates: {departure_date} to {return_date}
{collected_info}

Recent conversation:
{conversation_context}

Requirements:
- Ask how many travelers AND their ages (both in same question)
- Explain we need ages for accurate pricing
- Provide example format
- Be warm and natural (1-2 sentences max)

Example good responses:
- "Great! How many people are traveling, and what are their ages? (e.g., '2 travelers, ages 30 and 8')"
- "Perfect! I'll need the ages of everyone traveling for accurate pricing. How many travelers and their ages?"
- "Who's going on this trip? Please share the number of travelers and their ages."
- "How many travelers, and what are their ages? For example: '2 travelers, ages 30 and 8'"
""",

        "adventure_sports": """You are a friendly travel insurance assistant having a natural conversation.

Ask if they're planning adventure activities.

Context you have so far:
- Destination: {destination}
- Dates: {departure_date} to {return_date}
- Travelers: {travelers}
{collected_info}

Recent conversation:
{conversation_context}

Requirements:
- Ask about adventure sports/activities
- Give examples (skiing, diving, trekking, bungee jumping)
- Explain this affects coverage options
- Keep it conversational (1-2 sentences max)
- Be enthusiastic if the destination suggests adventure activities

Example good responses:
- "One last question! Are you planning any adventure activities like skiing, scuba diving, or hiking?"
- "Almost done! Will you be doing any adventure sports (diving, skiing, trekking, etc.)?"
- "Great! Are there any adventure activities on your itinerary? This helps me recommend the right coverage."
- "Last thing - any adventure sports planned? Things like diving, skiing, or bungee jumping?"
""",

        "confirmation": """You are a friendly travel insurance assistant having a natural conversation.

Present the trip details you've collected and ask the user to confirm they're correct.

Context you have:
{collected_info}

Requirements:
- Summarize ALL the information collected (destination, dates, travelers, adventure sports)
- Present it clearly with each detail on its own line
- Ask if everything is correct
- Be friendly and thorough (this is important!)
- Format as a confirmation request

Example format:
"Perfect! Let me confirm your trip details:

🌍 Destination: {destination}
📅 Departure: {departure_date}
📅 Return: {return_date}
👥 Travelers: {travelers} (ages: {ages})
🏔️ Adventure sports: {adventure_sports}

Is everything correct?"
"""
    }
    
    # Fallback templates - used if LLM fails or feature is disabled
    FALLBACK_TEMPLATES = {
        "destination": "Where are you traveling to?",
        "departure_date": "When does your trip start? Please provide the date in YYYY-MM-DD format. For example: 2025-12-15",
        "return_date": "When do you return to Singapore? Please provide the date in YYYY-MM-DD format. For example: 2025-12-22",
        "travelers": "How many travelers are going, and what are their ages? For example: '2 travelers, ages 30 and 8'",
        "adventure_sports": "Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?",
        "confirmation": "Please confirm the details are correct."
    }
    
    def __init__(self):
        """Initialize the question generator."""
        pass
    
    def generate_question(
        self,
        field: str,
        collected_info: Dict[str, Any],
        conversation_history: List[BaseMessage],
        llm_client: Any,
        use_llm: bool = True
    ) -> str:
        """
        Generate a natural, context-aware question for the specified field.
        
        Args:
            field: Field to ask about (destination, departure_date, etc.)
            collected_info: Information already collected from user
            conversation_history: Previous conversation messages
            llm_client: LLM client for generation (GroqLLMClient instance)
            use_llm: Whether to use LLM generation (False = use templates)
            
        Returns:
            Generated question as string
        """
        # If LLM mode disabled, use templates
        if not use_llm:
            return self._get_fallback_template(field, collected_info)
        
        # Try to generate with LLM
        try:
            return self._generate_with_llm(field, collected_info, conversation_history, llm_client)
        except Exception as e:
            print(f"⚠️  Question generation failed for field '{field}': {e}")
            print(f"   Falling back to template")
            return self._get_fallback_template(field, collected_info)
    
    def _generate_with_llm(
        self,
        field: str,
        collected_info: Dict[str, Any],
        conversation_history: List[BaseMessage],
        llm_client: Any
    ) -> str:
        """Generate question using LLM with context awareness."""
        
        # Get the appropriate system prompt
        prompt_template = self.PROMPTS.get(field)
        if not prompt_template:
            print(f"⚠️  No prompt template for field '{field}', using fallback")
            return self._get_fallback_template(field, collected_info)
        
        # Build context from collected info
        info_lines = []
        for key, value in collected_info.items():
            if value is not None:
                # Format dates nicely
                if isinstance(value, date):
                    value = value.isoformat()
                # Format lists nicely
                elif isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                info_lines.append(f"- {key}: {value}")
        
        info_summary = "\n".join(info_lines) if info_lines else "- (No information collected yet)"
        
        # Get last 3 messages for context (balance between context and brevity)
        recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        conversation_context = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content[:100]}"
            for msg in recent_messages
        ]) if recent_messages else "(First interaction)"
        
        # Extract specific values for prompt formatting
        destination = collected_info.get("destination", "[not provided yet]")
        departure_date = collected_info.get("departure_date")
        if isinstance(departure_date, date):
            departure_date = departure_date.isoformat()
        departure_date = departure_date or "[not provided yet]"
        
        return_date = collected_info.get("return_date")
        if isinstance(return_date, date):
            return_date = return_date.isoformat()
        return_date = return_date or "[not provided yet]"
        
        travelers = collected_info.get("travelers")
        if isinstance(travelers, list):
            travelers = f"{len(travelers)} travelers, ages {', '.join(str(t) for t in travelers)}"
        travelers = travelers or "[not provided yet]"
        
        # Format the system prompt with actual data
        system_prompt = prompt_template.format(
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            travelers=travelers,
            collected_info=info_summary,
            conversation_context=conversation_context
        )
        
        # Generate the question using LLM
        user_prompt = f"Generate a natural, friendly question to ask the user about their {field}. Keep it conversational and reference the context provided. Maximum 2 sentences."
        
        # Use the LLM client's generate method
        response = llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,  # Higher temperature for natural variation
            max_tokens=150    # Questions should be concise
        )
        
        # Validate response
        if not response or len(response.strip()) == 0:
            print(f"⚠️  LLM returned empty response for field '{field}'")
            return self._get_fallback_template(field, collected_info)
        
        # Clean up response
        response = response.strip()
        
        # Ensure it's reasonably short (questions shouldn't be essays)
        if len(response) > 300:
            print(f"⚠️  LLM response too long ({len(response)} chars), using fallback")
            return self._get_fallback_template(field, collected_info)
        
        print(f"✅ Generated question for '{field}': {response[:80]}...")
        return response
    
    def _get_fallback_template(self, field: str, collected_info: Dict[str, Any]) -> str:
        """Get fallback template with basic context injection if possible."""
        template = self.FALLBACK_TEMPLATES.get(field, "Could you provide more information?")
        
        # For some templates, we can still inject context even without LLM
        if field == "departure_date" and collected_info.get("destination"):
            return f"When do you depart for {collected_info['destination']}? Please use YYYY-MM-DD format, like 2025-12-15"
        elif field == "return_date" and collected_info.get("destination"):
            return f"When do you return from {collected_info['destination']}? Please use YYYY-MM-DD format, like 2025-12-22"
        
        return template

