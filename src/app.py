import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate             
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI            
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import pymysql
pymysql.install_as_MySQLdb()

load_dotenv()

def init_database(host, port, user, password, database):
    db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_url)


def get_sql_chain(db):
    template = '''
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.

    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}

    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.

    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT Name FROM Artist LIMIT 10;

    Your turn:

    Question: {question}
    SQL Query:
    '''

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")     

    def get_schema(_):
        return db.get_table_info()
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )


def get_response(user_query: str, db: SQLDatabase, chat_history: list):
    sql_chain = get_sql_chain(db)

    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}

    NOTE : along with the answer provide table format if it is possible.
    Remember to follow these guidelines:
    1. If user do not specify any table name then assume the table name is 'emp'
   
    Dangerous Operations:
    - If the SQL query contains any dangerous operations like DELETE, DROP, UPDATE, or ALTER, do not execute the query. Instead, respond with "I'm sorry, but I cannot execute queries that modify or delete data."
    """

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")      

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=lambda _: db.get_table_info(),
            response=lambda vars: db.run(vars['query'])
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke({
        "chat_history": chat_history,
        "question": user_query
    })


<<<<<<< HEAD
st.set_page_config("DataTalk Pro", page_icon='💬')
=======
# Page configuration
st.set_page_config(
    page_title="DataTalk Pro",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for dark glassmorphism theme
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(26, 26, 46, 0.7);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #4facfe;
        font-weight: 700;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 0 0 20px rgba(79, 172, 254, 0.5);
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Chat message containers */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        color: white;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #4facfe;
        box-shadow: 0 0 10px rgba(79, 172, 254, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 172, 254, 0.5);
    }
    
    /* Chat input */
    .stChatInput > div > div > textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        color: white;
        backdrop-filter: blur(10px);
    }
    
    .stChatInput > div > div > textarea:focus {
        border-color: #4facfe;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.3);
    }
    
    /* Success/Error messages */
    .stSuccess, .stError {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar header */
    [data-testid="stSidebar"] h2 {
        color: #4facfe;
        font-weight: 600;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Labels */
    .stTextInput label, .stNumberInput label {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 500;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(79, 172, 254, 0.5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(79, 172, 254, 0.7);
    }
    
    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.1);
    }
    
    # /* Hide Streamlit branding */
    # #MainMenu {visibility: on;}
    # footer {visibility: on;}
    
    /* Chat message avatar styling */
    .stChatMessage [data-testid="chatAvatarIcon-user"],
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1> &nbsp;&nbsp;&nbsp;&nbsp;DataTalk Pro</h1>
        <p>Intelligent Database Conversations Powered by AI</p>
    </div>
""", unsafe_allow_html=True)
>>>>>>> b80ae19f4f0f622af18fa2c89369ae5ca1937683

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [
        AIMessage(content="Hello! I'm DataTalk Pro. Ask me anything about your data or database structure.")
    ]

<<<<<<< HEAD
st.title("💬 DataTalk Pro")


with st.sidebar:
    st.header("💬 DataTalk Pro")
=======

with st.sidebar:
    st.markdown("### 🔌 Database Connection")
>>>>>>> b80ae19f4f0f622af18fa2c89369ae5ca1937683
    st.markdown("---")

    host = st.text_input("Host", value="sql8.freesqldatabase.com", key='host')
    port = st.text_input("Port", value="3306", key='port')
    user = st.text_input("User", value="sql8809948", key='user')
    password = st.text_input("Password", type="password", value="vFh7Mqw9PP", key='password')
    database = st.text_input("Database", value="sql8809948", key='database')

    if st.button("🚀 Connect", use_container_width=True):
        with st.spinner("Connecting to database..."):
            try:
                db = init_database(
                    st.session_state['host'],
                    st.session_state['port'],
                    st.session_state['user'],
                    st.session_state['password'],
                    st.session_state['database']
                )
                st.success("✅ Connected successfully!")
                st.session_state['db'] = db
            except Exception as e:
                st.error(f"❌ Connection error: {e}")


for message in st.session_state['chat_history']:
    if isinstance(message, AIMessage):
        with st.chat_message("AI", avatar="🤖"):
            st.markdown(message.content)
    else:
        with st.chat_message("Human", avatar="👤"):
            st.markdown(message.content)


user_query = st.chat_input("💭 Ask me anything about your database...")
if user_query is not None and user_query.strip() != "":
    if 'db' not in st.session_state:
        st.error("⚠️ Please connect to a database first from the sidebar.")
        st.stop()

    st.session_state["chat_history"].append(HumanMessage(content=user_query))

    with st.chat_message("Human", avatar="👤"):
        st.markdown(user_query)

    with st.chat_message("AI", avatar="🤖"):
        response = get_response(
            user_query,
            st.session_state['db'],
            st.session_state['chat_history']
        )

        if response is None or response.strip() == "":
            response = "I am sorry, I could not find an answer to your question."
        elif "error" in response.lower():
            response = "There was an error executing the query."
        st.markdown(response)

    st.session_state["chat_history"].append(AIMessage(content=response))
