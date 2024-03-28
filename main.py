import gzip
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

CSV_LINK = "https://nathan.bonnell.fr/public/tile_placements.csv"
FILES_PATH = './dataset/'

# index	color code
# 0	#FFFFFF
# 1	#E4E4E4
# 2	#888888
# 3	#222222
# 4	#FFA7D1
# 5	#E50000
# 6	#E59500
# 7	#A06A42
# 8	#E5D900
# 9	#94E044
# 10	#02BE01
# 11	#00E5F0
# 12	#0083C7
# 13	#0000EA
# 14	#E04AFF
# 15	#820080

COLORS = {
    0: [255, 255, 255],
    1: [228, 228, 228],
    2: [136, 136, 136],
    3: [34, 34, 34],
    4: [255, 167, 209],
    5: [229, 0, 0],
    6: [229, 149, 0],
    7: [160, 106, 66],
    8: [229, 217, 0],
    9: [148, 224, 68],
    10: [2, 190, 1],
    11: [0, 229, 240],
    12: [0, 131, 199],
    13: [0, 0, 234],
    14: [224, 74, 255],
    15: [130, 0, 128]
}

def init_db():
    client = MongoClient('localhost', 27017)
    db = client['rplace']
    return db

def init_collection(db):
    return db['rplace_history_2017']

# # Load all files from 2022_place_canvas_history-000000000000.csv.gzip to 2022_place_canvas_history-000000000078.csv.gzip
# def load_files():
#     files = []
#     for i in range(79):
#         file_path = FILES_PATH + '2022_place_canvas_history-' + str(i).zfill(12) + '.csv.gzip'
#         files.append(file_path)
#     return files

# Load data from files
def load_data(files):
    data = []
    for file in files:
        with gzip.open(file, 'rb') as f:
            df = pd.read_csv(f)
            data.append(df)
    return data

def load_data_to_db(files, collection):
    for file in files:
        with open(file, 'rb') as f:
            df = pd.read_csv(f)
            print(f"Loading data from file: {file}")
            records = df.to_dict(orient='records')
            for record in records:
                # 2022
                # try:
                #     record['timestamp'] = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S.%f UTC')
                # except Exception as e:
                #     record['timestamp'] = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S UTC')
                # try:
                #     coords = record['coordinate']
                #     x, y = [int(i) for i in coords.split(',')]
                #     record['x'] = x
                #     record['y'] = y
                #     record.pop('coordinate')
                # except Exception as e:
                #     squareP1, squareP2, squareP3, squareP4 = [int(i) for i in coords.split(',')]
                #     record['squareP1'] = squareP1
                #     record['squareP2'] = squareP2
                #     record['squareP3'] = squareP3
                #     record['squareP4'] = squareP4
                #     record.pop('coordinate')

                # 2017
                record['ts'] = datetime.fromtimestamp(record['ts'] / 1000)
                record['x_coordinate'] = int(record['x_coordinate'])
                record['y_coordinate'] = int(record['y_coordinate'])
            collection.insert_many(records)
            print(f"Data from file: {file} loaded")

def get_data(collection, query):
    result = collection.find(query)
    return result

# Generate image from data using matplotlib
def generate_image(data):
    canvas = np.zeros((1001, 1001, 3), dtype=np.uint8)
    # Invert y axis
    canvas = np.flipud(canvas)
    for row in data:
        try:
            x = row['x_coordinate']
            y = row['y_coordinate']
            color = row['color']
            color = COLORS[color]
            canvas[x, y] = color
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    plt.imshow(canvas)
    plt.show()

def generate_image_old(data):
    canvas = np.zeros((1001, 1001, 3), dtype=np.uint8)
    colors = COLORS
    valid_data = [(row['x_coordinate'], row['y_coordinate'], colors[row['color']]) for row in data if all(key in row for key in ('x_coordinate', 'y_coordinate', 'color'))]
    x, y, color_data = zip(*valid_data)
    canvas[x, y] = color_data
    plt.imshow(canvas)
    plt.show()


if __name__ == '__main__':
    db = init_db()
    collection = init_collection(db)
    print(f"DB and collection initialized")
    # Load all files
    # files = load_files()
    # print(f"Total files: {len(files)} loaded")
    # load_data_to_db(["./dataset/tile_placements.csv"], collection)
    # print(f"Data loaded to DB")
    # Get data from DB
    data = get_data(collection, {})
    print(f"Data loaded, generating image...")
    generate_image(data)
