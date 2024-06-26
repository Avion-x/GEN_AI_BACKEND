

from product.models import Product, StructuredTestCases
from product.services.aws_bedrock import AwsBedrock
from product.services.generic_services import parseModelDataToList, rebuild_request
from product.services.github_service import push_to_github, CustomGithub
from product.services.langchain_ import Langchain_
from product.services.open_ai import ChatGPTAssistantManager, CustomOpenAI
from user.models import CustomerConfig
from sentence_transformers import SentenceTransformer, util
from product.services.custom_logger import logger
import threading

_thread_locals = threading.local()


class GenerateTests:
    AiModels = {
        "gpt_35": CustomOpenAI,
        "gpt_40": CustomOpenAI,
        "gpt_assistant": ChatGPTAssistantManager,
        "anthropic.claude-v2:1": AwsBedrock,
        "anthropic.claude-v2": AwsBedrock,
        'amazon.titan-text-express-v1': AwsBedrock,
    }
    
    def __init__(self, request, **kwargs):
        self.body = kwargs.get('body', {})
        self.request = request
        self.ai_obj = self.get_ai_obj(self.body)
        self.set_device(self.body.get('device_id', None))
        self.prompts_data = kwargs.get('prompts_data', {})
        self.test_names = kwargs.get('test_names', [])
        self.lang_chain = Langchain_(prompt_data=self.prompts_data, request=self.request, vector_namespace = self.device.pinecone_name_space)


    def set_device(self, device_id):
        try:
            self.device = Product.objects.get(id=device_id)
        except Exception as e:
            raise e

    def get_ai_obj(self, data):
        try:
            model = data.get('ai_model', "open_ai")
            ai_model = self.AiModels.get(model, None)
            if not ai_model:
                message = f"Please provide valid ai_model, Available models are {list(self.AiModels.keys())}"
                logger.log(level="ERROR", message=message)
                raise Exception(message)
            return ai_model(modelId=model)
        except Exception as e:
            raise e
        
    def process_request(self):
        try:
            response = {}
            for each_test in self.prompts_data:
                self.test_id = each_test.get('test_id')
                self.test_type = each_test.get('test_name') 
                category_data = each_test.get('category_data',[])
                response[self.test_type] = self.process_category_prompts(category_data)
            return response
        except Exception as e:
            raise e
        
    def process_category_prompts(self, category_data=[]):
        response_data = []
        for category in category_data:
            response = {}
            self.category_id = category.get('category_id')
            self.category_name = category.get('category_name')
            self.kb_data = self.lang_chain.execute_kb_queries(category.get('kb_prompt', []))
            sub_catgory_data = category.get('sub_category_data',[])
            response[self.category_name] = self.process_sub_category_prompt(sub_catgory_data)
            response_data.append(response)
        return response_data  

    def process_sub_category_prompt(self, sub_category_data):
        response_data = []
        for sub_category in sub_category_data:
            response = {}
            self.sub_category_id = sub_category.get('sub_category_id')
            self.sub_category_name = sub_category.get('sub_category_name')
            prompt = sub_category.get('actual_prompt', None)
            if not prompt:
                raise Exception(f"Please send the prompt to generate test cases.")
            prompt = prompt.replace('${a.content}', self.kb_data)
            file_path = self.get_file_path(self.test_type, self.category_name, self.sub_category_name)
            response[self.sub_category_name] = self.generate_tests(prompt, context=self.kb_data)
            result = self.store_parsed_tests(data = response[self.sub_category_name])
            if result:
                git = CustomGithub(self.request.user.customer)
                insert_data = {
                    "device_id" : self.device.id,
                    "test_category_id" : self.category_id,
                    "test_sub_category_id" : self.sub_category_id,
                    "prompts" : sub_category_data
                }
                insert_data['git_data'] = git.push_to_github(data=response[self.sub_category_name].pop('raw_text', ""), file_path=file_path)
                from product.views import insert_test_case
                insert_test_case(self.request, data=insert_data.copy())
            response_data.append(response)
        return response_data

    def store_parsed_tests(self, data):
        for test_case, test_script in zip(data.get('test_cases', []), data.get('test_scripts', [])):
            name = test_case.get('testname', test_case.get('name', "")).replace(" ", "_").lower() or test_script.get('testname', test_script.get('name', "")).replace(" ", "_").lower()

            test_id = f"{self.request.user.customer.name}_{self.test_type}_{self.category_name}_{self.device.product_code}_{name}".replace(
                " ", "_").lower()
            _test_case = {
                "test_id": test_id,
                "test_name": f"{name}",
                "objective": test_case.get("objective", ""),
                "data": test_case,
                "type": "TESTCASE",
                "test_category_id": self.category_id,
                "test_sub_category_id" : self.sub_category_id,
                "product": self.device,
                "customer": self.request.user.customer,
                "request_id": self.request.request_id,
                "created_by": self.request.user
            }

            _test_script = {
                "test_id": test_id,
                "test_name": f"{name}",
                "objective": test_script.get("objective", ""),
                "data": test_script,
                "type": "TESTSCRIPT",
                "test_category_id": self.category_id,
                "test_sub_category_id" : self.sub_category_id,
                "product": self.device,
                "customer": self.request.user.customer,
                "request_id": self.request.request_id,
                "created_by": self.request.user
            }

            # similarity = self.check_semantic_similarity(name=name, test_names=test_names)
            similarity = True
            if similarity:
                StructuredTestCases.objects.create(**_test_case)
                StructuredTestCases.objects.create(**_test_script)
                return True
            return False
    
    def check_semantic_similarity(self, name, test_names, threshold=90):
        try:
            print(name)
            print(test_names)
            model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            embedding1 = model.encode(name, convert_to_tensor=True)
            test_names = list(StructuredTestCases.objects.filter(type='TESTCASE').values_list('test_name', flat = True))


            # Print current heading1 being compared
            logger.log(level='INFO', message="Checking '{}' for similarities:".format(name.strip()))
            print("Checking '{}' for similarities:".format(name.strip()))        

            embedding1 = model.encode(name.strip(), convert_to_tensor=True)
            percentage=[]
            for heading2 in test_names:
                embedding2 = model.encode(heading2.strip(), convert_to_tensor=True)

                cosine_score = util.pytorch_cos_sim(embedding1, embedding2).item()
                similarity_percentage = cosine_score * 100
                percentage.append(similarity_percentage)
                #print(similarity_percentage,type(similarity_percentage))

                logger.log(level='INFO', message="Similarity between '{}' and '{}': {:.2f}%".format(name.strip(), heading2.strip(), similarity_percentage))

                # Print similarity percentage for current combination
                print("Similarity between '{}' and '{}': {:.2f}%".format(name.strip(), heading2.strip(), similarity_percentage))

                if similarity_percentage >= threshold:
                    logger.log(level='INFO', message="Above similarity is greater than 90% so no need to add that value".format(name.strip()))
                    return False
            else:
                if any(x >= 90 for x in percentage):
                    pass
                else:

                    StructuredTestCases.objects.create(test_name=name, type='TESTCASE')
                    logger.log(level='INFO', message="Added '{}' to database".format(name.strip()))
                return True
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while checking similarity:{e}")
            return True

    def get_file_path(self, test_type, test_category, test_code):
        try:
            device_code = self.device.product_code
            path = CustomerConfig.objects.filter(config_type='repo_folder_path',
                                                 customer=self.request.user.customer).first().config_value
            return path.replace("${device_code}", device_code) \
                .replace("${test_type}", test_type) \
                .replace("${test_category}", test_category) \
                .replace("${test_code}", test_code)
        except Exception as e:
            return f"data/{self.request.user.customer.code}/{test_type}/{test_code}"

    def generate_tests(self, prompt, context, **kwargs):
        try:
            response_text = ""
            kwargs['prompt'] = prompt
            kwargs['context'] = context
            kwargs.update(self.body)
            prompt_data = self.ai_obj.send_prompt(**kwargs)
            response_text += prompt_data
            return self.get_test_data(response_text)
        except Exception as e:
            raise e

    def get_test_data(self, text_data):
        result = {"raw_text": text_data, "test_cases": [], "test_scripts": []}
        data = parseModelDataToList(text_data)
        for _test in data:
            test_case = _test.get('testcase', None)
            test_scripts = _test.get('testscript', None)
            if test_case and test_scripts:
                if isinstance(test_case, list):
                     result['test_cases'] += test_case
                else:
                    result['test_cases'].append(test_case)

                if isinstance(test_scripts, list):
                    result['test_scripts'] += test_scripts
                else:
                    result['test_scripts'].append(test_scripts)
        return result
