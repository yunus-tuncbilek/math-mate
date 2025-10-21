print("Loading LLM...")

# suppress warnings
import warnings
warnings.filterwarnings("ignore")

from together import Together
import os
from rag import rag_utils

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Get Client
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY environment variable not set")
client = Together(api_key=TOGETHER_API_KEY)

def prompt_llm(prompt):
    # This function allows us to prompt an LLM via the Together API

    # model
    model = "openai/gpt-oss-20b"

    # print(f"Using {model}")

    # # Calculate the number of tokens
    # tokens = len(prompt.split())

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

print("LLM Ready!")

'''respond function for ai response to HW questions'''
def get_ai_response(user_message, chat_history="", homework="", lecture=""):
    prompt = f"""
    You are a helpful AI Chatbot that loves to help students with their homework.

    Instructions:
    - Make your answers at most 30 words
    - Only give the response to the user's message
    - Give the students hints or suggestions
    - Do not provide direct answers to homework questions
    - If you don't know the answer, just say "I don't know"
    - Do not make up answers
    - Check with the student to see if they need further assistance or clarification
    - Be friendly and encouraging
    - If your last response included a question, wait for the student's reply before responding again
    - Please use the knowledge base to answer the question if relevant
    - Use LaTeX syntax for mathematical expressions.

    Knowledge base:
    - Homework assignments:
    {homework}

    - Lecture notes:
    {lecture}

    Error database:
    
    Here is your chat history with the user:
    {chat_history}
    
    Respond to the user's message below:
    {user_message}
    """

    return prompt_llm(prompt)

def closest_chunk_from_rag(question):
    data_file = "rag/data/lectures.txt"
    data_txt = rag_utils.load_data(data_file)

    chunks = rag_utils.get_chunks(data_txt)
    embeddings = rag_utils.get_embeddings(chunks)

    # RETRIEVE CLOSEST CHUNK
    # -----------------------
    closest_chunk, similarity, chunk_idx, query_embedding, all_similarities = (
        rag_utils.retrieve_closest_chunk(question, chunks, embeddings)
    )

    return closest_chunk