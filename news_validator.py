import streamlit as st
import logging
import time
import re
from app import process_user_input

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="Fake News Validator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to format text with clickable citations
def format_with_citations(text):
    """Format text to convert URLs into clickable links"""
    # Handle numbered lists with URLs
    pattern = r'(\d+\.\s*)(https?://[^\s\)]+)'
    text = re.sub(pattern, r'\1[\2](\2)', text)
    
    # Handle URLs in parentheses
    pattern = r'\((https?://[^\s\)]+)\)'
    text = re.sub(pattern, r'([\1](\1))', text)
    
    # Handle raw URLs
    pattern = r'(?<!\[)(https?://[^\s\)]+)(?!\])'
    text = re.sub(pattern, r'[\1](\1)', text)
    
    return text

# Function to display sources with clickable links
def display_sources(sources):
    """Display a list of sources as clickable links"""
    if not sources:
        return
    
    st.markdown("### 📚 Sources Used:")
    for i, source in enumerate(sources, 1):
        # Create a clickable markdown link
        st.markdown(f"{i}. [{source}]({source})", unsafe_allow_html=False)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem;
    }
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #E5E7EB;
    }
    .result-container {
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        margin-top: 1rem;
    }
    .sources-container {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
        margin-top: 1rem;
    }
    .footer {
        text-align: center;
        color: #6B7280;
        font-size: 0.8rem;
        margin-top: 2rem;
    }
    .verdict-true {
        color: #10B981;
        font-weight: bold;
    }
    .verdict-false {
        color: #EF4444;
        font-weight: bold;
    }
    .verdict-partial {
        color: #F59E0B;
        font-weight: bold;
    }
    .verdict-insufficient {
        color: #6B7280;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.image("https://i.imgur.com/JR8bT9Q.png", width=100)
    st.markdown("### About")
    st.info(
        "This application uses Llama-4 AI to analyze news headlines and determine "
        "if they are real or fake. It searches the web for relevant information "
        "and provides sources to back up its analysis."
    )
    
    st.markdown("### How it works")
    st.markdown("""
    1. Enter your news headline or claim
    2. AI searches for information via Tavily API
    3. Results are analyzed by Llama-4
    4. You get a verdict with source citations
    """)

# Main content area
st.markdown("<h1 class='main-header'>🔍 Fake News Validator</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Check if a news headline is real or fake</p>", unsafe_allow_html=True)

# Session state for storing user input and time range selection
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'selected_time_range' not in st.session_state:
    st.session_state.selected_time_range = "month" # Default time range

# Function to update user input in session state
def set_example(text):
    st.session_state.user_input = text

# Function to update selected time range
def set_time_range(time_range):
    st.session_state.selected_time_range = time_range

# User input
user_input = st.text_area(
    "Enter a news headline or claim to verify:",
    value=st.session_state.user_input,
    height=100,
    placeholder="Example: Is it true that Elon Musk is buying Twitter?"
)

# Time Range selection
col1, col2 = st.columns([1, 4]) # Adjusted column ratio
with col1:
    st.markdown("#### Time Range:")
    st.caption("Limit search results")

with col2:
    time_options = ["none", "day", "week", "month", "year"]
    time_labels = ["Any Time", "Past Day", "Past Week", "Past Month", "Past Year"] # User-friendly labels
    # Find the index of the current selection
    try:
        current_index = time_options.index(st.session_state.selected_time_range)
    except ValueError:
        current_index = time_options.index("month") # Default to month if value is invalid
        st.session_state.selected_time_range = "month"
        
    selected_time_label = st.radio(
        "Select search time range",
        options=time_labels, # Show user-friendly labels
        index=current_index,
        horizontal=True,
        label_visibility="collapsed",
        help="Choose the time period for search results. 'Any Time' removes the time limit."
    )
    # Get the corresponding value ('none', 'day', etc.)
    selected_time_value = time_options[time_labels.index(selected_time_label)]
    
    # Update session state if changed
    if selected_time_value != st.session_state.selected_time_range:
        st.session_state.selected_time_range = selected_time_value

# Display currently selected time range with styling
st.markdown(
    f"<div style='margin-bottom:1rem;'><small>Searching within: <strong style='color:#3B82F6;'>{selected_time_label}</strong></small></div>",
    unsafe_allow_html=True
)

# Example buttons
st.markdown("#### Try these examples:")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.button("PM Modi and 15 lakhs", 
              on_click=set_example, 
              args=["Is it true that PM Modi announced 15 lakhs to every Indian citizen?"],
              help="Check this popular claim")
        
with col2:
    st.button("Rahul Gandhi's MP post", 
              on_click=set_example, 
              args=["Did Rahul Gandhi resign his MP post recently?"],
              help="Check this political claim")

with col3:
    st.button("India's Mars mission", 
              on_click=set_example, 
              args=["Did India successfully send a spacecraft to Mars for less than $100 million?"],
              help="Check this space achievement claim")

# Status display containers
status = st.empty()
progress = st.empty()
result_container = st.container()

# Process button
if st.button("Verify This Claim", type="primary") and user_input:
    # Show processing status
    status.info("Processing your request...")
    progress_bar = progress.progress(0)
    
    # Update progress periodically to show activity
    for percent_complete in range(0, 51, 10):
        progress_bar.progress(percent_complete)
        if percent_complete < 50:
            time.sleep(0.1)
    
    try:
        # Call the processing function with selected time range
        with st.spinner(f"Analyzing information from the {selected_time_label.lower()}..."):
             # Pass the selected time range to the processing function
            result = process_user_input(user_input, 
                                        time_range=st.session_state.selected_time_range, 
                                        status_callback=None)
             
            # Extract response and sources from the result
            if isinstance(result, dict):
                analysis_text = result.get("response", "")
                sources = result.get("sources", [])
            else:
                # Fallback for older format or error messages
                analysis_text = result
                sources = []
            
            # Format the response text
            formatted_result = format_with_citations(analysis_text)
            
            # Show progress completing
            for percent_complete in range(50, 101, 10):
                progress_bar.progress(percent_complete)
                if percent_complete < 100:
                    time.sleep(0.1)
            
            # Clear the status message and progress bar
            status.empty()
            progress.empty()
            
            # Display the results
            st.markdown("### Results:")
            
            # Extract Verdict and Analysis
            verdict = ""
            analysis_body = ""
            if analysis_text.startswith("Verdict:"):
                lines = analysis_text.split('\n', 1)
                verdict_line = lines[0].replace("Verdict:", "").strip()
                # Map verdict to color and icon
                verdict_colors = {
                    "TRUE": "#22C55E",  # Green
                    "FALSE": "#EF4444", # Red
                    "PARTIALLY TRUE": "#F59E0B", # Amber
                    "INSUFFICIENT INFORMATION": "#6B7280" # Gray
                }
                verdict_icons = {
                    "TRUE": "✅",
                    "FALSE": "❌",
                    "PARTIALLY TRUE": "⚠️",
                    "INSUFFICIENT INFORMATION": "❓"
                }
                color = verdict_colors.get(verdict_line.upper(), "#6B7280")
                icon = verdict_icons.get(verdict_line.upper(), "ℹ️")
                verdict = f"<strong style='color:{color};'>{icon} {verdict_line.upper()}</strong>"
                if len(lines) > 1:
                    analysis_body = lines[1].strip()
            else:
                # If format is unexpected, display as is
                analysis_body = analysis_text

            # Display Verdict and Analysis with better separation
            st.markdown("---") # Add a horizontal rule
            if verdict:
                st.markdown(f"### Verdict: {verdict}", unsafe_allow_html=True)
                st.markdown("#### Analysis")
            else:
                 st.markdown("### Analysis") # Fallback if no verdict found
            st.markdown(analysis_body)
            st.markdown("---") # Add another horizontal rule
            
            # Display sources if any
            if sources:
                st.markdown("### 📚 Sources Consulted:")
                # Use columns for better layout
                num_columns = 3 # Adjust as needed
                cols = st.columns(num_columns)
                for i, source_url in enumerate(sources):
                    with cols[i % num_columns]:
                        st.markdown(f"[{source_url}]({source_url})", unsafe_allow_html=False)

    except Exception as e:
        # Show error message
        status.error(f"Error: {str(e)}")
        progress.empty()

# Footer
st.markdown("<div class='footer'>Fake News Validator • Powered by Llama-4, Groq, and Tavily • 2025</div>", 
           unsafe_allow_html=True)
