import json
import ollama
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

AZURE_ENDPOINT = "https://liquidmindinvoice.cognitiveservices.azure.com/"
AZURE_KEY = "de011e6175a14593bfdff3bb210c65b2"
MODEL_ID = "prebuilt-invoice"  # Use the appropriate model for trade finance docs
file_path = r"C:\Users\SARTHAK\OneDrive\Pictures\Screenshots\Screenshot (62).png"

# Initialize Azure Document Intelligence Client
doc_client = DocumentIntelligenceClient(
    AZURE_ENDPOINT, AzureKeyCredential(AZURE_KEY))


def extract_key_values(file_path):
    try:
        with open(file_path, "rb") as document:
            poller = doc_client.begin_analyze_document(
                MODEL_ID, document_content=document.read()
            )
        result = poller.result()

        # Convert the result to a dictionary
        extracted_data = {}
        for kv_pair in result.key_value_pairs:
            if kv_pair.key and kv_pair.value:
                extracted_data[kv_pair.key.content] = kv_pair.value.content

        return extracted_data
    except Exception as e:
        print(f"Error in document extraction: {str(e)}")
        return {"error": str(e)}


def parse_response(response):
    """Ensure response content is a valid JSON before returning"""
    try:
        response_content = response.get("message", {}).get("content", "").strip()
        return json.loads(response_content)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing response: {str(e)}")
        print(f"Raw response: {response}")
        return None


def document_analyzer_agent(extracted_data):
    prompt = f"""
    You are a Document Analysis Agent specialized in trade finance documents. 
    Analyze the following extracted data and ensure strict JSON formatting:

    {json.dumps(extracted_data, indent=2)}

    Your tasks:
    1. Identify all **missing fields** that should be present in a trade finance document.
    2. Highlight **critical issues** or inconsistencies in the provided data.
    3. Provide a **structured summary** of your findings.

    **Output must be in valid JSON format only** with the following structure:
    ```json
    {{
        "missing_fields": ["field1", "field2", ...],
        "critical_issues": ["issue1", "issue2", ...],
        "analysis_summary": "detailed summary"
    }}
    ```
    Do not include any explanation, only output valid JSON.
    """

    response = ollama.chat(
        model="deepseek-r1:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return parse_response(response) or {
        "missing_fields": [],
        "critical_issues": ["Failed to parse analyzer response"],
        "analysis_summary": "Analysis failed"
    }


def compliance_validator_agent(analyzer_output, extracted_data):
    prompt = f"""
    You are a Compliance Validation Agent specializing in trade finance regulations.
    Validate the document compliance against government trade finance guidelines.

    **Extracted Data:**
    {json.dumps(extracted_data, indent=2)}

    **Previous Analysis:**
    {json.dumps(analyzer_output, indent=2)}

    Your tasks:
    1. Determine if the document is **compliant** or **non-compliant**.
    2. Assess **compliance risk** as **high, medium, or low**.
    3. Identify any **violations** of trade finance regulations.
    4. Provide **recommendations** for achieving compliance.

    **Output must be in valid JSON format only**:
    ```json
    {{
        "compliance_status": "compliant/non-compliant",
        "risk_assessment": "high/medium/low",
        "violations": ["violation1", "violation2", ...],
        "recommendations": ["rec1", "rec2", ...]
    }}
    ```
    Do not include any explanation, only output valid JSON.
    """

    response = ollama.chat(
        model="deepseek-r1:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_response(response) or {
        "compliance_status": "unknown",
        "risk_assessment": "high",
        "violations": ["Failed to parse validator response"],
        "recommendations": ["Manual review required"]
    }


def data_enhancement_agent(validator_output, extracted_data):
    prompt = f"""
    You are a Data Enhancement Agent specializing in trade finance documents. 
    Enhance extracted data and suggest missing values.

    **Extracted Data:**
    {json.dumps(extracted_data, indent=2)}

    **Compliance Analysis:**
    {json.dumps(validator_output, indent=2)}

    Your tasks:
    1. Suggest **possible values** for missing fields using available context.
    2. Assign **confidence scores** (0-1) for each suggested value.
    3. Recommend **verification steps** and **additional data sources**.

    **Output must be in valid JSON format only**:
    ```json
    {{
        "suggested_values": {{"field1": {{"value": "suggested_value", "confidence": 0.9}}}},
        "verification_steps": ["step1", "step2", ...],
        "additional_sources": ["source1", "source2", ...]
    }}
    ```
    Do not include any explanation, only output valid JSON.
    """

    response = ollama.chat(
        model="deepseek-r1:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_response(response) or {
        "suggested_values": {},
        "verification_steps": ["Failed to parse enhancement response"],
        "additional_sources": ["Manual review required"]
    }


def process_document(file_path):
    try:
        print("Extracting key-value pairs using Azure Document Intelligence...")
        extracted_data = extract_key_values(file_path)

        print("\n1. Running Document Analyzer Agent...")
        analyzer_results = document_analyzer_agent(extracted_data)

        print("\n2. Running Compliance Validator Agent...")
        validator_results = compliance_validator_agent(analyzer_results, extracted_data)

        print("\n3. Running Data Enhancement Agent...")
        enhancement_results = data_enhancement_agent(validator_results, extracted_data)

        print("\n==== Final Analysis Report ====")
        print("\nDocument Analysis:")
        print(json.dumps(analyzer_results, indent=2))
        print("\nCompliance Validation:")
        print(json.dumps(validator_results, indent=2))
        print("\nData Enhancement Suggestions:")
        print(json.dumps(enhancement_results, indent=2))

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    process_document(file_path)
