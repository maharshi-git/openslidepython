from flask import Flask, jsonify, send_file, request, Response
from flask_cors import CORS
# from openslide import open_slide
# from PIL import Image
import os, sys, time
import json

from io import BytesIO

app = Flask(__name__)
CORS(app)




os.environ['PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT'] = '100.0'

if getattr(sys, 'frozen', False):
    # The application is running as a bundled executable
    current_dir = os.path.dirname(sys.executable)
else:
    # The application is running as a script
    current_dir = os.path.dirname(os.path.abspath(__file__))
#tile_viwer = os.path.join(current_dir, 'openslide-win64-20230414', 'bin')

OPENSLIDE_PATH = r'C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\openslide-bin-4.0.0.2-windows-x64\bin'
# print(OPENSLIDE_PATH)
if hasattr(os, 'add_dll_directory'):
    # Python >= 3.8 on Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide
    
    
current_dir = os.path.dirname(os.path.abspath(__file__))
dir = os.path.join(current_dir ,'static', 'tiles','CMU-1.ndpi')
slide = openslide.open_slide(dir)
    
    

def get_directories(path):
    dir_dict = { "name": os.path.basename(path), "type": "directory" }
    dir_dict["children"] = [
        get_directories(os.path.join(path, name)) if os.path.isdir(os.path.join(path, name)) 
        else { "name": name, "type": "file" } 
        for name in os.listdir(path)
    ]
    return dir_dict


@app.route('/tile/<int:level>/<int:row>_<int:col>.jpeg')
# @app.route('/tile/<level>/<int:col>/<int:row>')
def tile(level, col, row):
    # level = request.args.get('level')
    # row = request.args.get('row')
    # col = request.args.get('col')
    # Calculate the tile dimensions
    
    # col= col + 1
    # row = row + 1
    
    print(level, col, row)

    # level = level - 8
    
    # if col == 0:
    # level = 16 - level
    levelArr, zoomLevel = calculate_values(level)
    # level = level
    # tile_width = slide.level_dimensions[level][0]
    # tile_height = slide.level_dimensions[level][1]
    tile_width = slide.level_dimensions[7][0]
    tile_height = slide.level_dimensions[7][1]
    

    
    # //if else condition for col and row
    # if col <= 0:
    #     col = 1 
    # if row <= 0:
    #     row = 1
        
    
    # Read the tile image
    tile = slide.read_region((col*tile_width , row *tile_height), 8, (tile_width, tile_height))
    # tile = slide.read_region((col , row ), level, (tile_width, tile_height))
    
    # Convert the image data to JPEG format
    output = BytesIO()
    # tile_format = "jpeg"
    # tile_bytes = tile.convert("RGB").tobytes(tile_format, "RGB")
    tile.convert("RGB").save(output, format='JPEG')
    tile_bytes = output.getvalue()
    
    return Response(tile_bytes, mimetype='image/jpeg')


def calculate_values(input_value):
    second_value = 18 - input_value
    third_value = input_value - 8
    return second_value, third_value

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
    
    # app.run(threaded=False)
    app.run(debug=True)
