from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        response.data = {"error": str(data["detail"])}
        return response

    if isinstance(data, list):
        response.data = {"error": "Please check the submitted information.", "details": data}
        return response

    if isinstance(data, dict):
        field_errors = {}
        for key, value in data.items():
            if key in {"detail", "error"}:
                continue
            if isinstance(value, list):
                field_errors[key] = [str(item) for item in value]
            else:
                field_errors[key] = [str(value)]
        message = "Please check the submitted information."
        if "non_field_errors" in field_errors:
            message = field_errors["non_field_errors"][0]
        elif len(field_errors) == 1:
            only = next(iter(field_errors.values()))
            if only:
                message = only[0]
        response.data = {"error": message, "fields": field_errors}
    return response
