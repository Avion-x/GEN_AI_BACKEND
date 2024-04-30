

from product.models import Product, StructuredTestCases
from product.services.aws_bedrock import AwsBedrock
from product.services.generic_services import parseModelDataToList, rebuild_request
from product.services.github_service import push_to_github, CustomGithub
from product.services.langchain_ import Langchain_
from product.services.open_ai import CustomOpenAI
from user.models import CustomerConfig
from sentence_transformers import SentenceTransformer, util
from product.services.custom_logger import logger
import threading

_thread_locals = threading.local()


class GenerateTests:
    AiModels = {
        "open_ai": CustomOpenAI,
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
            for test_type, tests in self.prompts_data.items():
                for test_main in tests:
                    response[test_type] = {}
                    for test, test_data in test_main.items():
                        response[test_type][test] = self.execute(self.request, test_type, test, test_data, self.test_names)
            return response
        except Exception as e:
            raise e

    def execute(self, request, test_type, test_category, input_data, test_names):
        try:
            response = {}
            insert_data = {"test_category_id": input_data.pop("test_category_id", None), "device_id": self.device.id,
                           "prompts": input_data}
            from product.views import insert_test_case
            for test_code, details in input_data.items():
                kb_data = self.lang_chain.execute_kb_queries(details.get('kb_query', []))
                print("\n\n kb data is :", kb_data)
                prompts = details.get('prompts', [])
                prompts = [prompts[0].replace('${a.content}', kb_data)]
                file_path = self.get_file_path(request, test_type, test_category, test_code)
                response[test_code] = self.generate_tests(prompts=prompts, context=kb_data)

                result = self.store_parsed_tests(request=request, data = response[test_code], test_type=test_type, test_category=test_category, test_category_id=insert_data.get("test_category_id"), test_names=test_names)
                if result:
                    git = CustomGithub(request.user.customer)
                    insert_data['git_data'] = git.push_to_github(data=response[test_code].pop('raw_text', ""), file_path=file_path)
                    insert_test_case(request, data=insert_data.copy())
            # response['test_category'] = test_category
            return response
        except Exception as e:
            raise e

    def store_parsed_tests(self, request, data, test_type, test_category, test_category_id, test_names):
        for test_case, test_script in zip(data.get('test_cases', []), data.get('test_scripts', [])):
            name = test_case.get('testname', test_case.get('name', "")).replace(" ", "_").lower()
            test_id = f"{request.user.customer.name}_{test_type}_{test_category}_{self.device.product_code}_{name}".replace(
                " ", "_").lower()
            _test_case = {
                "test_id": test_id,
                "test_name": f"{name}",
                "objective": test_case.get("objective", ""),
                "data": test_case,
                "type": "TESTCASE",
                "test_category_id": test_category_id,
                "product": self.device,
                "customer": request.user.customer,
                "request_id": self.request.request_id,
                "created_by": request.user
            }

            _test_script = {
                "test_id": test_id,
                "test_name": f"{name}",
                "objective": test_script.get("objective", ""),
                "data": test_script,
                "type": "TESTSCRIPT",
                "test_category_id": test_category_id,
                "product": self.device,
                "customer": request.user.customer,
                "request_id": self.request.request_id,
                "created_by": request.user
            }

            # similarity = self.check_semantic_similarity(name=name, test_names=test_names)
            similarity = True
            if similarity:
                StructuredTestCases.objects.create(**_test_case)
                StructuredTestCases.objects.create(**_test_script)
                return True
            return False
    
    def check_semantic_similarity(self, name, test_names, threshold=95):
        try:
            model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            embedding1 = model.encode(name, convert_to_tensor=True)

            # Print current heading1 being compared
            logger.log(level='INFO', message="Checking '{}' for similarities:".format(name.strip()))
            # print("Checking '{}' for similarities:".format(name.strip()))        

            embedding1 = model.encode(name.strip(), convert_to_tensor=True)

            for heading2 in test_names:
                embedding2 = model.encode(heading2.strip(), convert_to_tensor=True)

                cosine_score = util.pytorch_cos_sim(embedding1, embedding2).item()
                similarity_percentage = cosine_score * 100

                logger.log(level='INFO', message="Similarity between '{}' and '{}': {:.2f}%".format(name.strip(), heading2.strip(), similarity_percentage))

                # Print similarity percentage for current combination
                # print("Similarity between '{}' and '{}': {:.2f}%".format(name.strip(), heading2.strip(), similarity_percentage))

                if similarity_percentage >= threshold:
                    logger.log(level='INFO', message="Above similarity is greater than 95% so no need to add that value".format(name.strip()))
                    return False
            else:
                return True
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while checking similarity,{e}")
            return False

    def get_file_path(self, request, test_type, test_category, test_code):
        try:
            device_code = self.device.product_code
            path = CustomerConfig.objects.filter(config_type='repo_folder_path',
                                                 customer=request.user.customer).first().config_value
            return path.replace("${device_code}", device_code) \
                .replace("${test_type}", test_type) \
                .replace("${test_category}", test_category) \
                .replace("${test_code}", test_code)
        except Exception as e:
            return f"data/{request.user.customer.code}/{test_type}/{test_code}"

    def generate_tests(self, prompts, context, **kwargs):
        try:
            response_text = ""
            for prompt in prompts:
                kwargs['prompt'] = prompt
                kwargs['context'] = context
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
