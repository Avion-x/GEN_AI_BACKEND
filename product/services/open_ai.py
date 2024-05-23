import os
import time
from typing import Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv,find_dotenv
from user.settings import BASE_DIR

# Set your OpenAI GPT-3 API key
load_dotenv(find_dotenv())
OPENAI_GPT_API_KEY = os.environ.get('OPENAI_GPT_API_KEY')
client = OpenAI(api_key=OPENAI_GPT_API_KEY)


class CustomOpenAI():
    def __init__(self, role="user", append_prompt=None, *args: Any, **kwds: Any) -> Any:
        self.role = role
        self.append_prompt = append_prompt or """
        . Each testcase and testscript should be encapsulated within its own separate JSON object, and it is an object under the "testname" key. All these JSON objects should be assembled within a Python list, resulting in [{ "testname":"", "testcase":{}, "testscript":{}}] Each test case should include a testname, objective, steps (list of expected results), relevant test data. Make sure each test script JSON object includes the following fields: 'testname', 'objective', 'file_name', 'init_scripts'. The 'init_scripts' field should contain pip install commands for all required packages, 'script' (given in triple quotes), 'run_command' (a command to execute the python file) and 'expected_result'. The Python list with the JSON objects should not include any unrelated context or information. Find the starting delimiter as ###STARTLIST### and the ending delimiter as ###ENDLIST###
        """

        self.model_registry = {
           "gpt_35": {
                "model": "gpt-3.5-turbo"
            },
            "gpt_40": {
                "model": "gpt-4.0"
            }
        }

    def get_ai_model_id(self, user_input=None):
        try:
            model = self.model_registry.get(user_input)
            if model is None:
                raise Exception(f"Please pass valid model. Available models in gpt are {list(self.model_registry.keys())}")
            return model['model']
        except Exception as e:
            raise e
        
    
    def build_prompt(self, **kwargs):
        try:
            prompt = kwargs.get('prompt', "") + self.append_prompt 
            context = kwargs.get('context', None)
            if context:
                prompt = prompt.replace("${a.content}", context)
            return prompt
        except Exception as e:
            raise e

    def send_prompt(self, prompt, **kwargs):
        try:
            response = client.chat.completions.create(
                messages=[
                {
                    "role": self.role,
                    "content": prompt + self.append_prompt or self.build_prompt(**kwargs)
                }
            ],
            # model= kwargs.get('modelId', "text-embedding-ada-002")  # "gpt-3.5-turbo-1106",
            model = self.get_ai_model_id(kwargs.get('modelId'))
            )
            output_text = "\n\n" + response.choices[0].message.content
            return output_text
        except Exception as e:
            raise e



