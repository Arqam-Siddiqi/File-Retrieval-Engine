import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from PIL import Image
import io
from collections import defaultdict

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
    update_virtual_file_system()
    save_virtual_file_system()
    
    vfs_by_docId, vfs_by_path = get_vfs()
    return jsonify({
        "vfs_by_docId": vfs_by_docId, 
        "vfs_by_path": vfs_by_path
    })

@app.get("/docs")
def get_all_docs():
    docs = display_document_ids_in_vector_db()
    return jsonify(docs)

@app.get("/search/<string:query>")
def search_docs(query):
    vfs_by_docId, _ = get_vfs()

    res = defaultdict(list)

    result = retrieve_closest_doc(query, k=6)
    output = []
    for id, score in result:
        output.append((id, score))
    output.sort(key=lambda x: x[1], reverse=True)
    
    for id, score in output:
        res[score].append({
            "filename": vfs_by_docId[str(id)]["filename"],
            "path": vfs_by_docId[str(id)]["path"],
            "extension": vfs_by_docId[str(id)]["extension"],
        })

    json_data = json.dumps(res, indent=4, sort_keys=False)

    return Response(json_data, mimetype='application/json')

@app.post("/search-by-image")
def search_by_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    try:
        # Read and convert the uploaded file to PIL Image
        image_bytes = image_file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Get search results
        vfs_by_docId, _ = get_vfs()
        result = retrieve_closest_doc(img, k=6)
        print(result)
        # Format response
        res = defaultdict(list)
        output = []
        for id, score in result:
            output.append((id, score))
        output.sort(key=lambda x: x[1], reverse=True)
        
        for id, score in output:
            res[score].append({
                "filename": vfs_by_docId[str(id)]["filename"],
                "path": vfs_by_docId[str(id)]["path"],
                "extension": vfs_by_docId[str(id)]["extension"],
            })
        
        json_data = json.dumps(res, indent=4, sort_keys=False)
        return Response(json_data, mimetype='application/json')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500