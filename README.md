# OpenAI GPT-3.5/GPT-4 Assisted Chatbot

This Python-based chatbot project is developed with the assistance of OpenAI's GPT-3.5 and GPT-4 AI models. The author, Stanley, has utilized these powerful language models to create a versatile chatbot capable of handling various tasks.

## Design Goals

The primary objective of this chatbot is to provide users with an interactive, intelligent, and efficient tool for communication and assistance. It aims to understand and process user inputs, perform tasks, and generate appropriate responses accordingly.

Some of the key design goals are:

1. Seamless integration of OpenAI's GPT-3.5/GPT-4 models
2. Maintain user conversation history
3. Support various commands for user interaction
4. Ensure scalability and performance

## Architecture

The chatbot application is built using Python and leverages the following technologies and libraries:

1. Flask: A lightweight web framework for handling HTTP requests and routing
2. FoundationDB (FDB): A distributed and highly-scalable database for storing conversation history
3. OpenAI API: A Python library for interacting with OpenAI's GPT-3.5/GPT-4 models

The application follows a modular design with separate functions for handling user inputs, processing commands, interacting with the AI models, and managing conversation history in the database.

## Installation and Execution

Follow these steps to install and run the chatbot application:

1. Clone the repository to your local machine:

git clone <repository_url>

2. Change to the project directory:

cd <project_directory>

3. Create a virtual environment and activate it:

python3 -m venv venv
source venv/bin/activate

4. Install the required dependencies:

pip install -r requirements.txt

5. Set up your OpenAI API key and other environment variables. Create a `.env` file in the project directory with the following content:

OPENAI_API_KEY=<your_openai_api_key>
WEBSITES_PORT=<desired_port_number> (optional, defaults to 5921)

Replace `<your_openai_api_key>` with your actual API key, and `<desired_port_number>` with the port you want the application to run on (if not using the default).

6. Set up FoundationDB (FDB) by following the instructions in their [official documentation](https://apple.github.io/foundationdb/getting-started.html). Make sure the `fdb.cluster` file is placed in the project directory.

7. Start the Flask application by running:

python app.py

8. The chatbot application should now be running on the specified port (or the default port 5921). To interact with the chatbot, send HTTP POST requests to the `/callback` endpoint, including a JSON payload with the user's `user_id` and `user_input`:

{
"user_id": "example_user",
"user_input": "/help"
}

Feel free to customize the chatbot's functionality and commands to suit your specific needs. Enjoy using the GPT-3.5/GPT-4 assisted chatbot!

