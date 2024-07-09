from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError, APIStatusError
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

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

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user_input = request.args.get('user_input') if request.method == 'GET' else request.form['user_input']
    
    logger.info("Starting chat session...")
    
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
        return jsonify(content=message.content)
    except APIConnectionError as e:
        logger.error("The server could not be reached", exc_info=True)
        logger.error(f"Exception details: {e.__cause__}")
        return jsonify(error="The server could not be reached"), 503
    except RateLimitError as e:
        logger.error("A 429 status code was received; we should back off a bit.", exc_info=True)
        return jsonify(error="Too many requests, please try again later"), 429
    except APIStatusError as e:
        logger.error(f"Another non-200-range status code was received: {e.status_code}", exc_info=True)
        logger.error(f"Response details: {e.response}")
        return jsonify(error=f"API error: {e.status_code}"), e.status_code
    except APIError as e:
        logger.error(f"A general API error occurred: {str(e)}", exc_info=True)
        return jsonify(error="An unexpected error occurred"), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')