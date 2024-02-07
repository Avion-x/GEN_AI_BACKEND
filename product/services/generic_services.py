
from product.models import ProductPrompt, TestType, ProductSubCategory, Customer, ProductCategoryPromptCode, Prompt, ProductCategoryPrompt
from product.serializers import ProductSubCategorySerializer, CustomerSerializer, PromptSerializer
import datetime
import os, re, json
from user.settings import BASE_DIR


def get_prompts_for_device(device_id=None, device_name=None, test_type_id=[], **kwargs):
    try:
        filters = {}
        if not device_id and not device_name:
            raise Exception(f"send device id or device name to get prompts")
        if device_id:
            filters['product_id'] = device_id
        elif device_name:
            filters['product__product_code'] = device_name

        prompts = ProductPrompt.objects.filter(**filters, status=1).values_list('executable_prompt', flat=True)
        response = {}
        for test_id in test_type_id:
            test_type = TestType.objects.filter(id=test_id).first()
            if test_type:
                response[test_type.code] = {}
                for test_category in test_type.test_category.filter(status=1, is_approved=1).all()[:1]:
                    for test_code, test_code_details in test_category.executable_codes.items():
                        test_prompts = [prompt.replace('${TestType}', test_code_details.get("code", test_code)) for prompt in  prompts] if test_code_details.get("code", None) else []
                        test_prompts += test_code_details.get("default", [])
                        if not len(test_prompts):
                            continue
                        if response.get(test_type.code):
                            response[test_type.code][test_category.name][test_code] = test_prompts
                        else:
                            response[test_type.code][test_category.name] = {"test_category_id": test_category.id}
                            response[test_type.code][test_category.name][test_code] = test_prompts
        if not response:
            raise Exception(f"Incorrect configuration of test types, Please verify once")
        return response
    except Exception as e:
        raise e
    
def get_string_from_datetime(_timestamp=None):
    if not _timestamp:
        _timestamp = datetime.datetime.now()
    return _timestamp.strftime("%Y-%m-%d %H_%M_%S")


def validate_mandatory_checks( input_data={}, checks = {}):
    try:
        data = {}
        for check, conditions in checks.items():
            data[check] = input_data.get(check, None)
            if data[check] is None and conditions.get('is_mandatory'):
                raise Exception(f"Please pass {check} in queryparams")
            if not isinstance(data[check], conditions.get('type')) and conditions.get('convert_type'):
                try:
                    data[check] = conditions.get('type')(conditions.get('convert_expression')(data[check])) if conditions.get('convert_expression') else conditions.get('type')(data[check])
                except Exception as e:
                    raise Exception(f"{check} should be of type {conditions.get('type')} and you sent {data[check]},  cannot convert {data[check]} to {conditions.get('type')} ")
        return data
    
    except Exception as e:
        raise Exception(f"Validation of mandatory fields to request test cases failed, Error message is {str(e)}")
    

def write_file(file_path="data/output.md", mode="w", data= ""):
    try:
        directory_path, file_name = os.path.split(file_path)
        directory_path = os.path.join(BASE_DIR, directory_path)
        os.makedirs(directory_path, exist_ok=True)
        os.chmod(directory_path, 0o777)

        with open(os.path.join(directory_path, file_name), "a", encoding="utf-8") as file:
            file.write(data)
    except Exception as e:
        raise e


def parseModelDataToList(text):
    # text = re.search(r"###STARTLIST###(.+)###ENDLIST###", text, re.DOTALL).group(1)
    list_occurences = re.findall(r"###STARTLIST###(.+?)###ENDLIST###", text, re.DOTALL)
    data = []
    for each_list in  list_occurences:
        try:
            data += eval(each_list)
        except Exception as e:
            print(e)
    return data


# def trigger_product_prompt_data(customer_id, product_sub_category_id, product_code, product_id):

#     # get sub_category name using customer_id, prodcut_sub_category_id
#     prod_sub_cate = ProductSubCategory.objects.filter(id=product_sub_category_id, customer=customer_id, status=1)
#     serializer = ProductSubCategorySerializer(prod_sub_cate, many=True)
#     print(serializer.data[0]['sub_category'])
#     sub_category = serializer.data[0]['sub_category']
#     product_category_id = serializer.data[0]['product_category_id']

#     # get customer code and name
#     cust_name = Customer.objects.filter(id=customer_id).values('name', 'code')
#     print(cust_name)
#     serializer_cust = CustomerSerializer(cust_name, many=True)
#     customer_name = serializer_cust.data[0]['name']
#     prouduct_category_prompt_code = customer_name + ' ' + sub_category
#     print(prouduct_category_prompt_code)

#     # here save product_category_prompt_code in product category prompt code table using prompt code, customer_id, product_sub_category_id
#     new_productcategorypromptcode = ProductCategoryPromptCode(product_sub_category=prouduct_category_prompt_code,
#                                                               customer_id=customer_id, status=1,
#                                                               product_sub_category_id=product_sub_category_id)

#     new_productcategorypromptcode.save()


#     # get prompts from prompt table
#     get_prompts = Prompt.objects.filter().values('provider', 'foundation_model', 'prompt', 'id')
#     prompts = PromptSerializer(get_prompts, many=True).data

#     for prompt1 in prompts:
#         prompt = prompt1['prompt']
#         id = prompt1['id']
#         print('1', prompt)
#         if '${ReplaceWithProductCategoryPromptCode}' in prompt:
#             prompt = prompt.replace('${ReplaceWithProductCategoryPromptCode}', prouduct_category_prompt_code)
#             print('2', prompt)

#         # insert into product_category_prompt
#         product_category_prompt_obj = ProductCategoryPromptCode(prompt_code=prompt, prompt_id=id, product_sub_category_id=product_sub_category_id, customer_id=customer_id, status=1)

#         product_category_prompt_obj.save()

#         if '{ReplaceWithProductCode}' in prompt:
#             prompt = prompt.replace('{ReplaceWithProductCode}', product_code)
#             print('4', prompt)

#         # insert into product_prompt table
#         product_prompt_obj = ProductPrompt(executable_prompt=prompt, status=1, customer_id=customer_id,
#                                            product_id=product_id, prompt_id=id, product_category_id=product_category_id)

#         product_prompt_obj.save()


def trigger_product_prompt_data(customer_id, product_sub_category_id, product_code, product_id, last_updated_by):

    # get sub_category name using customer_id, prodcut_sub_category_id
    prod_sub_cate = ProductSubCategory.objects.filter(id=product_sub_category_id, customer=customer_id, status=1)
    serializer = ProductSubCategorySerializer(prod_sub_cate, many=True)
    sub_category = serializer.data[0]['sub_category']
    product_category_id = serializer.data[0]['product_category']

    # get customer code and name
    cust_name = Customer.objects.filter(id=customer_id).values('name', 'code')
    serializer_cust = CustomerSerializer(cust_name, many=True)
    customer_name = serializer_cust.data[0]['name']
    prouduct_category_prompt_code = customer_name + ' ' + sub_category

    # here save product_category_prompt_code in product category prompt code table using prompt code, customer_id, product_sub_category_id
    new_productcategorypromptcode = ProductCategoryPromptCode(prompt_code=prouduct_category_prompt_code,
                                                              customer_id=customer_id, status=1, product_sub_category_id=product_sub_category_id, last_updated_by_id=last_updated_by)
    new_productcategorypromptcode.save()

    # get prompts from prompt table
    get_prompts = Prompt.objects.filter().values('provider', 'foundation_model', 'prompt', 'id')
    prompts = PromptSerializer(get_prompts, many=True).data

    for prompt1 in prompts:
        prompt = prompt1['prompt']
        id = prompt1['id']
        if '${ReplaceWithProductCategoryPromptCode}' in prompt:
            prompt = prompt.replace('${ReplaceWithProductCategoryPromptCode}', prouduct_category_prompt_code)

        # insert into product_category_prompt
        product_category_prompt_obj = ProductCategoryPrompt(executable_prompt=prompt, prompt_id=id, customer_id=customer_id, status=1, last_updated_by_id=last_updated_by, product_category_id=product_category_id, sequence_no=10)

        product_category_prompt_obj.save()

        if '{ReplaceWithProductCode}' in prompt:
            prompt = prompt.replace('{ReplaceWithProductCode}', product_code)

        # insert into product_prompt table
        product_prompt_obj = ProductPrompt(executable_prompt=prompt, status=1, customer_id=customer_id,
                                           product_id=product_id, prompt_id=id, last_updated_by_id=last_updated_by, sequence_no=14)

        product_prompt_obj.save()

