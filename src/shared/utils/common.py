import json


def to_serializable(obj):
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def extract_context_from_event(event):
    data = event["data"].get("result").model_dump()
    content = data.get("content")
    if isinstance(content, str):
        return json.loads(content)
    return content
