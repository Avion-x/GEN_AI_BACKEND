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

class AwsBedrock():
    def __init__(self, **kwargs):
        self.bedrock_runtime = boto3.client('bedrock-runtime',
            aws_access_key_id='AKIA3MUTZS7BNCEROH24',
            aws_secret_access_key='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',
            region_name='us-west-2')

        self.default_prompt_suffix = """
             . Each testcase and testscript should be encapsulated within its own separate JSON object, and it is an object under the "testname" key. All these JSON objects should be assembled within a Python list, resulting in [{ "testname":"", "testcase":{}, "testscript":{}}] Each test case should include a testname, objective, steps (list of expected results), relevant test data. Make sure each test script JSON object includes the following fields: 'testname', 'objective', 'file_name', 'init_scripts'. The 'init_scripts' field should contain pip install commands for all required packages, 'script' (given in triple quotes), 'run_command' (a command to execute the python file) and 'expected_result'. The Python list with the JSON objects should not include any unrelated context or information. Find the starting delimiter as ###STARTLIST### and the ending delimiter as ###ENDLIST###
        """

        # self.default_prompt_suffix = """
        #      . Each script should be encapsulated within its own JSON object, and all these JSON objects should be assembled within a Python list. Make sure each JSON object includes the following fields: 'name' (test case name), 'objective', 'file_name', 'script' (give me in triple quotes), 'expected_result', 'run_command' (a command to execute the python file), and 'init_scripts'. The 'init_scripts' field should contain pip install commands for all required packages. The Python list with the JSON objects should not include any unrelated context or information. give me a delimitor to find the starting as ###STARTLIST### and ending of the list as ###ENDLIST###
        # """
        
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
                    "prompt": "'\\n\\nHuman:'+self.prompt+' Provide the output in markdown format.'+'\\n\\nAssistant:'",
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
        try:
            self.prompt = self.kwargs.get("prompt", "") + self.default_prompt_suffix
            self.temperature = self.kwargs.get("temperature", None)
            self.top_p = self.kwargs.get("top_p", None)
            self.top_k = self.kwargs.get("top_k", None)
            self.max_tokens = self.kwargs.get("max_tokens", None)
            self.stop_sequence = self.kwargs.get("stop_sequence", [])
        except Exception as e:
            raise Exception("Failed to set default values for Aws Bedrock")
    
    def get_body(self):
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
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.replace_placeholders(value)
            return data
        elif isinstance(data, str):
            return eval(data)
        else:
            return data
        
    def send_prompt(self, **kwargs):
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

            model_response = self.bedrock_runtime.invoke_model_with_response_stream(**params)
            return self.format_streeming_response(model_response)
        except Exception as e:
            raise Exception(f"Failed to send prompt to Aws Bedrock. Error is {e}")
        
    def format_streeming_response(self, model_response):
        try:
            output = ""
            for response in model_response["body"]:
                json_response = json.loads(response["chunk"]["bytes"])
                output += json_response[self.model_data.get('streeming_response_obj', 'completion')]
            return output
        except Exception as e:
            raise Exception("Failed to format response from Aws Bedrock. Error is {e}")
        

# aws = AwsBedrock()
# response = aws.send_prompt(prompt = "Genereate unit test cases for the router MX480.", modelId='anthropic.claude-v2:1')

# print(response)