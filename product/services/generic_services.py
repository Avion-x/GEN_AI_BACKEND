from product.models import ProductPrompt, TestType
import datetime
import os
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

        prompts = ProductPrompt.objects.filter(**filters).values_list('executable_prompt', flat=True)
        response = {}
        for test_id in test_type_id:
            test_type = TestType.objects.filter(id=test_id).first()
            if test_type:
                for test_category in test_type.test_category.filter(status=1, is_approved=1).all():
                    for test_code, test_code_details in test_category.executable_codes.items():
                        test_prompts = [prompt.replace('${TestType}', test_code_details.get("code", test_code)) for prompt in  prompts] if test_code_details.get("code", None) else []
                        test_prompts += test_code_details.get("default", [])
                        if not len(test_prompts):
                            continue
                        if response.get(test_type.code):
                            response[test_type.code][test_code] = test_prompts
                        else:
                            response[test_type.code] = {"test_type_id": test_type.id}
                            response[test_type.code][test_code] = test_prompts
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