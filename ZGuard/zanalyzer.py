import ollama

# Function to call the Llama API with a prompt
def send_to_z_analyze(patterndb,TransactionHistory,currenttrsanaction):
    print("Request received")
    
    # Construct the prompt
    prompt = f"""
    PatternDB : {patterndb} ;;;;;
    User Previous Transaction History : {TransactionHistory} ;;;;
    currenttrsanaction : {currenttrsanaction};;;
    
    JUST RETURN THE JSON - NOT ANYTHING ELSE - JUST JSON.s
    Be fast fast fast and short.
    payment are in INR.
    modify the json summary with Current Transaction names (not from Pattern DB) , tell like a story , """    
    # Call the Ollama model
    response = ollama.chat(
        model="zGuard",
        messages=[
            {"role": "user", "content": prompt},  # Pass the prompt
        ],
    )
    
    # Return the response from the model
    return response.get("message", {}).get("content", "No message found")

print(send_to_z_analyze("","",""))