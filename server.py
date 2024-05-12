from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
# from openslide import open_slide
# from PIL import Image
import os
import json

app = Flask(__name__)
CORS(app)

def get_directories(path):
    dir_dict = { "name": os.path.basename(path), "type": "directory" }
    dir_dict["children"] = [
        get_directories(os.path.join(path, name)) if os.path.isdir(os.path.join(path, name)) 
        else { "name": name, "type": "file" } 
        for name in os.listdir(path)
    ]
    return dir_dict

@app.route('/get-directory-structure', methods=['GET'])
def get_directory_structure():
    directories = get_directories(r'C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\resources')
    return jsonify(directories)


@app.route('/getAnnotation', methods=['POST'])
def getAnnotation():
    print('api hit')
    data = request.get_json()

    try:
        comment = data['body'][0]['value']
    except:
        comment = ''

    try:
        tags = data['body'][1]['value']
    except:
        tags = ''
    
    id = data['id']

    try:
        coordinates = data['target']['selector']['value']
        _, pixel_values = coordinates.split(":")
        x, y, width, height = pixel_values.split(",")
        # x = float(x)
        # y = float(y)
        # width = float(width)
        # height = float(height)
    except:
        coordinates = ''
    
    # print(comment, tags, x, y, width, height)
    data = {
        "id": id,
        "comment": comment,
        "tags": tags,
        "coordinates": {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
    }
    
    with open('annotation.json', 'r') as f:
        try:
            data_list = json.load(f)
        except json.JSONDecodeError:
            data_list = []
            
    data_list.append(data)
    
    with open('annotation.json', 'w') as f:
        json.dump(data_list, f)
    
    if not data:
        return jsonify({"message": "No JSON received"}), 400
    return jsonify({"message": "JSON received"}), 200


@app.route('/getSavedAnnotation', methods=['GET'])
def getSavedAnnotation():
    # return 'test'
    with open('annotation.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/deleteAnnotation', methods=['POST'])
def deleteAnnotation():
    data = request.get_json()
    id = data['id']
    with open('annotation.json', 'r') as f:
        data_list = json.load(f)
    
    for i in range(len(data_list)):
        if data_list[i]['id'] == id:
            data_list.pop(i)
            break
    
    with open('annotation.json', 'w') as f:
        json.dump(data_list, f)
    
    return jsonify({"message": "Annotation deleted"}), 200

@app.route('/updateAnnotation', methods=['POST'])
def updateAnnotation():
    data = request.get_json()
    id = data['id']
    comment = data['comment']
    tags = data['tags']
    coordinates = data['coordinates']
    x = coordinates['x']
    y = coordinates['y']
    width = coordinates['width']
    height = coordinates['height']
    
    with open('annotation.json', 'r') as f:
        data_list = json.load(f)
    
    for i in range(len(data_list)):
        if data_list[i]['id'] == id:
            data_list[i]['comment'] = comment
            data_list[i]['tags'] = tags
            data_list[i]['coordinates']['x'] = x
            data_list[i]['coordinates']['y'] = y
            data_list[i]['coordinates']['width'] = width
            data_list[i]['coordinates']['height'] = height
            break
    
    with open('annotation.json', 'w') as f:
        json.dump(data_list, f)
    
    return jsonify({"message": "Annotation updated"}), 200


if __name__ == '__main__':
    app.run(debug=True)
