import os
import google.generativeai as genai

# Configure the Gemini API
def find_details(input_data, detail):
    genai.configure(api_key="AIzaSyDLvYXhcoSGk1uzik08RXmyx1x9h8OatzI")
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
        ]
    )
    response = chat_session.send_message(f"Search for the given {detail} in the given data and return the date of invoice along with the date on which user uploaded the invoice in the system, keep the message precise: {input_data}")
    return response.text
