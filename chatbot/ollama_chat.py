import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

def generate_chat_stream(messages_history, new_message):
    """
    Calls local Ollama API to stream a generated response chunk-by-chunk.
    messages_history is a list of dicts: [{'role': 'user'/'ai', 'content': '...'}, ...]
    """
    
    # Construct a prompt with context
    prompt = "You are DermAI, a helpful and knowledgeable AI assistant. You can answer any general questions the user asks. However, you also specialize in dermatology, skin cancer, and general health. If providing medical advice, always advise consulting a real doctor."
    prompt += "\n\nChat History:\n"
    
    # Only keep the last 5 messages for context to save tokens and time
    recent_history = messages_history[-5:]
    
    for msg in recent_history:
        role = "User" if msg['role'] == 'user' else "DermAI"
        prompt += f"{role}: {msg['content']}\n"
        
    prompt += f"User: {new_message}\nDermAI:"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=120)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    yield data.get("response", "")
        else:
            print(f"Ollama API Error: {response.status_code} - {response.text}")
            yield "I am currently unable to reach my healthcare knowledge base. Ensure Ollama is running locally."
    except requests.exceptions.RequestException as e:
        print(f"Ollama Connection Error: {e}")
        yield "Failed to connect to DermAI Chat. Please make sure Ollama is running (`ollama run qwen2.5:3b`)."

if __name__ == "__main__":
    print(generate_chat_response([], "What are symptoms of skin cancer?"))
