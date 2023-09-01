
# PubMed Chat: A Python App Leveraging OpenAI's GPT-3.5-turbo and Streamlit Framework

## Context

PubMed is a free search engine that provides access primarily to the MEDLINE database of references and abstracts on life sciences and biomedical topics. It is maintained by the United States National Library of Medicine (NLM) at the National Institutes of Health.

This project presents a Streamlit application that leverages OpenAI's GPT-3.5-turbo model to create an interactive chat interface for querying PubMed. 

## Challenge

The primary challenge was to integrate and harmonize three separate components: the PubMed search functionality, the GPT-3.5-turbo conversational AI model, and the Streamlit framework. 

Key challenges included:
- Identifying the user's intention (searching for articles or requesting a summary of an article)
- Handling search queries and displaying results in an intuitive manner
- Summarizing abstracts in a user-friendly format
- Asking questions about a particular article
- Maintaining the conversational state and search results across interactions in Streamlit

## Solution

To resolve these challenges, we implemented the following solutions:

1. **Identifying User Intent**: We utilized GPT-3.5-turbo's powerful natural language understanding capabilities to classify user input as either a search request or a summary request.

2. **Handling Search Queries**: We integrated the `pymed` Python library to handle PubMed queries based on user input. The GPT-3.5-turbo model helped parse the user's search request, and the results were displayed in a conversational manner.

3. **Summarizing Abstracts**: The GPT-3.5-turbo model was used to generate concise summaries of article abstracts. We indexed the search results, allowing the user to request a summary by referencing the article number.

4. **Maintaining State in Streamlit**: Streamlit's session state was used to store the conversation history and search results, enabling a coherent and continuous chat experience.

## Updates (09-01-2023)

1. **Customization Features**: The app now includes a user_preferences module that allows users to tailor the type of articles or data they frequently search for.

2. **Interaction History**: Integration with Redis, an in-memory DB, to log past interactions, useful for referencing past searches or discussion points.

3. **External Tools**: Integration with tools like DuckDuckGo for cross-referencing information.

4. **Enhanced Summaries**: Summaries are now tailored to different expertise levels, offering insights that are accessible to both laypeople and experts.

## Core Functionalities

1. **PubMed Search**: The app allows users to search for articles on PubMed. The search can be based on different fields such as author, title, abstract, and keywords.

2. **Article Summarization**: The app can provide summaries of specific articles. The user can request a summary by providing the number of the article from the search results.

3. **Intent Classification**: The app uses GPT-3.5 model to interact with the user, understand their queries, and provide responses. It can classify user intent into categories like 'search', 'summary', 'fetch', 'general', 'web_search', and 'follow_up'.

4. **Short-term History**: The app can fetch and display previous interactions between the user and the AI assistant.

5. **Web Search**: The app can perform web searches for non-PubMed related requests requiring internet access.

6. **Follow-up Queries**: The app can handle follow-up queries based on previous interactions and user preferences.

## Outcome

The resulting PubMed Chat is an interactive chatbot that can understand natural language queries, perform PubMed searches, and provide concise summaries of scientific articles. This offers a user-friendly way to access and understand the vast amount of information available on PubMed.


