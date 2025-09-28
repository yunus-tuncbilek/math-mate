# suppress warnings
import warnings
warnings.filterwarnings("ignore")

from together import Together

# Get Client
your_api_key = "396a7aedf1b74f31a921f1bcc550f4a03768b4d7fc3596acb3bf90600051e425"
client = Together(api_key=your_api_key)

def prompt_llm(prompt):
    # This function allows us to prompt an LLM via the Together API

    # model
    model = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"

    # # Calculate the number of tokens
    # tokens = len(prompt.split())

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

print("LLM Ready!")

'''respond function'''
def get_ai_response(user_message, chat_history, homework):
    prompt = f"""
    You are a helpful AI Chatbot that loves to help students with their homework.

    Instructions:
    - Make your answers at most 30 words
    - Only give the response to the message
    - Give the students hints or suggestions
    - Do not solve the question for them
    - Please use the knowledge base to answer the question if relevant

    Knowledge base:
    
    Error database:

    Respond to the user's message below:
    {user_message}

    Here is your chat history with the user:
    {chat_history}

    Here is the user's Homework:
    {homework}
    """

    return prompt_llm(prompt)