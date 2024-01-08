import openai

# Set your OpenAI GPT-3 API key
openai.api_key = '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'

# def send_prompt(prompt):
#     response = openai.Completion.create(
#         model="text-davinci-003",  # Replace with the latest version if available
#         prompt=prompt,
#         max_tokens=3800 # Adjust as needed
#     )
    
#     # return the response text
#     return response.choices[0].text.strip()


def send_prompt(prompt, output_file="output.md"):
    response = openai.Completion.create(
        model="text-davinci-003",  # Replace with the latest version if available
        prompt=prompt,
        max_tokens=3800  # Adjust as needed
    )

    # Extract text from the response and add Markdown formatting
    output_text = f"# GEN AI Output\n\n```\n{response.choices[0].text.strip()}\n```\n"

    # Write the response to a Markdown file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(output_text)

    return output_text
