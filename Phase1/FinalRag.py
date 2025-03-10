import os
import concurrent.futures
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Parallel PDF loading and splitting
def load_and_split_pdf(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    print(len(docs))
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)  # Smaller chunks
    return text_splitter.split_documents(docs)

# API Credentials Configuration
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\SARTHAK\\Downloads\\gen-lang-client-0091686678-84db239ad662.json"

st.title("RAG Application with Gemini LLM")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load and process PDFs in parallel
docs = []
directory_path = "C:\\Data"  # Adjust to your folder path

# Check if the vectorstore already exists, if not, create it
if not os.path.exists("C://Chroma_Storage"):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for filename in os.listdir(directory_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(directory_path, filename)
                futures.append(executor.submit(load_and_split_pdf, file_path))

        for future in concurrent.futures.as_completed(futures):
            docs.extend(future.result())

    # Create embeddings and vectorstore
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", timeout=60)
    vectorstore = Chroma.from_documents(documents=docs, embedding=embedding, persist_directory="C://Chroma_Storage")
else:
    # Load precomputed vectorstore
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", timeout=60)
    vectorstore = Chroma(persist_directory="C://Chroma_Storage", embedding_function=embedding)

# Set up retriever for fast similarity search
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})

# Configure LLM with reduced tokens for faster responses
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", temperature=0.2, max_tokens=50  # Reduced max tokens for quicker response
)

# Prompt Template
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know, say so. Keep the answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Caching query processing to speed up repeated queries
@st.cache_data
def process_query(query):
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain.invoke({"input": query})

# Chat functionality
query = st.chat_input("Ask something:")
if query:
    try:
        response = process_query(query)  # Cached query processing
        st.session_state.chat_history.append({"query": query, "response": response["answer"]})
    except Exception as e:
        st.session_state.chat_history.append({"query": query, "response": f"Error: {e}"})

# Display Chat History
for entry in st.session_state.chat_history[-50:]:
    st.write(f" {entry['query']}")
    st.write(f" {entry['response']}")
    st.write("---")
