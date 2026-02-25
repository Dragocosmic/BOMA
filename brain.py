import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama

def get_active_model(choice, key):
    """Initializes and returns the selected LLM."""
    try:
        if choice == "Groq (Cloud)":
            if not key:
                return None
            return ChatGroq(model="llama-3.3-70b-versatile", api_key=key, temperature=0.0)
        else:
            return Ollama(model="llama3.1", temperature=0.2)
    except Exception as e:
        st.sidebar.error(f"Connection Error: {e}")
        return None