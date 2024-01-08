import openai

# Set your OpenAI GPT-3 API key
openai.api_key = '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'

def send_prompt(prompt):
    response = openai.Completion.create(
        model="text-davinci-003",  # Replace with the latest version if available
        prompt=prompt,
        max_tokens=3800 # Adjust as needed
    )
    
    # return the response text
    return response.choices[0].text.strip()
