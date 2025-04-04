import os
import groq
import traceback

def create_groq_client():
    """
    Factory function to create a GROQ client with proper error handling.
    
    Returns:
        tuple: (client, model_name, error_message)
        - client: GROQ client or None if initialization failed
        - model_name: Model name to use
        - error_message: Error message if any
    """
    try:
        # Get credentials from environment
        api_key = os.getenv("GROQ_API_KEY")
        model_name = os.getenv("GROQ_MODEL_NAME", "deepseek-r1-distill-llama-70b")
        
        if not api_key:
            return None, None, "GROQ_API_KEY not found in environment variables"
        
        # Try to initialize the client
        try:
            # Simplest form of initialization
            client = groq.Client(api_key=api_key)
            print(f"GROQ client initialized successfully")
            return client, model_name, None
        except Exception as e:
            # If that fails, try a different approach
            print(f"Error initializing GROQ client: {str(e)}")
            print(traceback.format_exc())
            return None, None, f"Failed to initialize GROQ client: {str(e)}"
        
                
    except Exception as e:
        print(f"Unexpected error creating GROQ client: {str(e)}")
        print(traceback.format_exc())
        return None, None, f"Unexpected error: {str(e)}"

def call_groq_api(client, model_name, prompt, max_tokens=1000, temperature=0.2):
    """
    Helper function to call the GROQ API with error handling.
    
    Args:
        client: GROQ client
        model_name: Model name to use
        prompt: Prompt text
        max_tokens: Maximum tokens to generate
        temperature: Temperature parameter
        
    Returns:
        tuple: (response_text, error_message)
        - response_text: Generated text if successful
        - error_message: Error message if any
    """
    if not client:
        return None, "GROQ client not initialized"
    
    try:
        # Call the API
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        return response_text, None
        
    except Exception as e:
        error_msg = f"Error calling GROQ API: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        
        # Try fallback model
    try:
                fallback_model = "gemma2-9b-it"
                print(f"Trying fallback model: {fallback_model}")
                
                # Safely reduce prompt size to stay under token limits
                # Calculate approx 5950 tokens (slightly under 6000 limit)
                shortened_prompt = prompt[:23800]  # Assuming ~4 chars per token
                
                print(f"Original prompt length: {len(prompt)} chars, shortened to: {len(shortened_prompt)} chars")
                
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[{"role": "user", "content": shortened_prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                response_text = response.choices[0].message.content
                
                # Only add truncation warning if we actually truncated
                if len(shortened_prompt) < len(prompt):
                    response_text = "Note: Your query was truncated due to token limits. Results may be incomplete.\n\n" + response_text
                
                return response_text, None
                
    except Exception as e2:
        error_msg = f"Error with fallback model: {str(e2)}"
        print(error_msg)
        print(traceback.format_exc())
        
        # If rate limit error, try with even shorter prompt
        if "rate_limit_exceeded" in str(e2):
            try:
                print("Rate limit exceeded, trying with smaller prompt...")
                very_short_prompt = prompt[:20000]  # Even smaller, ~5000 tokens
                
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[{"role": "user", "content": very_short_prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                response_text = response.choices[0].message.content
                return "Note: Significant truncation was required due to token limits. Results may be incomplete.\n\n" + response_text, None
            except Exception as e3:
                return None, f"All fallback attempts failed: {str(e3)}"
        
        return None, error_msg
        
