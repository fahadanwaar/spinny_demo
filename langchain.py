
import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory

load_dotenv()

open_ai_key = os.environ.get('OPENAI_API_KEY')

llm = OpenAI(api_key=open_ai_key)

memory = ConversationBufferMemory()


conversation = ConversationChain(
    llm=llm,
    memory=memory
)

conversation.predict(input="Hello, my name is Ahmad")
conversation.predict(input="What is my name?")

# More efficient memory i-e storing context in summary:

schedule = "There is a meeting at 8am with your product team. \
     You will need your powerpoint presentation prepared. \
     9am-12pm have time to work on your LangChain \
     project which will go quickly because Langchain is such a powerful tool. \
     At Noon, lunch at the italian resturant with a customer who is driving \
     from over an hour away to meet you to understand the latest in AI. \
     Be sure to bring your laptop to show the latest LLM demo."

memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)

# Pre storing some context (not mandatory)
memory.save_context({"input": "Hello"}, {"output": "What's up"})
memory.save_context({"input": "Not much, just hanging"}, {"output": "Cool"})
memory.save_context({"input": "What is on the schedule today?"}, {
                    "output": f"{schedule}"})

conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

conversation.predict(input="What would be a good time for coffee break?")
