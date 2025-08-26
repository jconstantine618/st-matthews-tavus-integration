# api/create-conversation.py
import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ['TAVUS_API_KEY']
PERSONA_ID = os.environ['PERSONA_ID']
REPLICA_ID = os.environ.get('REPLICA_ID')

@app.route('/', methods=['POST'])
def create_conversation():
    # Build payload with required IDs
    payload = {'persona_id': PERSONA_ID}
    if REPLICA_ID:
        payload['replica_id'] = REPLICA_ID

    # Merge optional fields from the request body
    extra = request.get_json(silent=True) or {}
    for k in ['conversation_name', 'conversational_context', 'callback_url',
              'properties', 'audio_only']:
        if k in extra:
            payload[k] = extra[k]

    # Call Tavus API
    resp = requests.post(
        'https://tavusapi.com/v2/conversations',
        headers={
            'x-api-key': API_KEY,
            'Content-Type': 'application/json'
        },
        json=payload
    )

    # Return Tavus response with CORS headers
    return (
        resp.text,
        resp.status_code,
        {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )
