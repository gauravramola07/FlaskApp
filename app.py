import os
import ssl
import certifi
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import json
from dotenv import load_dotenv

load_dotenv()

# Patch pymongo's get_ssl_context to force TLS 1.2
# (prevents TLS 1.3 handshake failures with MongoDB Atlas on Python 3.14 / OpenSSL 3.x)
import pymongo.ssl_support as _ssl_support

_orig_get_ssl_context = _ssl_support.get_ssl_context

def _patched_get_ssl_context(certfile, passphrase, ca_certs, crlfile,
                              allow_invalid_certificates, allow_invalid_hostnames,
                              disable_ocsp_endpoint_check, is_sync):
    ctx = _orig_get_ssl_context(
        certfile, passphrase, ca_certs, crlfile,
        allow_invalid_certificates, allow_invalid_hostnames,
        disable_ocsp_endpoint_check, is_sync,
    )
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx

_ssl_support.get_ssl_context = _patched_get_ssl_context

app = Flask(__name__)

MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DB = os.environ.get('MONGODB_DB')
MONGODB_COLLECTION = os.environ.get('MONGODB_COLLECTION')

if not all([MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION]):
    raise ValueError("Missing MongoDB environment variables. Please set MONGODB_URI, MONGODB_DB, and MONGODB_COLLECTION.")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsAllowInvalidCertificates=False,
    directConnection=False,
    minPoolSize=1,
)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

@app.route('/')
def index():
    return render_template('todo.html')



@app.route('/api')
def get_data():
    try:
        # Fetch all documents from MongoDB collection
        documents = list(collection.find())
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc['_id'] = str(doc['_id'])
        
        return jsonify(documents)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        form_data = dict(request.form)
        result = collection.insert_one(form_data)
        if result.inserted_id:
            return redirect(url_for('success'))
        else:
            return render_template('index.html', error="Failed to insert data")
    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/submittodoitem', methods=['POST'])
def submit_todo_item():
    try:
        item_id = request.form.get('itemId')
        item_uuid = request.form.get('itemUuid')
        item_hash = request.form.get('itemHash')
        item_name = request.form.get('itemName')
        item_description = request.form.get('itemDescription')
        if not item_id or not item_uuid or not item_hash or not item_name or not item_description:
            return render_template('todo.html', error="Item ID, Item UUID, Item Hash, Item Name and Item Description are required."), 400
        todo_data = {
            "itemId": item_id,
            "itemUuid": item_uuid,
            "itemHash": item_hash,
            "itemName": item_name,
            "itemDescription": item_description
        }
        result = collection.insert_one(todo_data)
        if result.inserted_id:
            return redirect(url_for('success'))
        else:
            return render_template('todo.html', error="Failed to insert data"), 500
    except Exception as e:
        return render_template('todo.html', error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
    