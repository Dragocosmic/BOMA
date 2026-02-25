import streamlit as st
import os
from brain import get_active_model
from tools import process_uploaded_file, search_the_web, run_data_agent

# 1. Page Configuration
st.set_page_config(page_title="Boma - Agent", page_icon="🏭", layout="wide")

# 2. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "System Modularized. I am ready to analyze, modify, and visualize your data!"}]

# 3. Sidebar: Settings & File Upload
with st.sidebar:
    st.title("⚙️ System Settings")
    
    # Clean Model Selector
    model_choice = st.selectbox("Select Model", ["Groq (Cloud)", "Ollama (Local)"])
    
    # Secure API Key Retrieval
    api_key = ""
    if model_choice == "Groq (Cloud)":
        try:
            # Looks for the name 'GROQ_API_KEY' in your secrets.toml or Cloud dashboard
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            st.error("API Key missing! Please add 'GROQ_API_KEY' to your Streamlit Secrets.")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Machine Logs", type=["csv", "xlsx", "xls", "xlsb"])
    
    # Initialize the "Brain"
    llm = get_active_model(model_choice, api_key)

# 4. Main UI Header
st.title("🤖 Boma: AI Agent")

# 5. Data Processing Logic
dataset_context = ""
df = None
if uploaded_file:
    df, dataset_context = process_uploaded_file(uploaded_file)
    if df is not None:
        with st.expander("Preview Data"):
            st.dataframe(df.head())
    else:
        st.error(dataset_context)

# 6. Display Chat History (Including persistent charts)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # If the message has a saved chart, show it
        if msg.get("has_chart") and os.path.exists("chart.png"):
            st.image("chart.png")

# 7. Chat Input & Tool Routing
if prompt := st.chat_input("Type a command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not llm:
            st.error("Brain disconnected. Check API key.")
        else:
            with st.spinner("Processing..."):
                extra_context = dataset_context if dataset_context else ""
                
                # --- ROUTE 1: INTERNET SEARCH ---
                if "search" in prompt.lower() or "internet" in prompt.lower():
                    st.info("🌐 Boma is searching the web...")
                    web_results = search_the_web(prompt)
                    extra_context += f"\n\n{web_results}"
                    final_prompt = f"CONTEXT:\n{extra_context}\n\nUSER QUESTION: {prompt}"
                    
                    try:
                        response = llm.invoke(final_prompt)
                        final_text = response.content if hasattr(response, 'content') else response
                        st.markdown(final_text)
                        st.session_state.messages.append({"role": "assistant", "content": final_text})
                    except Exception as e:
                        st.error(f"Error: {e}")

                # --- ROUTE 2: DATA EXECUTION (ETL & CHARTS) ---
                elif df is not None and any(word in prompt.lower() for word in ["data", "sheet", "excel", "plot", "chart", "graph", "visualize"]):
                    st.info("📊 Boma is executing Python analysis...")
                    
                    # Clean old charts
                    if os.path.exists("chart.png"):
                        os.remove("chart.png")

                    # Run Data Agent
                    agent_result = run_data_agent(df, prompt, llm)
                    st.markdown(agent_result)
                    
                    # Check for chart and update history
                    if os.path.exists("chart.png"):
                        st.image("chart.png")
                        st.session_state.messages.append({"role": "assistant", "content": agent_result, "has_chart": True})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": agent_result})

                # --- ROUTE 3: STANDARD CHAT ---
                else:
                    final_prompt = f"CONTEXT:\n{extra_context}\n\nUSER QUESTION: {prompt}" if extra_context else prompt
                    try:
                        response = llm.invoke(final_prompt)
                        final_text = response.content if hasattr(response, 'content') else response
                        st.markdown(final_text)
                        st.session_state.messages.append({"role": "assistant", "content": final_text})
                    except Exception as e:
                        st.error(f"Error: {e}")