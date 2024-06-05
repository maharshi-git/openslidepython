from flask import Flask, jsonify, send_file, request, Response
from flask_cors import CORS
# from openslide import open_slide
from PIL import Image
import os, sys, time
import json
import xmltodict

from io import BytesIO

import xml.etree.ElementTree as ET
import numpy as np

import csv

app = Flask(__name__)
CORS(app)

# annotations = ''

OPENSLIDE_PATH = r'C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\openslide-bin-4.0.0.2-windows-x64\bin'




os.environ['PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT'] = '100.0'

if getattr(sys, 'frozen', False):
    # The application is running as a bundled executable
    current_dir = os.path.dirname(sys.executable)
else:
    # The application is running as a script
    current_dir = os.path.dirname(os.path.abspath(__file__))

if hasattr(os, 'add_dll_directory'):
    # Python >= 3.8 on Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
        from openslide.deepzoom import DeepZoomGenerator
else:
    import openslide
    from openslide.deepzoom import DeepZoomGenerator
    
    
current_dir = os.path.dirname(os.path.abspath(__file__))
# C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\static\tiles\C23 - 4007 - 2049765 - LSIL.ndpi
# dir = os.path.join(current_dir ,'static', 'tiles','CMU-1.ndpi')
dir = os.path.join(current_dir ,'static', 'tiles','C23 - 4007 - 2049765 - LSIL.ndpi')
slide = openslide.open_slide(dir)

# dzi = DeepZoomGenerator(slide, tile_size=254, overlap=1)

width, height = slide.dimensions

# The 4 corner coordinates are (0, 0), (width, 0), (0, height), and (width, height)
corners = [(0, 0), (width, 0), (0, height), (width, height)]

print(corners)


    
    

def get_directories(path):
    dir_dict = { "name": os.path.basename(path), "type": "directory" }
    dir_dict["children"] = [
        get_directories(os.path.join(path, name)) if os.path.isdir(os.path.join(path, name)) 
        else { "name": name, "type": "file" } 
        for name in os.listdir(path)
    ]
    return dir_dict

@app.route('/tileSlide', methods=['GET'])
def tileSlide():
#     # Get the specified tile
    predict_list = get_box_list()
    predictArr = []
    
    for i in range(len(predict_list)):
        title,x1,y1,x2,y2,id,cat = predict_list[i]
        left = int(int((x1+x2)/2))
        top = int(int((y1+y2)/2))
     
        openSeaXCoord = (1/width)*left
        openSeaYCoord = (1/height) * top
    
        
        predictArr.append({
            "title": title,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "id": id,
            "cat": cat,
            "left": left,
            "top": top,
            "openSeaXCoord": openSeaXCoord,
            "openSeaYCoord": openSeaYCoord
        })
        
    
        
    returnObj = {"Predicts": predictArr}
    
    with open('test.json', 'w') as f:
        json.dump(returnObj, f)
    
    # dict_data = json.loads(returnObj)
    # fields = dict_data[0].keys()
    
    # with open('output.txt', 'w', newline='') as f_output:
    #     csv_writer = csv.DictWriter(f_output, fieldnames=fields, delimiter='\t')
    #     csv_writer.writeheader()
    #     csv_writer.writerows(dict_data)
    
    # annotations = read_file()
    return returnObj


def read_file():
    
    filename = r'C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\static\tiles\C23 - 4007 - 2049765 - LSIL.ndpi.ndpa'    
    with open(filename, 'r') as file:
        content = file.read()
    data_dict = xmltodict.parse(content)  # Convert XML to OrderedDict
    json_data = json.dumps(data_dict)  # Convert OrderedDict to JSON
    # print(json_data)
    return json_data


@app.route('/get_image/<annotNo>', methods=['GET'])
def get_image(annotNo):
    
    # annotNo = 3
    
    predict_list = get_box_list()
    
    title,x1,y1,x2,y2,id,cat = predict_list[int(annotNo)]
 
    # annotations = read_file()
    
    tile_anote = []                
    # centre of annotation in pixels
    cx = int((x1+x2)/2)  # int(gt[1])
    cy = int((y1+y2)/2)  # int(gt[2])        
    # centering the Groundtruth
    xc, yc = 510/2, 510/2
    left = int(cx - xc)
    top = int(cy - yc)     
    
    # annotations = json.loads(annotations)
    
    # annotObj = annotations['annotations']['ndpviewstate'][int(annotNo)]
    
    # coordinateCentre = (annotObj['x'], annotObj['y'])
    # print(coordinateCentre)
    
    # tile = slide.read_region((32640 ,32640), 0, (510, 510))
    tile = slide.read_region((left ,top), 0, (510, 510))
    
    tile = tile.convert('RGB')

    np_img = np.array(tile)
    np_img = get_bnc_adjusted(np_img,0)

    # Convert the adjusted np_img back to a PIL Image
    adjusted_tile = Image.fromarray(np_img)
    
    output = BytesIO()
    
    adjusted_tile.save(output, format='JPEG')
    tile_bytes = output.getvalue()
  
    # tile.convert("RGB").save(output, format='JPEG')
    tile_bytes = output.getvalue()
    
    return Response(tile_bytes, mimetype='image/jpeg')


@app.route('/tile/<int:level>/<int:row>_<int:col>.jpeg')
def tile(level, row, col):
    
    # print(level, col, row)
    
    zoomDiff = 16 - level

    print(slide.level_dimensions)
    
    slideNo = level - 7
    
    test = [(51200, 38144), (25600, 19072), (12800, 9536), (6400, 4768), (3200, 2384), (1600, 1192), (800, 596), (400, 298), (200, 149), (100, 74.5)]

    
    tile_width = test[slideNo][0]
    # tile_width = slide.level_dimensions[slideNo][0]
    
 
    tile_width = tile_width // 100
    
    print(510*tile_width)
    
    # tile = slide.read_region((row*32640 ,col*32640), level, (510, 510)) #for level 6 the length and bredth is 800 and 596
    # tile = slide.read_region((row*510*tile_width ,col*510*tile_width), zoomDiff, (510, 510)) #for level 6 the length and bredth is 800 and 596
    tile = slide.read_region((row*510*tile_width ,col*510*tile_width), zoomDiff, (510, 510)) #for level 6 the length and bredth is 800 and 596
    # tile = slide.read_region((row*30464 ,col*30464), zoomDiff, (510, 510)) #for level 6 the length and bredth is 800 and 596
    
    # Convert the image data to JPEG format
    output = BytesIO()
  
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
    
    with open(r'C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\annotation.json') as f:
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

def get_box_list(nm_p=221):
        tree = ET.parse(r'C:\Users\mahar\OneDrive\Documents\Custom Applciation\openseadragon\server\static\tiles\C23 - 4007 - 2049765 - LSIL.ndpi.ndpa')
        root = tree.getroot()
        x1, y1, x2, y2 = 0, 0, 0, 0
        box_list = []
        X_Reference, Y_Reference = get_referance(nm_p=nm_p)
        for elem in root.iter():
            # print(elem.tag)
            if elem.tag == 'ndpviewstate':
                title = elem.find('title').text
                cat = ""
                if elem.find('cat') != None:
                    cat = elem.find('cat').text
                
                # cx = int((int(elem.find('x').text) + X_Reference)/nm_p)
                # cy = int((int(elem.find('y').text) + Y_Reference)/nm_p)
                id = elem.get("id")   # MOD

            x = []
            y = []
            if elem.tag == 'pointlist':
                for sub in elem.iter(tag='point'):
                    x.append(int(sub.find('x').text))
                    y.append(int(sub.find('y').text))
                x1 = int((min(x) + X_Reference)/nm_p)
                x2 = int((max(x) + X_Reference)/nm_p)
                y1 = int((min(y) + Y_Reference)/nm_p)
                y2 = int((max(y) + Y_Reference)/nm_p)
                row = [title,x1, y1, x2, y2,id,cat]
                if title.lower() != 'bg':
                    box_list.append(row)
        return box_list

def get_referance(nm_p):
        # slide = self.slideRead()

        w = int(slide.properties.get('openslide.level[0].width'))
        h = int(slide.properties.get('openslide.level[0].height'))

        ImageCenter_X = (w/2)*nm_p
        ImageCenter_Y = (h/2)*nm_p

        OffSet_From_Image_Center_X = slide.properties.get(
            'hamamatsu.XOffsetFromSlideCentre')
        OffSet_From_Image_Center_Y = slide.properties.get(
            'hamamatsu.YOffsetFromSlideCentre')

        # print("offset from Img center units?", OffSet_From_Image_Center_X,OffSet_From_Image_Center_Y)

        X_Ref = float(ImageCenter_X) - float(OffSet_From_Image_Center_X)
        Y_Ref = float(ImageCenter_Y) - float(OffSet_From_Image_Center_Y)
        return X_Ref, Y_Ref
    
def get_bnc_adjusted(img,clip=12):
        hista,histb = np.histogram(img,255)        
        total =0
        n_rem= int((510*510*3*clip)/100)
        for i in reversed(range(255)):
            total +=hista[i]
            if total > n_rem :
                cut_off = int(histb[i])
                break

        alpha = 255/(cut_off)    
        gamma = 0.8
        img_stretched = np.clip(alpha*img, 0, 255)
        img_gama =255 *pow((img_stretched/255),gamma)    
        return img_gama.astype('uint8')
    


if __name__ == '__main__':
    
    # app.run(threaded=False)
    # app.run(debug=True)
    app.run()
    
    
 
