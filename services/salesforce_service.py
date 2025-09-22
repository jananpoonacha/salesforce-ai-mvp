# services/salesforce_service.py

import streamlit as st
from simple_salesforce import Salesforce, SalesforceGeneralError
import re
import redis
import json

def connect_to_salesforce(username, consumer_key, private_key):
    """
    Connects to Salesforce using JWT Bearer Flow with provided credentials.
    This is used by the offline cache_builder.py script.
    """
    if not all([username, consumer_key, private_key]):
        print("ERROR: Salesforce credentials were not provided.")
        return None
    try:
        return Salesforce(
            username=username,
            consumer_key=consumer_key,
            privatekey=private_key
        )
    except Exception as e:
        print(f"ERROR: Failed to connect to Salesforce: {e}")
        return None

def extract_sfdc_objects_by_keyword(text):
    """
    Performs a simple, text-based search for potential Salesforce object names.
    This acts as a safety net for the AI-based extraction.
    """
    if not text:
        return []
    # This regex finds capitalized words or words ending in __c
    pattern = r'\b([A-Z][a-zA-Z_]*__c|[A-Z][a-zA-Z]{2,})\b'
    potential_objects = re.findall(pattern, text)
    common_words_to_filter = {"As", "I", "When", "The", "A", "If", "But", "Only", "However"}
    return sorted(list(set(obj for obj in potential_objects if obj not in common_words_to_filter)))

def get_org_schema_for_objects(object_names_from_ai):
    """
    Performs a case-insensitive "Fetch and Filter" against the Redis cache
    to get the schema for a given list of object names.
    """
    if not object_names_from_ai:
        return "No objects were identified to fetch schema for.", {}

    debug_data = {}
    try:
        redis_client = redis.Redis(
            host=st.secrets["REDIS_HOST"], port=int(st.secrets["REDIS_PORT"]),
            username=st.secrets["REDIS_USERNAME"], password=st.secrets["REDIS_PASSWORD"],
            ssl=True, ssl_cert_reqs="required", decode_responses=True
        )
        redis_client.ping()
    except Exception as e:
        st.error(f"Could not connect to Redis cache. Error: {e}")
        return "Error: Could not connect to metadata cache.", debug_data
    
    # 1. Fetch the master list of all object names from the cache.
    master_list_json = redis_client.get("sfdc:all_object_names")
    if not master_list_json:
        st.warning("Master object list not found in cache.")
        debug_data["2_Master_Object_List_from_Cache"] = "ERROR: Not Found"
        return "Error: Master object list not found.", debug_data
    
    all_valid_object_names = set(json.loads(master_list_json))
    debug_data["2_Master_Object_List_from_Cache"] = sorted(list(all_valid_object_names))
    
    # 2. Find all actual objects that match the AI's suggestions, case-insensitively.
    matching_object_api_names = set()
    for suggestion in object_names_from_ai:
        suggestion_lower = suggestion.lower()
        for actual_object in all_valid_object_names:
            if suggestion_lower in actual_object.lower():
                matching_object_api_names.add(actual_object)

    debug_data["3_Matched_Objects_After_Filtering"] = sorted(list(matching_object_api_names))
    
    if not matching_object_api_names:
        st.warning(f"No matching schemas found in cache for AI-suggested terms: {', '.join(object_names_from_ai)}.")
        debug_data["4_Final_Schema_Context"] = "None"
        return "Could not retrieve schema from the cache.", debug_data

    # 3. Retrieve all schemas in one go.
    redis_keys_to_fetch = [f"sobject:{name}" for name in matching_object_api_names]
    schema_details = []
    cached_data_list = redis_client.mget(redis_keys_to_fetch)

    for key, cached_data in zip(redis_keys_to_fetch, cached_data_list):
        if cached_data:
            obj_name_from_key = key.split(":")[-1]
            fields_data = json.loads(cached_data)
            fields = [f"{field['name']} ({str(field['type'])})" for field in fields_data if field.get('createable')]
            schema_details.append(f"Object: {obj_name_from_key}\nFields: {', '.join(fields)}")
            
    final_schema_string = "\n\n".join(schema_details)
    debug_data["4_Final_Schema_Context"] = final_schema_string
    
    return final_schema_string, debug_data