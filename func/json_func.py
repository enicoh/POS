from flask import request

def _json():
    """Helper function to parse JSON request data."""
    return request.get_json(silent=True) or {}