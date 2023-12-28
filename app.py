import time
import os
import shelve
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request
from constants import SPINNY_INSTRUCTION

load_dotenv()

app = Flask(__name__)

open_ai_key = os.environ.get('OPENAI_API_KEY')
assistant_id = os.environ.get('ASSISTANT_ID')
file_id = os.environ.get('FILE_ID')

client = OpenAI(api_key=open_ai_key)


def upload_file(path):
    """
    Upload a file with an "assistants" purpose.

    Args:
        path (str): The path to the file to be uploaded.

    Returns:
        dict: The file information returned by OpenAI API.
    """
    return client.files.create(file=open(path, "rb"), purpose="assistants")


def create_assistant(assistant_name, my_instruction, uploaded_file, model="gpt-4-1106-preview"):
    """
    Create an OpenAI assistant.

    Args:
        assistant_name (str): The name of the assistant.
        my_instruction (str): Instructions for the assistant.
        uploaded_file (dict): The file information returned by OpenAI API.
        model (str): The language model to use (default is "gpt-4-1106-preview").

    Returns:
        dict: The created assistant information returned by OpenAI API.
    """
    return client.beta.assistants.create(
        name=assistant_name,
        instructions=my_instruction,
        model=model,
        tools=[{"type": "retrieval"}],
        file_ids=[uploaded_file.id]
    )


def check_or_create_thread(wa_id, name, file_id):
    """
    Check if a thread exists for a given user ID; if not, create a new thread.

    Args:
        wa_id (str): The user ID.
        name (str): The user's name.
        file_id (str): The file ID to be associated with the thread.

    Returns:
        str: The thread ID.
    """
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        thread_id = threads_shelf.get(wa_id, None)
        if thread_id is None:
            thread = client.beta.threads.create(messages=[
                {"role": "user", "content": f"Hey, I'm a new user to spinny. My name is {name}. Please greet me cheerfully.",
                    "file_ids": [file_id]}
            ])
            threads_shelf[wa_id] = thread.id
            return thread.id
        else:
            return thread_id


@app.route('/chat',  methods=["POST"])
def generate_response():
    """
    Generate a response for a chat message from the user.

    Returns:
        str: The generated response from the assistant.
    """
    data = request.get_json()
    message_body, wa_id, name = data['message'], data['user_id'], data['name']

    thread_id = check_or_create_thread(wa_id, name, file_id)

    thread = client.beta.threads.retrieve(thread_id)
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
        file_ids=[file_id]
    )

    new_message = run_assistant(thread)
    print(f"To {name}, Thread {thread_id}:", new_message)
    return new_message


def run_assistant(thread):
    """
    Run the OpenAI assistant for a given thread.

    Args:
        thread (dict): The thread information.

    Returns:
        str: The generated message from the assistant.
    """
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        instructions=SPINNY_INSTRUCTION
    )

    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


# Use the code below if a new assistant is created or API key is changed
inst = SPINNY_INSTRUCTION
assistant_name = "Spinny the friendly AI bot"
uploaded_file = upload_file('teach_spinny.pdf')
my_assistant = create_assistant(assistant_name, inst, uploaded_file)

if __name__ == '__main__':
    app.run(debug=True)
