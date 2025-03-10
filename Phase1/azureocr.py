from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


AZURE_ENDPOINT = "https://liquidmindinvoice.cognitiveservices.azure.com/"
AZURE_KEY = "de011e6175a14593bfdff3bb210c65b2"

client = DocumentAnalysisClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY))

def azure_ocr(uploaded_file):
    try:
        # Validate file format
        if uploaded_file.type not in ["application/pdf", "image/jpeg", "image/png", "image/tiff"]:
            raise ValueError("Unsupported file format. Upload a PDF, JPEG, PNG, or TIFF.")
        
        # Read file as binary data
        file_data = uploaded_file.read()
        if not file_data:
            raise ValueError("File data is empty or corrupted.")

        # Analyze document using Azure OCR
        poller = client.begin_analyze_document("prebuilt-document", file_data)
        result = poller.result()

        # Extract text from the result
        extracted_text = ""
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + "\n"
        return extracted_text

    except Exception as e:
        raise ValueError(f"Azure OCR failed: {e}")

