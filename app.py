from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError, APIStatusError
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)


# Define the log directory and file
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
log_file = os.path.join(log_dir, 'app.log')


# Ensure the log directory exists
os.makedirs(log_dir, exist_ok=True)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Initialize Anthropic client using the API key from .env
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('user_input')
    
    logger.info(f"Received chat request with input: {user_input}")
    
    try:
        message = anthropic_client.messages.create(
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            model="claude-3-sonnet-20240229",
        )
        logger.info("Chat response received")
        
        # Extract the text content from the message
        content = message.content[0].text if message.content else ""
        
        return jsonify(content=content)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify(error="An unexpected error occurred"), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
