
# PubMed Chat: A Streamlit App Leveraging OpenAI's GPT-3.5-turbo

## Context

PubMed is a free-to-access search engine that offers information on topics ranging from medicine, nursing, pharmacy, dentistry, veterinary medicine, and health care. It provides access to MEDLINE, a database of citations and abstracts in the fields of medicine, nursing, dentistry, veterinary medicine, health care systems, and preclinical sciences.

This project presents a Streamlit application that leverages OpenAI's GPT-3.5-turbo model to create an interactive chat interface for querying PubMed. 

## Challenge

The primary challenge was to integrate and harmonize three separate components: the PubMed search functionality, the GPT-3.5-turbo conversational AI model, and the Streamlit framework. 

Key challenges included:
- Identifying the user's intention (searching for articles or requesting a summary of an article)
- Handling search queries and displaying results in an intuitive manner
- Summarizing abstracts in a user-friendly format
- Maintaining the conversational state and search results across interactions in Streamlit

## Solution

To resolve these challenges, we implemented the following solutions:

1. **Identifying User Intent**: We utilized GPT-3.5-turbo's powerful natural language understanding capabilities to classify user input as either a search request or a summary request.

2. **Handling Search Queries**: We integrated the `pymed` Python library to handle PubMed queries based on user input. The GPT-3.5-turbo model helped parse the user's search request, and the results were displayed in a conversational manner.

3. **Summarizing Abstracts**: The GPT-3.5-turbo model was used to generate concise summaries of article abstracts. We indexed the search results, allowing the user to request a summary by referencing the article number.

4. **Maintaining State in Streamlit**: Streamlit's session state was used to store the conversation history and search results, enabling a coherent and continuous chat experience.

## Outcome

The resulting application is an interactive chatbot that can understand natural language queries, perform PubMed searches, and provide concise summaries of scientific articles. This offers a user-friendly way to access and understand the vast amount of information available on PubMed.

---

