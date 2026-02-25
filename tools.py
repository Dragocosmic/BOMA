import pandas as pd
from duckduckgo_search import DDGS
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

def process_uploaded_file(uploaded_file):
    """Reads CSV or Excel and generates text context for the AI."""
    try:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if file_ext == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_ext == 'xlsx':
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_ext in ['xls', 'xlsb']:
            engine = 'xlrd' if file_ext == 'xls' else 'pyxlsb'
            df = pd.read_excel(uploaded_file, engine=engine)
        else:
            return None, f"Unsupported file type: {file_ext}"
        
        context = f"DATASET INFO:\nFile: {uploaded_file.name}\nColumns: {', '.join(df.columns.tolist())}\nTotal rows: {len(df)}\nFirst 5 rows:\n{df.head().to_string(index=False)}"
        return df, context
    except Exception as e:
        return None, f"Error reading file: {e}"

def search_the_web(query):
    """Searches the internet using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found on the web."
        
        context = "WEB SEARCH RESULTS:\n"
        for i, r in enumerate(results):
            context += f"{i+1}. {r['title']}: {r['body']}\n"
        return context
    except Exception as e:
        return f"Web search failed: {e}"

# --- THE DATA EXECUTION AGENT ---
def run_data_agent(df, query, llm):
    """Gives the AI an execution engine to run Pandas code directly."""
    try:
        # THE FIX: We secretly attach a rule to stop the Streamlit chart freezing!
        safe_query = query + "\n\nCRITICAL RULE: If the user asks you to plot, graph, or draw a chart, you MUST save it as 'chart.png' in the current directory using plt.savefig('chart.png') or fig.write_image('chart.png'). DO NOT use plt.show() or fig.show()."
        
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            allow_dangerous_code=True,
            handle_parsing_errors=True
        )
        
        response = agent.invoke(safe_query)
        return response.get("output", "Operation completed.")
    except Exception as e:
        return f"Execution failed: {e}"