import os
from typing import Any
from openai import OpenAI

from user.settings import BASE_DIR

# Set your OpenAI GPT-3 API key
api_key = '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'
client = OpenAI(api_key=api_key)


class CustomOpenAI():
    def __init__(self, role="user", append_prompt=None, *args: Any, **kwds: Any) -> Any:
        self.role = role
        self.append_prompt = append_prompt or ". Provide data with markdown compatable for headers, sub headers, paragraphs, and code snippets that resemble the output format of ChatGPT."

    def get_or_set_thread(self):
        try:
            if not self.thread: 
                self.thread = client.beta.threads.create_and_run()
            return self.thread
        except Exception as e:
            raise e
    
    def get_thread_id(self):
        try:
            if self.thread is not None:
                return self.thread.id
            else:
                self.get_or_set_thread().id
        except Exception as e:
            raise e
    
    def delete_thread(self):
        try:
            if self.thread is not None:
                return client.beta.threads.delete(thread_id=self.thread.id)
        except Exception as e:
            raise e
        
    def send_prompt(self, prompt, **kwargs):
        response = client.chat.completions.create(
            messages=[
            {
                "role": self.role,
                "content": prompt + self.append_prompt
            }
        ],
        model=  "text-embedding-ada-002	"  # "gpt-3.5-turbo-1106",
        )
        output_text = "\n\n" + response.choices[0].message.content
        return output_text
