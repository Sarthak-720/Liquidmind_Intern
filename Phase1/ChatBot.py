import streamlit as st
from interact import reply
# Title
st.title("BASIC CHATBOT POWERED BY GEMINI LLM")

# Initialize session state to store chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Chat input
with st.form(key="chat_form"):
    user_input = st.text_input("Your message:", key="user_input")
    submit = st.form_submit_button("Send")

# Display chat messages
if user_input and submit:
    # Append user's message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    # Example response from the assistant (replace with actual logic)
    bot_response = reply(user_input)
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})

# Render messages in the chat
for message in st.session_state["messages"]:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    elif message["role"] == "assistant":
        st.chat_message("assistant").write(message["content"])
