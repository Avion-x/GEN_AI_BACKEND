from product.models import ProductPrompt, TestType
import datetime

def get_prompts_for_device(device_id=None, device_name=None, test_type_id=[], **kwargs):
    try:
        filters = {}
        if not device_id and not device_name:
            raise Exception(f"send device id or device name to get prompts")
        if device_id:
            filters['product_id'] = device_id
        elif device_name:
            filters['product__product_code'] = device_name
        test_types = TestType.objects.filter(id__in=test_type_id).values_list('code', flat=True)
        if not test_types:
            raise Exception(f"Invalid test type passed to get prompts for device ")
        
        product_prompts = [ prompt.replace('${TestType}', test_type) for test_type in test_types for prompt in  ProductPrompt.objects.filter(**filters).values_list('executable_prompt', flat=True)]

        print(product_prompts)
        return product_prompts
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