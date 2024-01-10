from product.models import ProductPrompt, TestType
import datetime

def get_prompts_for_device(device_id=None, device_name=None, test_type_id=None, **kwargs):
    try:
        filters = {}
        if not device_id and not device_name:
            raise Exception(f"send device id or device name to get prompts")
        if device_id:
            filters['product_id'] = device_id
        elif device_name:
            filters['product__product_code'] = device_name
        test_type = TestType.objects.filter(id=test_type_id).first()
        if test_type:
            test_type = test_type.code
        else:
            raise Exception(f"Invalid test type passed to get prompts for device ")
        
        product_prompts = [ prompt.replace('${TestType}', test_type) for prompt in  ProductPrompt.objects.filter(**filters).values_list('executable_prompt', flat=True)]
        
        print(product_prompts)
        return product_prompts
    except Exception as e:
        raise e
    
def get_string_from_datetime(_timestamp=None):
    if not _timestamp:
        _timestamp = datetime.datetime.now()
    return _timestamp.strftime("%Y-%m-%d %H_%M_%S")