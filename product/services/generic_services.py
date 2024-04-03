
from product.models import ProductPrompt, TestType, ProductSubCategory, Customer, ProductCategoryPromptCode, Prompt, ProductCategoryPrompt
from product.serializers import ProductSubCategorySerializer, CustomerSerializer, PromptSerializer
import datetime
import os, re, json
from user.settings import BASE_DIR
import boto3, pdfplumber
from io import BytesIO

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION  # Override default region
)
s3 = session.client('s3')


def get_prompts_for_device(device_id=None, device_name=None, test_type_data=[], **kwargs):
    try:
        filters = {}
        category_filters = {}
        if not device_id and not device_name:
            raise Exception(f"send device id or device name to get prompts")
        if device_id:
            filters['product_id'] = device_id
        elif device_name:
            filters['product__product_code'] = device_name

        prompts = ProductPrompt.objects.filter(**filters, status=1).values_list('executable_prompt', flat=True)
        response = {}
        for _test in test_type_data:
            test_id = _test.get("test_type_id", None)
            if test_id is None:
                raise Exception(f"Could not find test type id for tests")
            test_categories = _test.get("test_category_ids", [])
            if len(test_categories):
                category_filters = {'id__in':test_categories}
            test_type = TestType.objects.filter(id=test_id).first()
            if test_type:
                response[test_type.code] = {}
                for test_category in test_type.test_category.filter(status=1, is_approved=1, **category_filters).all():
                    for test_code, test_code_details in test_category.executable_codes.items():
                        test_prompts = [prompt.replace('${TestType}', test_code_details.get("code", test_code)) for prompt in  prompts] if test_code_details.get("code", None) else []
                        test_prompts += test_code_details.get("default", [])
                        test_prompts = {"kb_query":get_knowledge_base_query(test_category), "prompts" : test_prompts}
                        if not len(test_prompts):
                            continue
                        if response.get(test_type.code) and response[test_type.code].get(test_category.name):
                            response[test_type.code][test_category.name][test_code] = test_prompts
                        else:
                            response[test_type.code][test_category.name] = {"test_category_id": test_category.id}
                            response[test_type.code][test_category.name][test_code] = test_prompts
        if not response:
            raise Exception(f"Incorrect configuration of test types, Please verify once")
        return response
    except Exception as e:
        raise e

def get_knowledge_base_query(test_category):
    kb_queries = test_category.knowledge_base_prompts.all()
    data = []
    for query in kb_queries:
        _q = query.query.replace('${TestCategory}', test_category.name)
        data.append({"top_k":query.top_k, "kb_prompt_id":query.id,  "query":_q, "default_query_data":query.default_data})
    return data


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


def download_files_from_s3(bucket_name, key_prefix, local_directory):
    try:
        # List objects in the specified S3 directory
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=key_prefix)
        
        # Check if any objects are found
        if 'Contents' in response:
            # Create local directory if it doesn't exist
            os.makedirs(local_directory, exist_ok=True)
            
            # Iterate over objects and download them
            for obj in response['Contents']:
                key = obj['Key']
                file_name = os.path.basename(key)
                local_path = os.path.join(local_directory, file_name)
                # Download file from S3 to local filesystem
                s3.download_file(bucket_name, key, local_path)
            return True
        else:
            raise Exception("No files found in the specified directory.")
    except Exception as e:
        raise e

    


def delete_local_directory(local_directory):
    # Delete the local
    if os.path.exists(local_directory):
        os.rmdir(local_directory)
        return (True, f"Local directory '{local_directory}' deleted.")
    else:
        return (False, f"Local directory '{local_directory}' not found")


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


# Function to extract table as matrix
def extract_table_as_matrix(page):
    table = page.extract_table()
    if table is None:
        return None

    # Convert table to matrix
    matrix = []
    for row in table:
        matrix_row = []
        for cell in row:
            if cell:
                matrix_row.append(cell)
        if matrix_row:
            matrix.append(matrix_row)

    return matrix


def extract_pdf(bucket_name, folder_path):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
        for obj in response.get('Contents', []):
            pdf_file = obj['Key']
            if pdf_file.endswith('.pdf'):
                # Download PDF from S3
                s3_response_object = s3.get_object(Bucket=bucket_name, Key=pdf_file)
                pdf_content = s3_response_object['Body'].read()

                # Process PDF content and write to S3
                with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                    processed_text = ""
                    for page in pdf.pages:
                        string = ""
                        # Extract text from the page
                        text = page.extract_text()
                        processed_text += text + "\n"
                        matrix = extract_table_as_matrix(page)
                        if matrix and all(len(sublist) == len(matrix[0]) for sublist in matrix):
                            for row in matrix[1:-1]:
                                # Iterate over each column other than the first one
                                for i in range(1, len(row)):
                                    string += f"{matrix[0][0]}, {row[0]}, {matrix[0][i]}, {row[i]},"
                            if string:
                                processed_text += string[:-1] + "\n"
                        processed_text += '\n'

                # Convert processed text to BytesIO object
                processed_text_bytes = BytesIO(processed_text.encode('utf-8'))
                # Create text file name
                file_name = folder_path + "processed/" + pdf_file.split('/')[-1][:-4] + "_" + str(datetime.datetime.today()) + '.txt'

                # Upload the processed file directly to S3 in the same folder
                s3.put_object(Bucket=bucket_name, Key=file_name, Body=processed_text_bytes)

        return {"message": "Text extraction and upload completed successfully", "status": 200}
    
    except Exception as e:
        return {"message": f"Failed to upload text file for {file_name}", "status": 400}
