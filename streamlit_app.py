import streamlit as st
import openai
from pymed import PubMed
import ast
import json
import uuid
from langchain.llms.openai import OpenAI
from langchain.agents import initialize_agent,AgentType
from langchain.tools import DuckDuckGoSearchRun
from redis_store import store_interaction, fetch_last_n_interactions
from user_profile import user_preferences

# Generate a unique user ID using UUID
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Debug Print user ID 
print(st.session_state.user_id)

# Store OpenAI key
openai.api_key = st.secrets["openaikey"]
openai_api_key = st.secrets["openaikey"]

# Streamlit Sidebar for setting the PubMed Search results, default 3 articles
st.sidebar.markdown("## Settings")

num_results = st.sidebar.slider('Number of search results:', 1, 10, 3, key='num_results_slider')

# Streamlit Sidebar for setting the PubMed Summariztion 
summary_type = st.sidebar.selectbox('Summary Type:', ['Concise', 'Plain Language', 'Detailed'], key='summary_type')

preferred_field, preferred_subfield = user_preferences()
print(preferred_field, preferred_subfield)

# Pubmed Search function 
def search_pubmed(query, field=None):
    pubmed = PubMed(tool="PubMedChat", email="pubmedchat@gmail.com")
    
    if field:
        # if field.lower() == "author":
        #     query = normalize_author_name(query)  # Normalize the author name
        query = f"{query} [{field}]"
        print(f"Search query: {query}")
    try:
        # results = pubmed.query(query, max_results=num_results)
        results = list(pubmed.query(query, max_results=num_results)) ##pymed stores search results as an iterator by default
        print(f"Search results: {results}")
    except Exception as e:
        error_message = f"An error occurred while searching PubMed: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        return []
    
    if not results:  # when search results are none
        return [], True  # return empty list and flag indicating no results
    
    articles = []
    for result in results:
        authors = ', '.join([f"{author['lastname']} {author['initials']}" for author in result.authors])
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{result.pubmed_id}/"
        articles.append({
            "title": result.title,
            "authors": authors,
            "url": pubmed_url,
            "publication_date": result.publication_date,
            "abstract": result.abstract,
            "pmid": result.pubmed_id  # Adding the PubMed ID
        })
    return articles, False

# Function for chat messages 
def chat_with_gpt3(messages):
    typing_message = st.markdown("""
        <style>
            .typing-message {
                border: 1px solid #f0f2f680;
                border-radius: 5px;
                padding: 10px;
                color: #4a4a4a;
                font-size: 16px;
                width: 100%;  
                margin: 10px 0;
                background-color: #f0f2f680;
            }
        </style>
        <div class="typing-message">🤖 is typing...</div>
        """, unsafe_allow_html=True)

    full_response = ""
    for response in openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    ):
        content = response.choices[0].delta.get("content", "")
        full_response += content

    typing_message.empty() ## Deletes the "Ai is typing message"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    return full_response

def search_articles(user_id, response):
    try:
        response_dict = ast.literal_eval(response)
        if isinstance(response_dict, dict) and 'type' in response_dict and 'value' in response_dict:
            field_type = response_dict["type"].lower()
            field_mapping = {
                "author": "Author",
                "title": "Title",
                "abstract": "Abstract",  # Added support for Abstract
                "keywords": "Keywords"   # Added support for Keywords
            }
            field = field_mapping.get(field_type, "Title") # Default to Title if field not recognized
            query = response_dict["value"].strip()

            st.session_state.messages.append({"role": "assistant", "content": f"I'm searching PubMed for '{query}'. Please wait..."})

            results, no_results_flag = search_pubmed(query, field)  # get results and flag from search_pubmed

            if no_results_flag:  # when search results are none
                messages = [
                    {"role": "system", "content": "You are a PubMed AI assistant. The user has searched for articles, but none were found. Provide a friendly concise response to offer search suggestions."},
                    {"role": "user", "content": f"I searched for '{query}'in PubMed but didn't find any results."}
                ]
                no_results_message = chat_with_gpt3(messages)
                st.session_state.messages.append({"role": "assistant", "content": no_results_message})

            # print(f"After appending no_results_message: {st.session_state.messages}")
    
            st.session_state.search_results = results
          
            response = ""  # reset the response

            # Prepare a string to hold all the search results
            search_results_str = ""
            for idx, result in enumerate(results, start=1):
                messages = [
                    {"role": "system", "content": "You are a PubMed AI research assistant. Your task is to provide a brief description of scientific articles, including the title, authors, publication date, key topics, and a pubmed URL."},
                    {"role": "user", "content": f"Provide the title, authors, key topics, and URL for this article? '{result['title']}' by {result['authors']}. The article was published on {result['publication_date']}. Here is a link to the full article: {result['url']}"},
                ]
                response = chat_with_gpt3(messages)
                search_results_str += f"[{idx}] " + response + "\n\n"

                # Store the user's query and the assistant's response
                #store_interaction(user_id, 'response', response)
                store_interaction(st.session_state.user_id, 'query', response)

                st.session_state.messages.append({"role": "assistant", "content": f"[{idx}] " + response + "\n\n"})

    except (ValueError, SyntaxError):
        print(f"Failed to parse GPT-3.5-turbo response: {response}")  # DEBUG

def process_user_input(user_input):
    print("process_user_input() function called")
    messages = [
        {"role": "system", "content": "You are a PubMed AI assistant. Your task is to understand the user's query and convert it to a key-value. If the user wants to search articles by an author or a topic, extract the author's name or the topic from the user's query. For a PubMed search related query return the response in the following format: {'type': 'the type of search', 'value': 'the search term'}. The list of Pubmed search types are 'author','title','keywords','abstract'"},
        {"role": "user", "content": user_input},
    ]
    response = chat_with_gpt3(messages)

    # Store the user's response

    #store_interaction(user_id, 'query', user_input)
    store_interaction(st.session_state.user_id, 'query', user_input)
    
    # Store the assistant's response
    # store_interaction(user_id, 'response', response)
    store_interaction(st.session_state.user_id, 'response', user_input)

    return response

def summarize_article(user_id, user_input, summary_type):
    ## Note: summarizing articles by number is temporary, PMID based or Titles? 
    # Extract number from user input
    number = [int(s) for s in user_input.split() if s.isdigit()]
    if number and 1 <= number[0] <= len(st.session_state.search_results):
        article = st.session_state.search_results[number[0] - 1]
        abstract = article["abstract"]
        messages = [
            {"role": "user", "content": f"Here is an abstract of a pubmed article: {abstract}. Could you provide a {summary_type.lower()} summary of the abstract?"},
        ]
        summary = chat_with_gpt3(messages)

        # Store the user's query and the assistant's response
        # store_interaction(user_id, 'response', f"'{article['title']}': {summary}")
        store_interaction(st.session_state.user_id, 'response', f"Here is a summary of the article titled '{article['title']}': {summary}")

        return f"Here is a summary of the article's abstract titled '{article['title']}': {summary}"
    
def classify_user_input(user_input):
    # key word based user intent classification for "Fetch" intent is temporary. Research for alternatives 
    # Define keywords for "fetch" and "summary" intents
    fetch_keywords = ["previous", "past", "history", "remember", "recall", "retrieve", "fetch"]
    summary_keywords = ["summary","summarise", "summarize", "details", "explain", "overview"]

    if any(keyword in user_input.lower() for keyword in fetch_keywords):
        return 'fetch'
    if any(keyword in user_input.lower() for keyword in summary_keywords):
        return 'summary'

    
    messages = [
    {"role": "system", "content": "You are a PubMed AI assistant. Given the user's query, your task is to classify the most likely intent. The user's intent can be one of the following: 'search' for PubMed articles, 'summarize' a specific article, 'web_search' for non-pubmed related request requiring internet access, 'follow_up' to ask a question related to previous search results. Use 'general' for queries outside the scope of PubMed. Please respond with exactly one of these terms: 'search', 'summarize', 'general', 'web_search', 'follow_up'"},
    {"role": "user", "content": user_input},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    content = response.choices[0].message['content']
    response = content.lower()
    print(f"classified intent: {response}")

    if response == 'search':
        return 'search'
    elif response == 'follow_up':
        return 'follow_up'
    elif response == 'web_search':
        return 'web_search'
    else: 
        return 'general'
    
def handle_fetch_intent(user_id, n):
    interactions = fetch_last_n_interactions(user_id, n)
    messages = format_interactions_for_gpt3(interactions)
    response = chat_with_gpt3(messages)
    return response

def format_interactions_for_gpt3(interactions):
    formatted_interactions = [{"role": "system", "content": "You are a PubMed AI assistant. Use the context of the user's previous interactions to inform your responses. If the user asks about a previous interaction, provide a summary of the user's past questions in a structured way. In the response refer to the user as You and the AI assistant as I or in the first-person"}]
    for interaction in interactions:
        interaction_dict = ast.literal_eval(interaction.decode("utf-8"))  # Convert bytes to string and parse string to dictionary
        role = "user" if interaction_dict["type"] == "query" else "assistant"
        content = interaction_dict["content"]
        formatted_interactions.append({"role": role, "content": content})
    return formatted_interactions

def format_interactions_for_user(interactions):
    formatted_interactions = []
    for interaction in interactions:
        interaction_dict = ast.literal_eval(interaction.decode("utf-8"))  # Convert bytes to string and parse string to dictionary
        if interaction_dict["type"] == "query":  # We only want the user's questions
            content = interaction_dict["content"]
            formatted_interactions.append(content)
    # Format the interactions for the user
    formatted_interactions = "\n".join(f"{idx+1}. {question}" for idx, question in enumerate(formatted_interactions))
    return formatted_interactions

def search_web(query):
    # Initialize the OpenAI module, load the DuckDuckGoSearch tool, and run the search query using an agent
    llm = OpenAI(temperature=0, openai_api_key=openai_api_key, verbose=True, streaming=True)
    search_agent = initialize_agent(
        tools=[DuckDuckGoSearchRun(name="Search")],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True)
    result = search_agent.run(query)
    print(result)
    return result

def process_web_search_input(user_input):
    print("DEBUG: process_web_search_input() function called\n") 
    # Perform the web search
    search_results = search_web(user_input)
    print(search_results)

    # Create a system message to set the context for GPT-3
    system_message = {
        "role": "assistant", 
        "content": "You are a web search assistant for Medical queries. Given the search results, generate a user-friendly response summarizing the results."
    }

    # User message with the search results
    user_message = {"role": "user", "content": str(search_results)}

    # Send messages to GPT-3 for processing
    response = chat_with_gpt3([system_message, user_message])
    print(response)
    return response

def handle_follow_up_query(user_id, follow_up_query, preferred_field, preferred_subfield):
    print("DEBUG: Follow Up triggered\n")
    # Print user preferences for debugging
    print("User Preferences:", preferred_field, preferred_subfield)
    
    # Fetch the last 5 interactions
    last_interactions = fetch_last_n_interactions(user_id, n=5)

    # Construct user preferences content
    preferences_content = "User Preferences:\n"
    for field, subfields in preferred_subfield.items():
        preferences_content += f"  {field}: {', '.join(subfields)}\n"

    # Construct the context for the system message
    system_content = "You are a PubMed AI assistant. Respond to user queries based on the previous interactions and provided preferences.\n"
    system_content += preferences_content
    for interaction_bytes in last_interactions:
        interaction_str = interaction_bytes.decode('utf-8')
        interaction = json.loads(interaction_str)
        role = "Assistant" if interaction["type"] == "response" else "User"
        system_content += f"{role}: {interaction['content']}\n"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": follow_up_query}
    ]
    # Print messages for debugging
    print("Messages sent to the model:\n")
    print(messages)

    # Query Chat model with context window
    response = chat_with_gpt3(messages)

    # Store the user's query and the assistant's response
    # store_interaction(user_id, 'query', follow_up_query)
    # store_interaction(user_id, 'response', response)

    store_interaction(st.session_state.user_id, 'query', follow_up_query)
    store_interaction(st.session_state.user_id, 'response', response)

    return response


def main():
    st.title("PubMed Chat 🤖")

    st.warning('⚠️ PubMed Chat is designed for research purposes and does not replace medical advice\n. Always verify the information independently and seek professional assistance for medical inquiries and adverse events')

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.search_results = []  # initialize search results in session state

    user_input = st.chat_input("You:")
    print(f"User Input: {user_input}")  # Debug print
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # print(f"Before updating chat: {st.session_state.messages}")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_intent = classify_user_input(user_input)
      
        if user_intent == 'search':
            response = process_user_input(user_input)
            print(f"After process_user_input: {st.session_state.messages}")
            st.session_state.messages.append({"role": "assistant", "content": response})
            print(f"After search_articles: {st.session_state.messages}\n")
            search_articles(st.session_state.user_id, response)
        elif user_intent == 'summary':
            response = summarize_article(st.session_state.user_id, user_input,summary_type)
            st.session_state.messages.append({"role": "assistant", "content": response})
        elif user_intent == 'fetch':
            interactions = fetch_last_n_interactions(st.session_state.user_id, 3)  # Fetch the last 3 interactions
            formatted_interactions = format_interactions_for_gpt3(interactions)  # Format the interactions for GPT-3

            system_message = {"role": "system", "content": "You are a PubMed AI assistant. The user has requested a summary of their previous interactions. Please provide a concise summary of the user's questions and your responses, referring to the user and yourself in the first and second person respectively."}
            formatted_interactions.append(system_message)

            response = chat_with_gpt3(formatted_interactions)
            st.session_state.messages.append({"role": "assistant", "content": response})
        elif user_intent == 'general':
            messages = [
                {"role": "system", "content": "You are PubMed AI assistant. The user has made a general or unclear request. You are forbidden to respond to topics outside of PubMed or the Medical Domain.Respond in a friendly and helpful manner, guiding them to use this chatbot's functions effectively. "},
                {"role": "user", "content": user_input}
            ]
            response = chat_with_gpt3(messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
        elif user_intent == 'web_search':
            print("Web search section triggered\n")
            response = process_web_search_input(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})
        elif user_intent == 'follow_up':
            print("Follow Up triggered\n")
            response = handle_follow_up_query(st.session_state.user_id, user_input, preferred_field, preferred_subfield)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
