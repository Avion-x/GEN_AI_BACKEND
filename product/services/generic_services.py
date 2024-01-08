from product.models import ProductPrompt


def get_prompts_for_device(device_id=None, device_name=None):
    try:
        filters = {}
        if not device_id or not device_name:
            raise Exception(f"send device id or device name to get prompts")
        if device_id:
            filters['product_id'] = device_id
        elif device_name:
            filters['product__product_code'] = device_name
        product_prompts = ProductPrompt.objects.filter(**filters).values_list('executable_prompt', flat=True)
        prompts = ". ".join(product_prompts)
        return prompts
    except Exception as e:
        raise e