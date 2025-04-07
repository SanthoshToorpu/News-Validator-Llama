import os
import re
import json
from tavily import TavilyClient
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Debug: Check if keys are loaded
print(f"TAVILY_API_KEY loaded: {'Yes' if TAVILY_API_KEY else 'No'}")
print(f"GROQ_API_KEY loaded: {'Yes' if GROQ_API_KEY else 'No'}")

# Initialize clients
try:
    print("Initializing Tavily client...")
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    print("Tavily client initialized successfully")
    
    print("Initializing Groq client...")
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("Groq client initialized successfully")
except Exception as e:
    print(f"Error initializing clients: {e}")

# System prompt for the Llama-4 model
SYSTEM_PROMPT = """<|begin_of_text|><|header_start|>system<|header_end|>
You are a professional fact-checker specializing in verifying news claims. Your job is to determine if a claim is true, false, or partially true based on real information found on the web.

For each claim:
1. First, call the search_web function to find relevant information.
2. Analyze all the information thoroughly and consider the credibility of sources.
3. Provide a clear verdict: TRUE, FALSE, PARTIALLY TRUE, or INSUFFICIENT INFORMATION.

Your goal is to help users distinguish between real and fake news with evidence-based analysis.

Always remember your thumb rule. No matter the query is repeated or it has been asked by the user in past you should always, I repeat always use the search tool to search. Even if it is a repeated query or it is in chat history you should always use the search tool to search. Why as it makes the result more concrete.

You have access to the following function:
{
  "name": "search_web",
  "description": "Search the web for information related to a news headline or claim",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query related to the news or claim to verify"
      },
      "time_range": {
        "type": "string",
        "enum": ["none", "day", "week", "month", "year"],
        "description": "Time range to limit search results. Use 'none' to search without a time limit (default is 'month')."
      }
    },
    "required": ["query"]
  }
}

do not add years until mentioned by the user in the input
if a user says "what are the top sold items in year 2024" then include year 2024 in the search query" 
if a user says "what are the top sold items" then do not add any years in the search query" 

To call a function, respond like this:
[search_web(query="your search query", time_range="month")]
<|eot|>"""

def search_web(query, time_range="month"):
    """
    Search the web for information using Tavily API
    
    Args:
        query (str): Search query
        time_range (str): Time range for results - 'day', 'week', 'month', 'year'
        
    Returns:
        dict: Raw Tavily API response or error string
    """
    # --- Hardcoded Parameters --- #
    topic = "general"
    search_depth = "advanced"
    max_results = 15
    # -------------------------- #
    
    print(f"Performing Tavily search for '{query}' with time_range='{time_range}'")
    print(f" -> Using fixed settings: topic='{topic}', depth='{search_depth}', max_results={max_results}")
    
    # Validate time_range parameter (optional but good practice)
    valid_time_ranges = ["day", "week", "month", "year"]
    if time_range not in valid_time_ranges:
        print(f"Invalid time_range '{time_range}', defaulting to 'month'")
        time_range = "month"
        
    try:
        # Perform the search with Tavily using fixed and passed parameters
        response = tavily_client.search(
            query=query,
            topic=topic, # Fixed
            search_depth=search_depth, # Fixed
            max_results=max_results, # Fixed
            time_range=time_range, # From argument
            include_answer="advanced"
        )
        
        # Return the raw response dictionary
        return response
        
    except Exception as e:
        print(f"Error searching with Tavily: {e}")
        # Return error as a dictionary for consistent handling later
        return {"error": f"Error searching with Tavily: {str(e)}"}

def execute_function_call(function_call):
    """
    Execute a function call based on the name and parameters
    
    Args:
        function_call (dict): Function call details
        
    Returns:
        str: Result of the function call, formatted for LLM
        dict: Error details if function call failed
    """
    name = function_call.get('name')
    parameters = function_call.get('parameters', {})
    
    print(f"Executing function: {name} with parameters: {parameters}")
    
    if name == 'search_web':
        # Extract parameters required by the simplified search_web
        query = parameters.get('query', '')
        time_range = parameters.get('time_range', 'month') # Default if not provided by LLM
        
        # Call the simplified search function
        result = search_web(query, time_range)
        
        # Check if Tavily returned an error
        if isinstance(result, dict) and 'error' in result:
            print(f"Error during search_web execution: {result['error']}")
            return f"Error: {result['error']}" # Return error string to LLM
            
        # Format the successful Tavily response for the LLM
        if isinstance(result, dict):
            formatted_results = "Search Results:\n\n"
            
            # Add search summary if available
            if result.get('answer'):
                formatted_results += f"Summary: {result.get('answer')}\n\n"
            
            # Add individual results with URLs for easy citation
            formatted_results += "Sources:\n"
            sources_list = [] # Store URLs separately
            for i, search_result in enumerate(result.get('results', []), 1):
                url = search_result.get('url', 'No URL')
                title = search_result.get('title', 'No Title')
                content = search_result.get('content', 'No content available')
                
                formatted_results += f"{i}. {title}\n"
                formatted_results += f"   URL: {url}\n"
                formatted_results += f"   Content: {content[:200]}...\n\n" # Truncate content for LLM
                
                if url and url != "No URL":
                    sources_list.append(url)
            
            # Return a dictionary containing formatted results and the raw source list
            return {
                "formatted_text": formatted_results,
                "sources": sources_list
            }
        else:
            # Should not happen with current search_web, but handle unexpected types
            print(f"Warning: Unexpected result type from search_web: {type(result)}")
            return str(result) # Convert to string
    else:
        return f"Error: Function {name} is not implemented"

def parse_llm_response(response_text):
    """
    Parse the LLM response to extract function calls
    
    Args:
        response_text (str): Response from the LLM
        
    Returns:
        list: Extracted function calls
    """
    # Regular expression pattern to extract function calls
    pattern = r'\[(.*?)\]'
    
    # Find all matches in the response
    matches = re.findall(pattern, response_text)
    
    if not matches:
        return []
    
    # Process each match
    function_calls = []
    for match in matches:
        # Split by comma, but not within parentheses
        calls = re.findall(r'([^,]+\([^)]*\))', match)
        
        for call in calls:
            # Extract function name and parameters
            func_match = re.match(r'(\w+)\((.*)\)', call.strip())
            if func_match:
                func_name = func_match.group(1)
                params_str = func_match.group(2)
                
                # Parse parameters
                params = {}
                param_matches = re.findall(r'(\w+)=(".*?"|\'.*?\'|\d+|[^,\s]+)', params_str)
                
                for param_name, param_value in param_matches:
                    # Remove quotes if present
                    if (param_value.startswith('"') and param_value.endswith('"')) or \
                       (param_value.startswith("'") and param_value.endswith("'")):
                        param_value = param_value[1:-1]
                    
                    # Convert to int if it's a number
                    if param_value.isdigit():
                        param_value = int(param_value)
                    
                    params[param_name] = param_value
                
                function_calls.append({
                    "name": func_name,
                    "parameters": params
                })
    
    return function_calls

def process_user_input(user_input, time_range="month", status_callback=None):
    """
    Process user input, send to LLM, and handle function calls
    
    Args:
        user_input (str): User's input/question
        time_range (str): Time range for search - 'none', 'day', 'week', 'month', 'year'
        status_callback (function, optional): Callback function to report status updates
        
    Returns:
        dict or str: Dictionary containing response and sources, or error string
    """
    # Use 'month' as default if 'none' or invalid is passed, although UI should handle this.
    effective_time_range = time_range if time_range in ["day", "week", "month", "year"] else "month"
    print(f"\n----- PROCESSING INPUT: '{user_input}' with time_range: '{time_range}' -----")
    
    # Helper function to update status if callback is provided
    def update_status(message, progress=None):
        print(f"STATUS: {message} (Progress: {progress}%)")
        if status_callback:
            status_callback(message, progress)
            
    try:
        # Step 1: Send the user input to the LLM with proper formatting
        update_status("Sending query to Llama-4...", 25)
        
        # Include the selected time range in the user message to guide the model
        time_range_prompt = f"Please use the time range '{time_range}' for your search."
        if time_range == 'none':
            time_range_prompt = "Please perform the search without any specific time range limitation."
            
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"<|header_start|>user<|header_end|>\n\n{user_input}\n\n{time_range_prompt}<|eot|>"}
        ]
        
        print("Sending request to Groq API...")
        try:
            completion = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1024,
                top_p=1,
                stream=False,
                stop=None
            )
            print("Received response from Groq API")
            llm_response = completion.choices[0].message.content
            print(f"LLM Response: {llm_response[:100]}...") # Print first 100 chars
        except Exception as e:
            print(f"ERROR with Groq API: {e}")
            return f"Error communicating with Groq API: {e}"
        
        # Step 2: Parse the response to check for function calls
        update_status("Checking if search is needed...", 35)
        function_calls = parse_llm_response(llm_response)
        print(f"Extracted function calls: {function_calls}")
        
        # If there are no function calls, return the response directly
        if not function_calls:
            update_status("No function calls detected, finalizing response...", 90)
            # Return in expected dictionary format, even without sources
            return {"response": llm_response, "sources": []}
        
        # Step 3: Execute the function calls
        update_status(f"Searching for information within time range: '{time_range}'...", 50)
        function_results = []
        
        for function_call in function_calls:
            update_status(f"Executing {function_call['name']}...", 60)
            try:
                # Ensure time_range from UI is passed if LLM doesn't specify
                if function_call['name'] == 'search_web' and 'time_range' not in function_call.get('parameters', {}):
                    function_call['parameters']['time_range'] = time_range # Use UI value
                
                result = execute_function_call(function_call)
                function_results.append(result)
                print(f"Function call result type: {type(result)}")
            except Exception as e:
                error_msg = f"Error executing function {function_call['name']}: {e}"
                print(error_msg)
                function_results.append(error_msg) # Append error string
        
        # Step 4: Send the function results back to the LLM
        update_status("Analyzing gathered information...", 75)
        
        # Extract formatted text and combine results for LLM
        combined_text_results = []
        all_sources = []
        for result in function_results:
            if isinstance(result, dict) and 'formatted_text' in result:
                combined_text_results.append(result['formatted_text'])
                if 'sources' in result:
                    all_sources.extend(result['sources'])
            elif isinstance(result, str):
                combined_text_results.append(result) # Append error messages or unexpected results
        
        final_combined_results = "\n\n".join(combined_text_results)
        print(f"Combined results length for LLM: {len(final_combined_results)} characters")
        
        # Create a new message for the LLM with the function results
        messages.append({"role": "assistant", "content": f"<|header_start|>assistant<|header_end|>\n\n{llm_response}<|eot|>"})
        messages.append({
            "role": "user", 
            "content": f"<|header_start|>user<|header_end|>\n\nHere are the results from the tools you called:\n\n{final_combined_results}\n\nBased on these results, is the news fake or real? Please analyze the claim.\n\n**IMPORTANT**: Start your response *immediately* with the verdict, followed by your analysis. Use one of the following verdicts: TRUE, FALSE, PARTIALLY TRUE, or INSUFFICIENT INFORMATION. \nExample format:\nVerdict: [VERDICT]\n[Your analysis here...]\n\n**ABSOLUTELY DO NOT** include the URLs or list the sources in your response. The system handles source display separately.<|eot|>"
        })
        
        # Get the final response from the LLM
        update_status("Generating final analysis...", 85)
        try:
            print("Sending final request to Groq API...")
            final_completion = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1024,
                top_p=1,
                stream=False,
                stop=None
            )
            print("Received final response from Groq API")
        except Exception as e:
            print(f"ERROR with final Groq API call: {e}")
            return {"response": f"Error generating final analysis: {e}", "sources": all_sources} # Return error with sources
        
        # Extract content from the final response, removing any header tags if present
        update_status("Finalizing response...", 95)
        final_response = final_completion.choices[0].message.content
        # Clean up the response if it contains header tags
        final_response = re.sub(r'<\|header_start\|>assistant<\|header_end\|>\s*', '', final_response)
        final_response = re.sub(r'<\|eot\|>', '', final_response).strip()
        
        # Create a dictionary with both response and sources (remove duplicates)
        unique_sources = list(dict.fromkeys(all_sources)) 
        response_with_sources = {
            "response": final_response,
            "sources": unique_sources
        }
        
        update_status("Complete!", 100)
        print("----- PROCESSING COMPLETE -----\n")
        return response_with_sources
        
    except Exception as e:
        print(f"ERROR in process_user_input: {e}")
        import traceback
        traceback.print_exc()
        return f"An error occurred during processing: {str(e)}" # Return error string

if __name__ == "__main__":
    # Example usage
    user_input = "Is it true that PM Modi announced 15 lakhs to every Indian citizen?"
    response = process_user_input(user_input)
    print(response)