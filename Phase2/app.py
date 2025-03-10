from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import os
import re
import html
from OCR import extract_details
from llm_integration import ( 
    validate_gst_certificate,
    validate_invoice_data,
    validate_pan_card,
    validate_bol,
    validate_export_declaration,
    chat
)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = r"C:\Hack1\uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.secret_key = os.urandom(24)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/junk")
def junk():
    return render_template("junk.html")

@app.route("/document-upload", methods=["GET", "POST"])
def document_upload():
    if request.method == "POST":
        document_type = request.form["documentType"]
        print(document_type)
        file = request.files.get("file")
        if not file or file.filename == "":
            return "No file uploaded"

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        return redirect(url_for("process_file", doc_type=document_type, file_name=file.filename))

    return render_template("document-upload.html")


@app.route("/chat", methods=["GET", "POST"])
def chat_bot():
    if request.method == "POST":
        user_message = request.form.get("message", "")  # Get the form input from the POST request
        if not user_message:
            return render_template("chat.html", error="No message provided")

        prompt = f"""
        You are a helpful chatbot assistant. Answer the following user question in a conversational and friendly tone: 
        and you are required to only answer the queries regarding the file names listed below. If any other topic is mentioned,
        reply with: I'm only designed to answer specific queries.

        documents: invoice, bill of lading, GST certificate, PAN card, export documents.

        User: {user_message}
        """

        try:
            raw_response = chat(prompt)  # Replace `chat` with your LLM function
            
            # Extract the actual text content from the raw response
            match = re.search(r'text:\s*&quot;(.*?)&quot;', raw_response, re.DOTALL)
            if match:
                chatbot_response = match.group(1).replace("\\n", "\n").strip()  # Clean up escaped newlines and spaces
            else:
                chatbot_response = "Unexpected response format."
            
            return render_template("chat.html", response=chatbot_response)
        except Exception as e:
            return render_template("chat.html", error=str(e))

    return render_template("chat.html")


@app.route("/process/<doc_type>/<file_name>", methods=["GET", "POST"])
def process_file(doc_type, file_name):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)

    if request.method == "POST":
        edited_details = request.form["extracted_details"]
        validation_feedback = process_validation(doc_type, edited_details)

        # session.pop('validation_feedback', None)
        session['validation_feedback'] = validation_feedback

        print(validation_feedback)
        return "hi"
    extracted_text = extract_details(file_path)

    return render_template(
        "edit.html",  
        details=extracted_text,
        file_name=file_name,
        doc_type=doc_type,
    )

@app.route("/feedback/<doc_type>")
def show_feedback(doc_type):

    feedback = session.pop('validation_feedback', 'No feedback available')
    print("this is line 69:"+feedback)

    return render_template("validation-results.html", feedback=format_chat_response(feedback), doc_type=doc_type)



def process_validation(doc_type, extracted_text):
    validation_functions = {
        "gst_certificate": validate_gst_certificate,
        "invoice": validate_invoice_data,
        "pan_card": validate_pan_card,
        "bol": validate_bol,
        "export_declaration": validate_export_declaration,
    }

    validation_func = validation_functions.get(doc_type)
    feedback = validation_func(extracted_text) if validation_func else "Invalid document type"
    feedback = re.sub(r"Parts\s*\{\s*text:\s*\"(.*?)\"\s*\}", r"\1", feedback, flags=re.DOTALL)
    feedback = re.sub(r'role:\s*\"model\"', "", feedback).strip()

    #editing here

    if "text:" in feedback:
        start_index = feedback.index("text:") + len("text:") + 2  
        end_index = feedback.index('}', start_index)
        extracted_text = feedback[start_index:end_index].strip()
        feedback = extracted_text
    
    return feedback.replace("\n", "<br>")

def format_chat_response(response):

    response = html.unescape(response)

    response = re.sub(r'\*\*([^*]+):\*\*', r'<strong>\1:</strong>', response)  # Bold key sections
    response = response.replace("* ", "<li>").replace("\n", "</li>")  # Format as list items

    formatted_response = f"<ul>{response}</ul>"
    return formatted_response

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/signup')
def signup():
     return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)
