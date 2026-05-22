import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DB = os.environ.get('MONGODB_DB')
MONGODB_COLLECTION = os.environ.get('MONGODB_COLLECTION')

if not all([MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION]):
    raise ValueError("Missing MongoDB environment variables. Please set MONGODB_URI, MONGODB_DB, and MONGODB_COLLECTION.")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api')
def get_data():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
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

if __name__ == '__main__':
    app.run(debug=True)
    