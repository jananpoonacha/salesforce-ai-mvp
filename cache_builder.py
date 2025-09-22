# cache_builder.py

import os
import json
from dotenv import load_dotenv
import streamlit as st
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from services import salesforce_service
from urllib.parse import quote_plus

# --- CONFIGURATION ---
PINECONE_INDEX_NAME = "salesforce-knowledge"
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSION = 1536 

def get_metadata_documents(sf):
    """
    Generator function that fetches all metadata from Salesforce
    and yields it as structured text documents.
    """
    print("\n--- Fetching Metadata from Salesforce ---")
    
    # 1. SObjects
    print("Fetching SObjects...")
    all_sobjects = sf.describe()['sobjects']
    object_names = [s['name'] for s in all_sobjects if s['createable']]
    for name in object_names:
        try:
            desc = getattr(sf, name).describe()
            fields = [f"- {f['name']} ({f['type']})" for f in desc['fields']]
            yield {
                "id": f"sobject:{name}",
                "text": f"Salesforce Object Schema for {name}.\nFields:\n" + "\n".join(fields),
                "metadata": {"type": "SObject", "name": name}
            }
        except Exception:
            continue
    
    # 2. Apex Classes
    print("Fetching Apex Classes...")
    classes = sf.query_all("SELECT Name, Body FROM ApexClass WHERE NamespacePrefix = ''")
    for cls in classes['records']:
        yield {
            "id": f"apexclass:{cls['Name']}",
            "text": f"Apex Class named {cls['Name']}.\nCode Body:\n{cls['Body']}",
            "metadata": {"type": "ApexClass", "name": cls['Name']}
        }

    # 3. Flows
    # MODIFIED: Use the direct API call method to avoid library version issues.
    print("Fetching Flows...")
    try:
        base_url = sf.sf_instance
        headers = {'Authorization': f"Bearer {sf.session_id}"}
        api_version = sf.sf_version
        flow_query = "SELECT DeveloperName, ActiveVersion.VersionNumber, Description FROM FlowDefinition"
        encoded_query = quote_plus(flow_query)
        url = f"https://{base_url}/services/data/v{api_version}/tooling/query/?q={encoded_query}"
        
        response = sf.session.get(url, headers=headers)
        response.raise_for_status()
        flows = response.json()

        for flow in flows['records']:
            yield {
                "id": f"flow:{flow['DeveloperName']}",
                "text": f"Salesforce Flow named {flow['DeveloperName']}. Description: {flow.get('Description', 'N/A')}",
                "metadata": {"type": "Flow", "name": flow['DeveloperName']}
            }
    except Exception as e:
        print(f"  - ⚠️ WARNING: Could not fetch Flows. Reason: {e}")

def run_indexing_pipeline():
    """Main function to run the entire indexing process."""
    print("--- Starting Salesforce Metadata Indexing Pipeline ---")
    load_dotenv()
    
    # --- 1. Initialize Clients ---
    try:
        print("Initializing OpenAI and Pinecone clients...")
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        print("✅ Clients initialized.")
    except Exception as e:
        print(f"❌ ERROR: Could not initialize clients. {e}"); return

    # --- 2. Connect to Pinecone Index ---
    try:
        print(f"Connecting to Pinecone index '{PINECONE_INDEX_NAME}'...")
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            print(f"Index not found. Creating a new serverless index with dimension {VECTOR_DIMENSION}...")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=VECTOR_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud='aws', region='us-west-2')
            )
        index = pc.Index(PINECONE_INDEX_NAME)
        print("✅ Connected to Pinecone index.")
    except Exception as e:
        print(f"❌ ERROR: Could not connect to or create Pinecone index. {e}"); return
        
    # --- 3. Connect to Salesforce ---
    print("Connecting to Salesforce...")
    sf_client = salesforce_service.connect_to_salesforce(
        username=os.getenv("SF_USERNAME"),
        consumer_key=os.getenv("SF_CONSUMER_KEY"),
        private_key=os.getenv("SF_PRIVATE_KEY")
    )
    if not sf_client: print("❌ ERROR: Could not connect to Salesforce."); return
    print("✅ Salesforce connection successful.")

    # --- 4. Fetch, Embed, and Upsert Metadata in Batches ---
    print("\n--- Starting Metadata Embedding and Upserting ---")
    batch_size = 100
    vectors_to_upsert = []
    
    for doc in get_metadata_documents(sf_client):
        try:
            embedding = openai_client.embeddings.create(
                input=[doc["text"]],
                model=EMBEDDING_MODEL
            ).data[0].embedding
            
            vectors_to_upsert.append({
                "id": doc["id"],
                "values": embedding,
                "metadata": doc["metadata"]
            })
            
            if len(vectors_to_upsert) >= batch_size:
                print(f"Upserting batch of {len(vectors_to_upsert)} vectors...")
                index.upsert(vectors=vectors_to_upsert)
                vectors_to_upsert = []

        except Exception as e:
            print(f"  - ⚠️ WARNING: Could not process document {doc['id']}. Reason: {e}")

    if vectors_to_upsert:
        print(f"Upserting final batch of {len(vectors_to_upsert)} vectors...")
        index.upsert(vectors=vectors_to_upsert)

    print("\n--- Indexing Pipeline Finished ---")
    print("Final index stats:")
    print(index.describe_index_stats())


if __name__ == "__main__":
    run_indexing_pipeline()