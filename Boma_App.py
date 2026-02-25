import streamlit as st
import os  # NEW: Allows Streamlit to read files on your computer
from brain import get_active_model
from tools import process_uploaded_file, search_the_web, run_data_agent

st.set_page_config(page_title="Boma - Industrial Agent", page_icon="🏭", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "System Modularized. I am ready to analyze, modify, and visualize your data!"}]

with st.sidebar:
    st.title("⚙️ System Settings")
    # Clean, simple model selector (Gemini-style)
    model_choice = st.selectbox("Select Model", ["Groq (Cloud)", "Ollama (Local)"])
    
    # Securely fetch the API key from the hidden vault
    if model_choice == "Groq (Cloud)":
        try:
            api_key = st.secrets["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"]
        except Exception:
            api_key = ""
            st.error("API Key missing! Please add it to Streamlit Secrets.")
    else:
        api_key = ""

    uploaded_file = st.file_uploader("Upload Machine Logs", type=["csv", "xlsx", "xls", "xlsb"])
    
    llm = get_active_model(model_choice, api_key)
    
st.title("🤖 Boma: Industrial AI Agent")

dataset_context = ""
df = None
if uploaded_file:
    df, dataset_context = process_uploaded_file(uploaded_file)
    if df is not None:
        with st.expander("Preview Data"):
            st.dataframe(df.head())
    else:
        st.error(dataset_context)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
                
                # --- TOOL ROUTER ---
                
                # Route 1: Internet Search
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

                # Route 2: Data Execution (ETL & Charts)
                # UPGRADED: Added chart trigger words
                elif df is not None and any(word in prompt.lower() for word in ["data", "sheet", "excel", "column", "filter", "plot", "chart", "graph", "visualize"]):
                    st.info("📊 Boma is writing and executing Python code...")
                    
                    # 1. Clean up any old charts before starting
                    if os.path.exists("chart.png"):
                        os.remove("chart.png")

                    # 2. Run the agent
                    agent_result = run_data_agent(df, prompt, llm)
                    st.markdown(agent_result)
                    st.session_state.messages.append({"role": "assistant", "content": agent_result})
                    
                    # 3. NEW: If a chart was created, display it!
                    if os.path.exists("chart.png"):
                        st.image("chart.png")
                        st.success("Chart generated and displayed successfully!")

                # Route 3: Standard Chat
                else:
                    final_prompt = f"CONTEXT:\n{extra_context}\n\nUSER QUESTION: {prompt}" if extra_context else prompt
                    try:
                        response = llm.invoke(final_prompt)
                        final_text = response.content if hasattr(response, 'content') else response
                        st.markdown(final_text)
                        st.session_state.messages.append({"role": "assistant", "content": final_text})
                    except Exception as e:
                        st.error(f"Error: {e}")