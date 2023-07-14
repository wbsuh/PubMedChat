import streamlit as st
import openai
from pymed import PubMed
import ast
import time

openai.api_key = st.secrets["openaikey"]

def search_pubmed(query, field=None):
    pubmed = PubMed(tool="PubMedChat", email="wonbae_suh@hotmail.com")
    
    if field:
        query = f"{query} [{field}]"
    
    results = pubmed.query(query, max_results=3)
    articles = []
    for result in results:
        authors = ', '.join([f"{author['lastname']} {author['initials']}" for author in result.authors])
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{result.pubmed_id}/"
        articles.append({
            "title": result.title,
            "authors": authors,
            "url": pubmed_url,
            "publication_date": result.publication_date,
            "abstract": result.abstract
        })
    return articles

def chat_with_gpt3(messages):
    full_response = ""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for response in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        ):
            content = response.choices[0].delta.get("content", "")
            for char in content:
                full_response += char
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)
            message_placeholder.markdown(full_response)
        
    return full_response

def process_user_input(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Your task is to understand the user's query and provide a helpful and conversational response. If the user wants to search articles by an author or a topic, extract the author's name or the topic from the user's query. For a search related query return the response in the following format: {'type': 'the type of search', 'value': 'the search term'}"},
        {"role": "user", "content": user_input},
    ]

    response = chat_with_gpt3(messages)
    st.session_state.messages.append({"role": "assistant", "content": response})

    return response

def search_articles(response):
    try:
        response_dict = ast.literal_eval(response)
        if isinstance(response_dict, dict) and 'type' in response_dict and 'value' in response_dict:
            field = "Author" if response_dict["type"].lower() == "author" else "Title"
            query = response_dict["value"].strip()

            st.session_state.messages.append({"role": "assistant", "content": f"I'm searching PubMed for '{query}'. Please wait..."})
            with st.chat_message("assistant"):
                st.markdown(f"I'm searching PubMed for '{query}'. Please wait...")

            results = search_pubmed(query, field)
            st.session_state.search_results = results
            print(f"DEBUG: Stored {len(st.session_state.search_results)} search results in session state")
            response = ""  # reset the response

            for idx, result in enumerate(results, start=1):
                messages = [
                    {"role": "system", "content": "You are an AI research assistant. Your task is to provide a brief description of scientific articles, including the title, authors, key topics, and a pubmed URL."},
                    {"role": "user", "content": f"Can you provide the title, authors, key topics, and URL for this article? '{result['title']}' by {result['authors']}. The article was published on {result['publication_date']}. Here is a link to the full article: {result['url']}"},
                ]
                response += f"[{idx}] " + chat_with_gpt3(messages) + "\n\n"
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.messages.append({"role": "assistant", "content": "Would you like a summary of any of these articles? If so, please specify the article by its number."})
    except (ValueError, SyntaxError):
        print(f"Failed to parse GPT-3.5-turbo response: {response}")  # DEBUG

def handle_article_question(user_input):
    # Extract number from user input
    number = [int(s) for s in user_input.split() if s.isdigit()]
    if number and 1 <= number[0] <= len(st.session_state.search_results):
        article = st.session_state.search_results[number[0] - 1]
        title = article["title"]
        messages = [
            {"role": "system", "content": f"You are a knowledgeable AI assistant. The user is asking a question about the following scientific article: '{title}'. Try to provide a helpful response."},
            {"role": "user", "content": user_input},
        ]
        response = chat_with_gpt3(messages)
        st.session_state.messages.append({"role": "assistant", "content": response})

def summarize_article(user_input):
    # Extract number from user input
    number = [int(s) for s in user_input.split() if s.isdigit()]
    if number and 1 <= number[0] <= len(st.session_state.search_results):
        article = st.session_state.search_results[number[0] - 1]
        abstract = article["abstract"]
        messages = [
            {"role": "user", "content": f"Here is an abstract of a research article: {abstract}. Could you provide a concise summary?"},
        ]
        summary = chat_with_gpt3(messages)
        st.session_state.messages.append({"role": "assistant", "content": f"Here is a summary of the article titled '{article['title']}': {summary}"})


def classify_user_input(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. The user is going to provide a command related to searching PubMed articles, summarizing an article, or asking a question about an article. Identify if the user's intent is to 'search', 'summarize', or 'ask'."},
        {"role": "user", "content": user_input},
    ]

    response = chat_with_gpt3(messages)
    response = response.lower()

    if 'summarize' in response:
        return 'summary'
    elif 'ask' in response or 'question' in response:
        return 'ask'
    else:
        return 'search'

def main():
    st.title("PubMed Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.search_results = []  # initialize search results in session state
        st.session_state.messages.append({
            "role": "assistant", 
            "content": (
                "Hello! I'm your AI assistant, ready to help you find articles on PubMed. "
                "You can ask me to find articles by a certain author or on a specific topic. "
                "Let's start!"
            )
        })

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("You:")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        user_intent = classify_user_input(user_input)

        if user_intent == 'search':
            response = process_user_input(user_input)
            search_articles(response)
        elif user_intent == 'summary':
            summarize_article(user_input)
        elif user_intent == 'ask':
            handle_article_question(user_input)

if __name__ == "__main__":
    main()
