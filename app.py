from flask import Flask, request, jsonify
import subprocess
import openai
import os
from flask_cors import CORS  
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
CORS(app)

CUSTOM_INSTRUCTIONS="""You are a highly skilled Sales Development Representative (SDR) for a fintech company. Your role is to engage potential customers, introduce financial products, and capture key customer details while maintaining a natural, human-like conversation. Begin each call with a warm greeting, addressing the customer by name if available, or politely asking for their name. Briefly introduce yourself and the fintech company, establishing trust by mentioning relevant partnerships or exclusive benefits. Gather essential customer details such as their name, email, location, employment status, and financial interests. Based on their profile, pitch one or two relevant financial products—such as a credit card with cashback benefits, a personal loan with competitive rates, or a savings account with high interest. If the customer hesitates, acknowledge their concerns and personalize the pitch by highlighting relevant benefits, offering incentives like no processing fees or exclusive discounts if available. Adapt your tone and language based on the customer's preference, seamlessly switching between English and Hindi when needed. If the customer shows interest, schedule a follow-up call, send details via email, or assist with the application process. Ensure that key customer details, interests, and preferences are logged for future follow-ups. Conclude each conversation with a polite thank-you and an open invitation for the customer to reach out for further details. Your goal is to make every interaction engaging, persuasive, and productive while capturing valuable insights about the customer’s needs."""

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")  # Example: "mongodb://localhost:27017"
DB_NAME = "banking_db"
COLLECTION_NAME = "customer_conversations"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPEN_API_KEY")

# Run main.py in the background
subprocess.Popen(["python", "main.py", "start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.route("/", methods=["GET"])
def run_main():
    return jsonify("hello"), 200

@app.route("/savedata", methods=["POST"])
def save_data():
    try:
        print("Your API Key:", OPENAI_API_KEY)

        data = request.json
        conversations = data.get("conversations", [])

        if not conversations or not isinstance(conversations, list):
            return jsonify({"error": "Invalid input. Expected an array of text inputs."}), 400

        prompt = f"""
        Extract relevant details about the person from the following banking conversation:
        {conversations}

        Output the information in JSON format with keys: 'name', 'interests', and 'details'.
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI assistant extracting customer details."},
                {"role": "user", "content": prompt}
            ]
        )

        extracted_data = response.choices[0].message.content

        # Store the extracted data in MongoDB
        record = {
            "conversations": conversations,
            "extracted_info": extracted_data
        }
        inserted_id = collection.insert_one(record).inserted_id

        return jsonify({
            "message": "Data saved successfully",
            "record": extracted_data,
            "mongo_id": str(inserted_id)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
