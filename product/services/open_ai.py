import os
from openai import OpenAI

from user.settings import BASE_DIR

# Set your OpenAI GPT-3 API key
api_key = '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'
# openai.api_key = api_key

# def send_prompt(prompt):
#     response = openai.Completion.create(
#         model="text-davinci-003",  # Replace with the latest version if available
#         prompt=prompt,
#         max_tokens=3800 # Adjust as needed
#     )
    
#     # return the response text
#     return response.choices[0].text.strip()


# def send_prompt(prompt, output_file="output.md"):
#     response = openai.Completion.create(
#         model="gpt-3.5-turbo",  # Replace with the latest version if available
#         prompt=prompt,
#         max_tokens=3800  # Adjust as needed
#     )

#     # Extract text from the response and add Markdown formatting
#     output_text = f"# GEN AI Output\n\n```\n{response.choices[0].text.strip()}\n```\n"

#     # Write the response to a Markdown file
#     with open(output_file, "w", encoding="utf-8") as file:
#         file.write(output_text)

#     return output_text

client = OpenAI(api_key=api_key)

def send_prompt(prompt, output_file="output.md"):
    response = client.chat.completions.create(
        messages=[
        {
            "role": "user",
            "content": prompt + ". Provide data with markdown compatable for headers, sub headers, paragraphs, and code snippets that resemble the output format of ChatGPT."
        }
    ],
    model="gpt-3.5-turbo-1106",
    )
    output_text = "\n\n" + response.choices[0].message.content
    print(output_text)
    output_file = os.path.join(BASE_DIR, "data", output_file)
    with open(output_file, "a", encoding="utf-8") as file:
        file.write(output_text)

    return output_text
