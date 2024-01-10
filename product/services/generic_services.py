from product.models import ProductPrompt
import datetime

def get_prompts_for_device(device_id=None, device_name=None, test_type=None):
    try:
        filters = {}
        if not device_id and not device_name:
            raise Exception(f"send device id or device name to get prompts")
        if device_id:
            filters['product_id'] = device_id
        elif device_name:
            filters['product__product_code'] = device_name
        product_prompts = [ prompt.replace('${TestType}', test_type) for prompt in  ProductPrompt.objects.filter(**filters).values_list('executable_prompt', flat=True)]
        print(product_prompts)
        return product_prompts
    except Exception as e:
        raise e
    
def get_string_from_datetime(_timestamp=None):
    if not _timestamp:
        _timestamp = datetime.datetime.now()
    return _timestamp.strftime("%Y-%m-%d %H_%M_%S")