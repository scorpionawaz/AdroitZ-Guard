import ollama

# Function to call the Llama API with a prompt
def send_to_z_analyze(currenttrsanaction, patterndb,TransactionHistory):
    print("Request received to Llama API : Now generating Answer")
    
    # Construct the prompt
    prompt = f"""
    PatternDB : {patterndb} ;;;;;
    User Previous Transaction History : {TransactionHistory} ;;;;
    currenttrsanaction : {currenttrsanaction}
    """    
    # Call the Ollama model
    response = ollama.chat(
        model="zGuard",
        messages=[
            {"role": "user", "content": prompt},  # Pass the prompt
        ],
    )
    
    # Return the response from the model
    return response.get("message", {}).get("content", "No message found")

