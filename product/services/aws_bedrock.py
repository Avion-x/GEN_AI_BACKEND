import boto3
import json

# class AwsBedrock(object):
#     def __init__(self, model="amazon.titan-text-express-v1"):
#         self.bedrock_runtime = boto3.client('bedrock-runtime',
#             aws_access_key_id='AKIA3MUTZS7BNCEROH24',
#             aws_secret_access_key='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')
#         self.model = model

#     def send_prompt(self, prompts="", maxTokenCount=3900, temparature=0.5, topP=0.1, stopSequences=[], accept='application/json', contentType='application/json'):
#         prompts+=". Provide data with markdown compatable for headers, sub headers, paragraphs, and code snippets in the output."
#         self.body = {
#             "inputText": prompts,
#             "textGenerationConfig" : {
#                 "maxTokenCount": maxTokenCount,
#                 # "temperature": temparature,
#                 # "topP": topP,
#                 # "stopSequences": stopSequences
#             }
#         }

#         print(self.body)
#         response = self.bedrock_runtime.invoke_model(body=json.dumps(self.body), modelId=self.model, accept=accept, contentType=contentType)
#         response_body = response['body'].read().decode()
#         json_response = json.loads(response_body)
#         return json_response.get('results', [{}])[0].get('outputText', "")

default_prompt = ". Provide data with markdown compatable for headers, sub headers, paragraphs, and code snippets in the output."

import boto3
import json


class AwsBedrock():
    """
        This module provides a class called AwsBedrock that interacts with the AWS Bedrock service to send prompts and receive responses from AI models.

        Usage:
            aws = AwsBedrock()
            response = aws.send_prompt(prompt="Generate unit test cases for the router MX480.", modelId='anthropic.claude-v2:1')
            print(response)

        Attributes:
            bedrock_runtime (boto3.client): The AWS Bedrock runtime client.
            default_prompt_suffix (str): The default suffix to be appended to the prompt.
            models_body_registry (dict): A dictionary mapping model IDs to their respective input bodies.
            modelId (str): The ID of the AI model to be used.
            kwargs (dict): Additional keyword arguments passed to the class constructor.

        Methods:
            set_default_values: Sets the default values for the class attributes.
            get_body: Retrieves the input body for the specified model.
            replace_placeholders: Replaces placeholders in the input body with actual values.
            send_prompt: Sends a prompt to the AI model and returns the response.
            format_streeming_response: Formats the streaming response from the AI model.
    """

    def __init__(self, **kwargs):
        """
        Initializes an instance of the AwsBedrock class.

        Args:
            **kwargs: Additional keyword arguments to be passed to the class.

        """
        self.bedrock_runtime = boto3.client('bedrock-runtime',
            aws_access_key_id='AKIA3MUTZS7BNCEROH24',
            aws_secret_access_key='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',
            region_name='us-west-2')

        self.default_prompt_suffix = """
             . Each testcase and testscript should be encapsulated within its own separate JSON object, and it is an object under the "testname" key. All these JSON objects should be assembled within a Python list, resulting in [{ "testname":"", "testcase":{}, "testscript":{}}] Each test case should include a testname, objective, steps (list of expected results), relevant test data. Make sure each test script JSON object includes the following fields: 'testname', 'objective', 'file_name', 'init_scripts'. The 'init_scripts' field should contain pip install commands for all required packages, 'script' (given in triple quotes), 'run_command' (a command to execute the python file) and 'expected_result'. The Python list with the JSON objects should not include any unrelated context or information. Find the starting delimiter as ###STARTLIST### and the ending delimiter as ###ENDLIST###
        """
        
        self.models_body_registry = {
            "anthropic.claude-v2:1" : {
                "input_body": {
                    "prompt": "'\\n\\nHuman:'+self.prompt+'\\n\\nAssistant:'",
                    "max_tokens_to_sample": "self.max_tokens or 2048",
                    "temperature" : "self.temperature or 1",
                    "top_k" : "self.top_k or 250",
                    "top_p" : "self.top_p or 0.999",
                    "stop_sequences" : "self.stop_sequence or ['\\n\\nHuman:']",
                },
                "streeming_response_obj" : "completion"
            },
            "anthropic.claude-v2" : {
                "input_body": {
                    "prompt": "'\\n\\nHuman:'+self.prompt+'\\n\\nAssistant:'",
                    "max_tokens_to_sample": "self.max_tokens or 2048",
                    "temperature" : "self.temperature or 1",
                    "top_k" : "self.top_k or 250",
                    "top_p" : "self.top_p or 0.999",
                    "stop_sequences" : "self.stop_sequence or ['\\n\\nHuman:']",
                },
                "streeming_response_obj" : "completion"
            },
            "amazon.titan-text-express-v1" : {
                "input_body": {
                    "inputText" : "self.prompt",
                    "textGenerationConfig" : {
                        "maxTokenCount": "self.max_tokens or 3900",
                        "temperature": "self.temparature or 0",
                        "topP": "self.top_p or 0.9",
                    }
                },
                "streeming_response_obj" : "outputText"
            }
        }
        
        self.modelId = kwargs.get('modelId', None)
        self.kwargs = kwargs

    def set_default_values(self):
        """
        Sets the default values for the class attributes.

        Raises:
            Exception: If there is an error while setting the default values.

        """
        try:
            self.context = self.kwargs.get("context", None)
            self.prompt = self.kwargs.get("prompt", "") 
            if self.context:
                self.prompt += f" Having context as {self.context}."
            self.prompt += self.default_prompt_suffix
            self.temperature = self.kwargs.get("temperature", None)
            self.top_p = self.kwargs.get("top_p", None)
            self.top_k = self.kwargs.get("top_k", None)
            self.max_tokens = self.kwargs.get("max_tokens", None)
            self.stop_sequence = self.kwargs.get("stop_sequence", [])
        except Exception as e:
            raise Exception("Failed to set default values for Aws Bedrock")
    
    def get_body(self):
        """
        Retrieves the input body for the specified model.

        Returns:
            dict: The input body for the specified model.

        Raises:
            Exception: If there is an error while retrieving the input body.

        """
        try:
            self.model_data = self.models_body_registry.get(self.modelId, None)
            if not self.model_data:
                raise Exception("Please send a valid model {e}")
            input_data = self.model_data.get("input_body", {})
            if not input_data:
                raise Exception("No Input Body for model mentioned, Please contact the admin ")
            self.set_default_values()
            return self.replace_placeholders(data = input_data.copy())
        except Exception as e:
            raise Exception(f"Failed to get body for aws bedrock. Error is {e}")
        
    def replace_placeholders(self, data={}):
        """
        Replaces placeholders in the input body with actual values.

        Args:
            data (dict): The input body data.

        Returns:
            dict: The input body with placeholders replaced.

        """
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.replace_placeholders(value)
            return data
        elif isinstance(data, str):
            return eval(data)
        else:
            return data
        
    def send_prompt(self, **kwargs):
        """
        Sends a prompt to the AI model and returns the response.

        Args:
            **kwargs: Additional keyword arguments to be passed to the method.

        Returns:
            str: The response from the AI model.

        Raises:
            Exception: If there is an error while sending the prompt.

        """
        try:
            self.kwargs.update(kwargs)
            self.modelId = self.modelId or kwargs.get('modelId', None)
            if not self.modelId:
                raise Exception(f"Please send a valid model id. Available model Ids are {list(self.models_body_registry.keys())}")
            body = self.get_body()
            print(body)
            params = {
                "modelId": self.modelId,
                "accept": kwargs.get('accept', '*/*'),
                "contentType": kwargs.get('contentType', 'application/json'),
                "body": json.dumps(body)
            }
            print(params)
            model_response = self.bedrock_runtime.invoke_model_with_response_stream(**params)
            return self.format_streeming_response(model_response)
        except Exception as e:
            raise Exception(f"Failed to send prompt to Aws Bedrock. Error is {e}")
        
    def format_streeming_response(self, model_response):
        """
        Formats the streaming response from the AI model.

        Args:
            model_response (dict): The streaming response from the AI model.

        Returns:
            str: The formatted response from the AI model.

        Raises:
            Exception: If there is an error while formatting the response.

        """
        try:
            output = ""
            for response in model_response["body"]:
                json_response = json.loads(response["chunk"]["bytes"])
                output += json_response[self.model_data.get('streeming_response_obj', 'completion')]
            return output
        except Exception as e:
            raise Exception("Failed to format response from Aws Bedrock. Error is {e}")
