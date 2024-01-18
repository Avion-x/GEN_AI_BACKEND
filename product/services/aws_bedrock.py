import boto3
import json

class AwsBedrock(object):

    def __init__(self, model="amazon.titan-text-express-v1"):
        self.bedrock_runtime = boto3.client('bedrock-runtime',
            aws_access_key_id='AKIA3MUTZS7BNCEROH24',
            aws_secret_access_key='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')
        self.model = model

    def send_prompt(self, prompts="", maxTokenCount=3900, temparature=0.5, topP=0.1, stopSequences=[], accept='application/json', contentType='application/json'):
        prompts+=". Provide data with markdown compatable for headers, sub headers, paragraphs, and code snippets in the output."
        self.body = {
            "inputText": prompts,
            "textGenerationConfig" : {
                "maxTokenCount": maxTokenCount,
                # "temperature": temparature,
                # "topP": topP,
                # "stopSequences": stopSequences
            }
        }

        print(self.body)

        response = self.bedrock_runtime.invoke_model(body=json.dumps(self.body), modelId=self.model, accept=accept, contentType=contentType)

        response_body = response['body'].read().decode()
        json_response = json.loads(response_body)

        return json_response.get('results', [{}])[0].get('outputText', "")