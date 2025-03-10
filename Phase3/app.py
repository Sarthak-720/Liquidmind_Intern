from flask import Flask, request, jsonify
import pandas as pd
import os
import json
import logging
from cryptography.fernet import Fernet
from langchain.schema.messages import HumanMessage
import google.generativeai as genai
import psycopg2
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv
import pathlib

try:
    from importlib.metadata import metadata
except ImportError:
    from importlib_metadata import metadata
 
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Move config to environment variables or config file in production
KEY_FILE = "secret.key"
KEY_ENV_VAR = "ENCRYPTION_KEY"
DB_CONFIG = {
    "host": "liquidmind.postgres.database.azure.com",
    "port": 5432,
    "database": "liquidminddb",
    "user": "lm_admin",
    "password": "liquidmind@123",
}

# Add these environment checks near the top of the file
GOOGLE_CREDENTIALS_PATH = os.path.join(pathlib.Path(__file__).parent, "Credentials.json")
GEMINI_API_KEY = 'AIzaSyCdCy_pq1b4m3OT2OfNWQr4XJ46LD4xVqM'

if not GOOGLE_CREDENTIALS_PATH:
    raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable is required")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Key management
def generate_key():
    try:
        # First check if key exists in environment variable
        env_key = os.getenv(KEY_ENV_VAR)
        if env_key:
            logger.info("Using encryption key from environment variable")
            return env_key.encode()

        # Then check for key file in secure location
        key_path = Path(KEY_FILE)
        if key_path.exists():
            with open(key_path, "rb") as key_file:
                logger.info("Using existing encryption key from file")
                return key_file.read()

        # If no key exists, generate one and save it
        key = Fernet.generate_key()
        
        # Save to file
        key_path.parent.mkdir(parents=True, exist_ok=True)
        with open(key_path, "wb") as key_file:
            key_file.write(key)
            
        # Also set it as environment variable
        os.environ[KEY_ENV_VAR] = key.decode()
        
        logger.info("New encryption key generated and saved")
        return key

    except Exception as e:
        logger.error(f"Error in key management: {str(e)}")
        raise
def load_key():
    try:
        return generate_key()
    except Exception as e:
        logger.error(f"Error loading key: {str(e)}")
        raise

class ChatGemini:
    def __init__(self, model_name: str, credentials_path: str, generation_config: dict):
        try:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=model_name, 
                generation_config=generation_config
            )
            logger.info(f"ChatGemini initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing ChatGemini: {str(e)}")
            raise

    def invoke(self, input_data) -> dict:
        try:
            logger.debug("Processing input data")
            payload = json.loads(input_data[0].content)
            encrypted_csv = payload.get("encrypted_csv")
            password = payload.get("password")
            user_task = payload.get("topic")

            if not all([encrypted_csv, password, user_task]):
                logger.error("Missing required data in payload")
                raise ValueError("Missing required data")

            cipher = Fernet(password.encode())
            decrypted_csv_data = cipher.decrypt(encrypted_csv.encode())
            logger.debug("CSV data decrypted successfully")

            csv_data_path = "temp_decrypted.csv"
            with open(csv_data_path, "wb") as file:
                file.write(decrypted_csv_data)

            data = pd.read_csv(csv_data_path)
            os.remove(csv_data_path)
            logger.debug("CSV data processed and temp file removed")

            csv_data_str = data.to_string(index=False)
            prompt = f''' The currency is INR.
            The response should not exceed 70 words and it should be in bullet points and no special formatting 
            Task: {user_task}\n\nRelevant CSV Data: \n{csv_data_str}
            The response should be such a way that it should be understood by a common man.
            Don't respond to random questions answer only specific questions related to the CSV Data
            '''

            logger.debug("Sending request to Gemini model")
            response = self.model.start_chat(history=[]).send_message(prompt)
            encrypted_response = cipher.encrypt(response.text.encode())
            logger.debug("Response received and encrypted")

            return {
                "response": encrypted_response.decode(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error in ChatGemini invoke: {str(e)}")
            return {"response": str(e), "status": "failed"}

# Initialize Gemini LLM
try:
    gemini_model = ChatGemini(
        model_name="gemini-1.5-flash",
        credentials_path=GOOGLE_CREDENTIALS_PATH,
        generation_config={
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
    )
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {str(e)}")
    raise

# Initialize encryption
generate_key()
key = load_key()
cipher = Fernet(key)

def encrypt_csv(file_path):
    try:
        with open(file_path, "rb") as file:
            encrypted_data = cipher.encrypt(file.read())
            logger.debug(f"CSV file encrypted: {file_path}")
            return encrypted_data
    except Exception as e:
        logger.error(f"Error encrypting CSV file: {str(e)}")
        raise

def format_invoice_message(response):
    raw_response_text = response
    cleaned_response_lines = []
    for line in raw_response_text.split("\n"):
        line = line.strip()
        if line.startswith("*"):
            # Convert bullet points into proper list items
            cleaned_response_lines.append(f"• {line[1:].strip()}")
        elif line:
            cleaned_response_lines.append(line)
    cleaned_response_text = "\n".join(cleaned_response_lines)
    return cleaned_response_text

@app.route('/analyze_invoice/', methods=['GET','POST'])
def analyze_invoice():
    conn = None
    cursor = None
    try:
        logger.info("New invoice analysis request received")
        
        if request.method == 'GET':
            msme_id = request.args.get('msme_id')

            topic = request.args.get('topic')
            logger.debug(f"GET request - MSME ID: {msme_id}, Topic: {topic}")
        else:
            if not request.is_json:
                logger.error("Invalid content type received")
                # return jsonify({"error": "Content-Type must be application/json"}), 415
                return ("Content-Type must be application/json")
            data = request.json
            msme_id = data.get('msme_id')
            topic = data.get('topic')
            logger.debug(f"POST request - MSME ID: {msme_id}, Topic: {topic}")
        
        if not topic or not msme_id:
            logger.error("Missing required parameters")
            # return jsonify({"error": "Both MSME ID and topic are required"}), 400
            return ("Both MSME ID and topic are required")

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.debug("Database connection established")

        # Check MSME existence and premium days
        check_msme_query = """
            SELECT EXISTS(SELECT 1 FROM msme WHERE msme_id = %s),
                   (SELECT premium_days FROM msme WHERE msme_id = %s)
        """
        cursor.execute(check_msme_query, (msme_id, msme_id))
        msme_exists, premium_days = cursor.fetchone()

        if not msme_exists:
            # return jsonify({
            #     "status": "error",
            #     "response": f"MSME ID {msme_id} not found in database"
            # }), 404
           return (f"MSME ID {msme_id} not found in database")
            
        if premium_days <= 0:
            # return jsonify({
            #     "status": "error",
            #     "response": "Your premium has expired. Please renew to continue using the service."
            # }), 403
            return ("Your premium has expired. Please renew to continue using the service.")

        # Check for invoices
        check_invoices_query = "SELECT COUNT(*) FROM invoice WHERE msme_id = %s"
        cursor.execute(check_invoices_query, (msme_id,))
        if cursor.fetchone()[0] == 0:
            # return jsonify({
            #     "status": "success",
            #     "response": "No invoices found for this MSME. Please upload some invoices to analyze."
            # })
            return ("No invoices found for this MSME. Please upload some invoices to analyze.")

        # Get invoice data
        cursor.execute("SELECT * FROM invoice WHERE msme_id = %s", (msme_id,))
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        
        # Save and encrypt CSV
        output_file = f"temp_invoice_{msme_id}.csv"
        df.to_csv(output_file, index=False)
        encrypted_csv = encrypt_csv(output_file)
        os.remove(output_file)

        # Process with Gemini
        payload = {
            "encrypted_csv": encrypted_csv.decode(),
            "password": key.decode(),
            "topic": topic.strip(),
        }
        result = gemini_model.invoke([HumanMessage(content=json.dumps(payload))])

        # if result["status"] == "failed":
        #     return jsonify({"error": result["response"]}), 500

        if result["status"] == "failed":
            return (result["response"])

        # return jsonify({
        #     "status": "success",
        #     "response": cipher.decrypt(result["response"].encode()).decode(),
        #     "premium_days": premium_days
        # })
        response_chat = cipher.decrypt(result["response"].encode()).decode() 
        formatted_msg = format_invoice_message(response_chat)
        return jsonify(formatted_msg)

    except Exception as e:
        logger.error(f"Error in analyze_invoice: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("Database connection closed")

if __name__ == "__main__":
    app.run()
