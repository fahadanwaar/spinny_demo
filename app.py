import time
import shelve
from flask import Flask, request
from openai import OpenAI
from constants import SPINNY_INSTRUCTION

app = Flask(__name__)
# FILE_ID = 'file-gdPgVsLFaAN2yDQyAeKWw7b5'
# FILE_ID = 'file-DSZE2TK7wwggRjkH7Dn3o7li'  # File provided to assistant #old
# ASSISTANT_ID = 'asst_MkjOHJCh90zr9slPv7RxQkdI' #old

FILE_ID = 'file-1fLKeUnCjFyu7ATXcmxxnCmw'  # new
ASSISTANT_ID = 'asst_gmrlgUwGJktMrG6lXtFIhfaK'  # new

# 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


@app.route('/')
def hello():
    return 'Hello, World!'


client = OpenAI(api_key='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')
# Fahad bhai's account
# client = OpenAI(api_key='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')


def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file


def create_assistant(assistant_name,
                     my_instruction,
                     uploaded_file,
                     model="gpt-4-1106-preview"):

    my_assistant = client.beta.assistants.create(
        name=assistant_name,
        instructions=my_instruction,
        model=model,
        tools=[{"type": "retrieval"}],
        file_ids=[uploaded_file.id]
    )

    return my_assistant


def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


@app.route('/chat',  methods=["POST"])
def generate_response():
    # Check if there is already a thread_id for the wa_id
    data = request.get_json()
    message_body = data['message']

    # We will get these two from our DB.
    wa_id = data['user_id']
    name = data['name']

    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create(messages=[
            {
                "role": "user",
                "content": f"Hey, I'm a new user to spinny. My name is {name}. Please greet me cheerfully.",
                "file_ids": [FILE_ID]
            }
        ])
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
        file_ids=[FILE_ID]  # we can override the assistant file here too
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {name}, Thread {thread_id}:", new_message)
    return new_message


def run_assistant(thread):
    # Retrieve the Assistant

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        instructions=SPINNY_INSTRUCTION
    )

    # Wait for completion
    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


inst = SPINNY_INSTRUCTION
assistant_name = "Spinny the friendly AI bot"
uploaded_file = upload_file('teach_spinny.pdf')
# FILE_ID = uploaded_file.id

my_assistant = create_assistant(assistant_name, inst, uploaded_file)


if __name__ == '__main__':
    app.run(debug=True)
