import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# API Key Configuration
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\SARTHAK\\Downloads\\gen-lang-client-0091686678-84db239ad662.json"

st.title("RAG Application with Gemini Model")

# Load multiple PDFs from "data/" directory
docs = []
directory_path = "C:\\Data"  # Adjust to your folder path
for filename in os.listdir(directory_path):
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(directory_path, filename))
        docs.extend(loader.load())

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
docs = text_splitter.split_documents(docs)

# Create embeddings and vectorstore
embedding = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",

)
vectorstore = Chroma.from_documents(documents=docs, embedding=embedding)

# Set up retriever
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})

# Configure LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", temperature=0, max_tokens=300
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

query = st.chat_input("Ask something:")
if query:
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = rag_chain.invoke({"input": query})
    st.write(response["answer"])
