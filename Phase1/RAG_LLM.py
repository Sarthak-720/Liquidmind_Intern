import streamlit as st
import os
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Configure Gemini API Key
genai.configure(api_key="AIzaSyDLvYXhcoSGk1uzik08RXmyx1x9h8OatzI")

st.title("RAG Application built on Gemini Model")

# Load multiple PDFs from the "data/" directory
docs = []
directory_path = "C:\Data"  # Folder containing multiple PDF files
for filename in os.listdir(directory_path):
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(directory_path, filename))
        docs.extend(loader.load())

# Split the documents into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
docs = text_splitter.split_documents(docs)

# Create vectorstore
vectorstore = Chroma.from_documents(
    documents=docs, 
    embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
)

# Set up retriever
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})

# Configure LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, max_tokens=300, timeout=None)

# Chat Input
query = st.chat_input("Ask something: ") 

# Define Prompt Template
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Handle Query
if query:
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = rag_chain.invoke({"input": query})

    st.write(response["answer"])
