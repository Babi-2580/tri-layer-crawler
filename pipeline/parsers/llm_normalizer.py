import os
from openai import OpenAI

# Initialize the client (Make sure you add OPENAI_API_KEY to your .env file eventually)
# For testing without a key, we have a fallback built-in.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "MOCK_KEY"))

def process_with_llm(raw_text: str, extraction_query: str) -> str:
    """Uses LLMs to extract specific data based on user instructions."""
    
    # If the user didn't ask for anything specific, just return the raw text
    if not extraction_query or extraction_query.strip() == "":
        return raw_text[:1000] # Truncated for safety

    # If you haven't set up an API key yet, bypass the LLM to prevent crashing
    if client.api_key == "MOCK_KEY":
        print("  -> [WARNING] No OpenAI API Key found. Returning mock parsed data.")
        return f"[MOCK EXTRACTION for query: '{extraction_query}'] Found 3 data points in text."

    # The actual AI parsing logic
    print(f"  -> [AI PARSER] Analyzing text for: '{extraction_query}'...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or "gpt-3.5-turbo" for cheaper testing
            messages=[
                {"role": "system", "content": "You are a cyber-intelligence data extractor. Extract exactly what the user requests from the provided text. Return ONLY the extracted data, no conversational filler."},
                {"role": "user", "content": f"INSTRUCTIONS: {extraction_query}\n\nRAW TEXT:\n{raw_text[:4000]}"}
            ],
            temperature=0.1 # Keep it strictly factual
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"LLM_EXTRACTION_ERROR: {str(e)}"