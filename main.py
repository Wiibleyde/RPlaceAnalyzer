import gzip
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import requests
from os import path, makedirs
import argparse
import yaml

CONFIG = {
    'db': {
        'host': 'MONGODBIP',
        'port': 0000,
    },
}

CSV_LINK = "https://nathan.bonnell.fr/public/tile_placements.csv"
FILES_PATH = './dataset/'

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
    client = MongoClient(CONFIG['db']['host'], CONFIG['db']['port'])
    db = client['rplace']
    return db

def init_collection(db):
    return db['rplace_history_2017']

def download_file():
    if not path.exists(FILES_PATH):
        makedirs(FILES_PATH)
    response = requests.get(CSV_LINK)
    with open(FILES_PATH + 'tile_placements.csv', 'wb') as f:
        f.write(response.content)

# Load all files from 2022_place_canvas_history-000000000000.csv.gzip to 2022_place_canvas_history-000000000078.csv.gzip
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
    # Clear collection
    collection.delete_many({})
    for file in files:
        with open(file, 'rb') as f:
            df = pd.read_csv(f)
            print(f"Loading data from file: {file} (this may take a while (again))")
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
                try:
                    record['ts'] = datetime.fromtimestamp(record['ts'] / 1000)
                    record['x_coordinate'] = int(record['x_coordinate'])
                    record['y_coordinate'] = int(record['y_coordinate'])
                except Exception as e:
                    print(f"Error processing record: {record} with error: {e}")
                    continue
            collection.insert_many(records)
            print(f"Data from file: {file} loaded")

def get_data(collection, query):
    result = collection.find(query)
    return result

# Generate image from data using matplotlib
def generate_image(data):
    canvas = np.zeros((1001, 1001, 3), dtype=np.uint8)
    for row in data:
        try:
            y = row['x_coordinate']
            x = row['y_coordinate']
            color = row['color']
            color = COLORS[color]
            canvas[x, y] = color
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    plt.imshow(canvas)
    plt.show()

# Generate heatmap from data using matplotlib
def generate_heatmap(data):
    canvas = np.zeros((1001, 1001), dtype=np.uint8)
    for row in data:
        try:
            y = row['x_coordinate']
            x = row['y_coordinate']
            canvas[x, y] += 1
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue
    plt.imshow(canvas, cmap='hot', interpolation='nearest')
    plt.axis(False)
    plt.show()

def generate_histogram(data):
    histogram_data = {}
    for row in data:
        try:
            timestamp = row['ts']
            # Truncate timestamp to date only (year, month, day, hour)
            timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            if timestamp in histogram_data:
                histogram_data[timestamp] += 1
            else:
                histogram_data[timestamp] = 1
        except Exception as e:
            print(f"Error processing row: {row} with error: {e}")
            continue

    # Generate histogram
    fig, ax = plt.subplots()
    ax.bar(histogram_data.keys(), histogram_data.values(), width=0.03)  # Use bar chart for pre-counted data
    ax.xaxis.set_major_locator(mdates.HourLocator(interval = 2))  # Set major ticks every hour
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %Hh'))  # Format x-axis to show hour and minute

    plt.xlabel('Hour')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.title('Histogram of Data')
    plt.show()

def load_config():
    with open('config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def parse_args():
    parser = argparse.ArgumentParser(description='Generate image from r/place data')
    parser.add_argument('-i', '--init', action='store_true', help='Download file and initialize DB and load data')
    parser.add_argument('-g', '--generate', action='store_true', help='Generate image from data (pixel placement)')
    parser.add_argument('-hm', '--heatmap', action='store_true', help='Generate heatmap from data (placement count per pixel)')
    parser.add_argument('-hi', '--histogram', action='store_true', help='Generate histogram from data (pixel count per hour)')
    return parser.parse_args()

if __name__ == '__main__':
    CONFIG = load_config()
    args = parse_args()
    db = init_db()
    collection = init_collection(db)
    print(f"DB and collection initialized")
    if args.init:
        print("Initializing...", end='\r')
        print("Downloading file... (this may take a while)")
        download_file()
        files = [FILES_PATH + 'tile_placements.csv']
        print("File downloaded, loading data to DB...", end='\r')
        load_data_to_db([FILES_PATH + 'tile_placements.csv'], collection)
        print(f"Data loaded to DB, exiting program")
        exit(0)
    elif args.generate:
        print("Generating image...")
        data = get_data(collection, {})
        print(f"Data loaded, generating image... (this may take a while)")
        generate_image(data)
    elif args.heatmap:
        print("Generating heatmap...")
        data = get_data(collection, {})
        print(f"Data loaded, generating heatmap... (this may take a while)")
        generate_heatmap(data)
    elif args.histogram:
        print("Generating histogram...")
        data = get_data(collection, {})
        print(f"Data loaded, generating histogram... (this may take a while)")
        generate_histogram(data)
    else:
        print("Please provide an argument")
        exit(1)
