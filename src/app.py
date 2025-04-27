import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from src.ir_service.embeddings import (
    display_document_ids_in_vector_db,
    retrieve_closest_doc
)
from src.ir_service.file_crawler import (
    load_virtual_file_system,
    update_virtual_file_system,
    save_virtual_file_system,
    get_vfs
)

app = Flask(__name__)
CORS(app, origins="*")

@app.get("/")
def ping():
    return jsonify(status="ok")

@app.get("/setup")
def setup():
    load_virtual_file_system()
    update_virtual_file_system("data")
    save_virtual_file_system()
    
    res = get_vfs()
    return jsonify(res)

@app.get("/docs")
def get_all_docs():
    docs = display_document_ids_in_vector_db()
    return jsonify(docs)

@app.get("/search/<string:query>")
def search_docs(query):
    vfs_by_docId, _ = get_vfs()

    res = {}

    result = retrieve_closest_doc(query, k=6)
    output = []
    for id, score in result:
        output.append((id, score))
    output.sort(key=lambda x: x[1], reverse=True)
    
    for id, score in output:
        res[vfs_by_docId[str(id)]["filename"]] = score

    json_data = json.dumps(res, indent=4, sort_keys=False)
    
    return Response(json_data, mimetype='application/json')