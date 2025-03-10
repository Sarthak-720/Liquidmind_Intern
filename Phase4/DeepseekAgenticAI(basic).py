
import json
import ollama
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

# Azure Document Intelligence Credentials (Replace with your actual values)
AZURE_ENDPOINT = "https://liquidmindinvoice.cognitiveservices.azure.com/"
AZURE_KEY = "de011e6175a14593bfdff3bb210c65b2"
MODEL_ID = "prebuilt-invoice"  # Use the appropriate model for trade finance docs
file_path = r"C:\Users\SARTHAK\OneDrive\Pictures\Screenshots\Screenshot (62).png"

# Initialize Azure Document Intelligence Client
doc_client = DocumentIntelligenceClient(AZURE_ENDPOINT, AzureKeyCredential(AZURE_KEY))

# Function to extract key-value pairs using Azure Document Intelligence
def extract_key_values(file_path):
    with open(file_path, "rb") as file_data:
        poller = doc_client.begin_analyze_document(MODEL_ID, file_data)
        result = poller.result()

    extracted_data = {}
    for field, content in result.documents[0].fields.items():
        # Ensure content has a proper value and extract it
        if hasattr(content, "value"):
            extracted_data[field] = content.value
        else:
            extracted_data[field] = "Not Found"

    return extracted_data

# Function to validate, identify missing data, and provide feedback using DeepSeek
def validate_and_feedback(extracted_data):
    prompt = f"""
    You are an expert in trade finance compliance. A user has uploaded a trade finance document. 
    The extracted data is as follows:

    {json.dumps(extracted_data, indent=2)}

    Your task:
    1. Verify the extracted data against prescribed government guidelines.
    2. Identify any missing key-value pairs and specify what is missing.
    3. Provide feedback on whether the document is valid or needs corrections.
    4. If corrections are needed, suggest specific changes.

    Return a structured and detailed response.
    """
    
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

# Main workflow (Autonomous Execution)
def process_document(file_path):
    print("Extracting key-value pairs using Azure Document Intelligence...")
    extracted_data = extract_key_values(file_path)

    print("Validating data, identifying missing fields, and generating feedback using DeepSeek...")
    feedback = validate_and_feedback(extracted_data)

    print("\n==== Final Feedback Report ====\n")
    print(feedback)

# Example usage (replace with actual file path)
process_document(file_path)

