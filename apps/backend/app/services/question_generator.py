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
- Ask for their destination COUNTRY - a country name is sufficient
- You DON'T need a specific city or region - just the country is fine
- Examples of good destinations: "Japan", "Nepal", "Thailand", "Indonesia"
- Only reject vague regions like "Asia", "Europe", "Southeast Asia" - actual countries are perfect
- Reference their previous messages if relevant
- Keep it natural and friendly (1-2 sentences max)
- Don't repeat information they already gave you

Example good responses:
- "Where are you traveling? Which country are you visiting?"
- "Great! Which country are you headed to?"
- "I'd love to help! What country are you traveling to?"
- "Where are you going? Just tell me the country - like Japan, Thailand, or Nepal"
""",

        "departure_date": """You are a friendly travel insurance assistant having a natural conversation.

Ask the user when their trip starts.

Context you have so far:
- Destination: {destination}
{collected_info}

Recent conversation:
{conversation_context}

CRITICAL - DETECT LOGICAL IMPOSSIBILITIES:
- If the user mentioned an activity that's IMPOSSIBLE at their destination, gently point it out
- Examples of impossibilities:
  * Skiing in tropical beach destinations (Thailand, Phuket, Bali, Singapore, Philippines, Indonesia, Malaysia, etc.)
  * Snow sports in equatorial/tropical regions
  * Scuba diving in landlocked mountain areas
- If you detect an impossibility, politely clarify and ask if they meant something else
- Don't be rude, just helpful - they might be joking or confused

Requirements:
- FIRST check if the user mentioned any impossible activities for {destination}
- If impossibility detected, politely point it out and ask for clarification (2-3 sentences is fine for this)
- Otherwise, ask for their departure date in a friendly, conversational way (1-2 sentences)
- Accept natural date formats (they can say "Jan 15", "next Friday", "December 20th", etc.)
- Keep it warm and natural - be helpful, not judgmental
- Don't just ignore impossible activities - address them kindly

Example responses if impossibility detected:
- "I noticed you mentioned skiing in Thailand - Thailand is a tropical beach destination without snow or skiing facilities. Did you mean a different activity like water sports, or perhaps you're visiting a different destination for skiing? I want to make sure you get the right coverage!"
- "Just checking - Phuket doesn't have skiing facilities since it's a tropical island. Did you mean water skiing or another beach activity? Or are you planning to ski somewhere else? Let me know so I can help properly!"

Example responses if no issues:
- "When do you depart for {destination}? You can say it any way - like 'Jan 15' or 'next Friday'"
- "What's your departure date to {destination}? Any format works!"
- "When are you heading to {destination}? Just tell me the date naturally!"
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
- Ask for their return date in a friendly way
- Mention it should be after their departure ({departure_date}) but don't be pushy
- Accept any natural date format
- Reference their trip context naturally
- Keep it conversational (1-2 sentences max)
- Be flexible and helpful, not demanding

Example good responses:
- "And when do you return from {destination}? Any format works - just make sure it's after {departure_date}!"
- "What's your return date? You can say it however you like - 'Jan 25', 'the 25th', etc."
- "When do you come back from {destination}? Just tell me the date naturally!"
- "Perfect! When's your return date? Feel free to use any format - as long as it's after you leave on {departure_date}!"
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
- Ask how many travelers AND their SPECIFIC AGES (both in same question)
- Be VERY CLEAR that you need the actual age numbers, not just the count
- Explain we need ages for accurate pricing
- Provide a CONCRETE example format showing ages as numbers
- Be warm and natural (1-2 sentences max)
- If they only gave a count before, emphasize you need the specific ages

Example good responses:
- "How many travelers and what are their specific ages? For example: '2 travelers, ages 30 and 8'. I need the actual ages for accurate pricing."
- "I need to know how many people are traveling and their exact ages. Please tell me like this: '3 travelers, ages 45, 42, and 12'"
- "Great! Now tell me how many travelers and their specific ages (numbers). Example format: '2 travelers, ages 30 and 8'"
- "How many people are going and what are their ages? Be specific with the age numbers - like '1 traveler, age 28' or '3 travelers, ages 35, 32, and 5'"
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
        "destination": "Where are you traveling? Which country are you visiting? For example: Japan, Nepal, Thailand",
        "departure_date": "When do you depart? You can say it any way you like - 'Jan 15', 'next Monday', '2025-12-15', whatever works for you!",
        "return_date": "When do you return? Any date format is fine - just let me know when you're coming back!",
        "travelers": "How many travelers and what are their ages? For example: '2 travelers, ages 30 and 8'",
        "adventure_sports": "Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?",
        "confirmation": "Is all the information above correct?"
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
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content[:200]}"  # Increased to 200 to catch full user messages
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
        if field == "departure_date":
            user_prompt = f"""Based on the recent conversation:
1. Check if the user mentioned any impossible activities for {destination} (e.g., skiing in tropical places, diving in landlocked areas)
2. Generate your response:

If you detected an impossibility:
- Politely point out the issue and ask for clarification
- Example: "I noticed you mentioned skiing in Thailand - Thailand is a tropical beach destination without skiing facilities. Did you mean water sports or a different destination?"

If no impossibility detected:
- Simply ask for the departure date in a friendly way
- Example: "When are you heading to {destination}? Any date format works!"

IMPORTANT: Only output the final question/response. Do NOT include your reasoning or analysis. Just give the question directly."""
        else:
            user_prompt = f"Generate a natural, friendly question to ask the user about their {field}. Keep it conversational and reference the context provided. Maximum 2 sentences."
        
        # Use the LLM client's generate method
        # Allow more tokens for departure_date since it might need to explain impossibilities
        # Use lower temperature for departure_date to ensure consistent impossibility detection
        max_tokens = 250 if field == "departure_date" else 150
        temperature = 0.5 if field == "departure_date" else 0.7  # Lower for logic checking
        response = llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
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
            return f"When do you depart for {collected_info['destination']}? Any format works - 'Jan 15', 'next week', whatever's easiest!"
        elif field == "return_date" and collected_info.get("destination"):
            dep_date = collected_info.get("departure_date")
            if dep_date:
                return f"When do you return from {collected_info['destination']}? Any date format is fine - just make sure it's after {dep_date}!"
            else:
                return f"When do you return from {collected_info['destination']}? Tell me the date however you like!"
        
        return template

