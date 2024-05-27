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


class ChatGPTAssistantManager:
    def __init__(self, *args, **kwargs):
        self.thread = None
        self.assistant = None

        # self.default_prompt_suffix = """
        # . Each testcase and testscript should be encapsulated within its own separate JSON object, and it is an object under the "testname" key. All these JSON objects should be assembled within a Python list, resulting in [{ "testname":"", "testcase":{}, "testscript":{}}] Each test case should include a testname, objective, steps (list of expected results), relevant test data. Make sure each test script JSON object includes the following fields: 'testname', 'objective', 'file_name', 'init_scripts'. The 'init_scripts' field should contain pip install commands for all required packages, 'script' (given in triple quotes), 'run_command' (a command to execute the python file) and 'expected_result'. The Python list with the JSON objects should not include any unrelated context or information. Find the starting delimiter as ###STARTLIST### and the ending delimiter as ###ENDLIST###
        # """

        self.default_prompt_suffix = """
            . Each test case and test script should be encapsulated within its own separate JSON object, and it should be an object under the "testname" key. All these JSON objects should be assembled within a Python list, resulting in a list like this: [{ "testname": "", "testcase": {}, "testscript": {} }]. Each test case should include a testname, objective, steps (list of expected results), and relevant test data. Make sure each test script JSON object includes the following fields: 'testname', 'objective', 'file_name', 'init_scripts'. The 'init_scripts' field should contain pip install commands for all required packages, 'script' (given in triple quotes), 'run_command' (a command to execute the python file), and 'expected_result'. The Python list with the JSON objects should not include any unrelated context or information. Find the starting delimiter as ###STARTLIST### and the ending delimiter as ###ENDLIST### and the list should be compatible to python list i should not get any error while converting into python list object.
        """
        
    def set_default_values(self):
        try:
            assistant_id = self.kwargs.get('assistant_id')
            if not assistant_id:
                message = "Please pass an assistant_id to the ChatGPTAssistantManager"
                raise Exception(message)
            self.assistant = self.get_assistant(assistant_id=assistant_id)
            self.thread = self.get_or_create_thread(self.kwargs.get('thread_id', None))
            self.context = self.kwargs.get("context", None)
            self.prompt = self.kwargs.get("prompt", "")
            if self.context:
                self.prompt = self.prompt.replace("${a.content}", self.context)
            self.prompt += self.default_prompt_suffix
            self.temperature = self.kwargs.get("temperature", 1.0)
            self.top_p = self.kwargs.get("top_p", 0.999)
            self.top_k = self.kwargs.get("top_k", 250)
            self.max_tokens = self.kwargs.get("max_tokens", 2048)
            self.stop_sequence = self.kwargs.get("stop_sequence", ['\\n\\nHuman:'])
        except Exception as e:
            raise Exception("Failed to set default values for CHATGPT:OPENAI")

    def list_assistants(self) -> list:
        assistants = client.beta.assistants.list()
        return assistants

    def get_assistant(self, assistant_id: str) -> dict:
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
        return assistant

    def update_assistant(self, assistant_id: str, name: Optional[str] = None, description: Optional[str] = None) -> dict:
        assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            name=name,
            description=description
        )
        return assistant

    def delete_assistant(self, assistant_id: str) -> None:
        client.beta.assistants.delete(assistant_id=assistant_id)
    
    def get_or_create_thread(self, thread_id:None):
        try:
            # thread_id = self.kwargs.get('thread_id',None)
            if thread_id:
                self.thread = client.beta.threads.retrieve(thread_id=thread_id)
            if not self.thread: 
                self.thread = client.beta.threads.create()
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

    def submit_message(self,file_ids: Optional[List[str]] = None) -> dict:
        message_payload = {
            "thread_id": self.thread.id,
            "role": "user",
            "content": self.prompt,
            # "file_ids": file_ids or []
        }
        message = client.beta.threads.messages.create(**message_payload)

        run_payload = {
            "thread_id": self.thread.id,
            "assistant_id": self.assistant.id,
        }
        run = client.beta.threads.runs.create(**run_payload)
        return message, run

    def run_thread(self) -> dict:
        message, run = self.submit_message()
        while run.status == "queued" or run.status == "in_progress":
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
        return message, run
    
    def get_response(self, run_id, get_only_current_run=True) -> list:
        messages = client.beta.threads.messages.list(thread_id=self.thread.id, order="asc")
        response = []
        for ind, m in enumerate(messages):
            if m.role == 'assistant':
                if (get_only_current_run):
                    if m.run_id == run_id:
                        content = m.content[0].text.value
                        response.append(content)
                else:
                    content = m.content[0].text.value
                    response.append(content)
        return response

    def send_prompt(self, **kwargs):
        try:
            self.kwargs = kwargs
            self.set_default_values()
            print(self.prompt)
            print("thread_id: " + self.thread.id)
            message, run = self.run_thread()
            llm_response = self.get_response(run_id=run.id, get_only_current_run=True)
            return "".join(llm_response)
        except Exception as e:
            message = f"Error sending prompt to chatgpt :: ERROR: {e}"
            raise message



