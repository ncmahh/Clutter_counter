import glob
from PIL import Image
import json
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import csv
from csv import writer
import os


## returns array of images
def get_image_paths(filepath):
    '''
    :param filepath: folder containing the images to process
    :return: an array of images paths
    '''

    # CHECK FILEPATH
    if(filepath[-1] != '\\'):
        filepath = filepath + '\\'
    if(filepath[-1] != '*'):
        filepath = filepath + '*'

    valid_extensions = ['.jpg', '.HEIC', '.HEIF', '.jpeg']

    #GET ARRAY OF IMAGES PATHS
    print("Files in folder: \n")
    images = []
    for filename in glob.glob(filepath):
        #image = Image.open(filename)
        print("\n" + filename)
        images.append(filename)

    return images

def get_labels(filepath):
    '''
    takes the image and gets the labels and rectangles from an api
    saves the json data to a master list and a new individual file
    returns the json data as a dictionary
    :param filepath: filepath to a single image to process
    :return: dictionary containing labels and data from the api, excluding the price and outcome status (sucess/failure)
    '''
    #TO DO: 

    headers = {"Authorization": "Bearer test"}

    url = "https://api.edenai.run/v2/image/object_detection"
    data = {
        "providers": "api4ai",                  #currently seleceted api4ai because it is the cheapest. Swap for Amazon once actually storing data
        "fallback_providers": "SentiSight.ai"
    }
    files = {'file': open(filepath, 'rb')}

    response = requests.post(url, data=data, files=files, headers=headers)


    # CHECK RESPONSE AND SAVE JSON
    if response.status_code == 200:
        #get text
        result = json.loads(response.text)
        # print(result['api4ai']['items'])
        print(result)

        #SAVE DATA - DELETE LATER?
        new_data = response.json()

        #OPEN JSON
        try:
            with open("data.json", "r") as json_file:
                existing_data = json.load(json_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            existing_data = []                                  

        existing_data.append(new_data)
        print(new_data)

        # Create new json file with data
        with open("data_new.json", "w") as json_file:
            json.dump(existing_data, json_file, indent=4)
            print("Data appended to data_new.json file.")

        #add to running list
        with open("data.json", "w") as json_file:
            json.dump(existing_data, json_file, indent=4)
            print("Data appended to data.json file.")
    else:
        print("Failed to retrieve data from the API. Status code:", response.status_code)
    
    #EXTRACT DICTIONARY
    data = pd.read_json("data_new.json")        #swap this to skip the saving and reopening step
    labels = data['sentisight'].loc['items'][0]
    
    return labels

def load_json_temp():
    '''
    Temporary function to load saved data while testing. 
    Will later be replaced with get_labels()
    and skip calling the api
    :return: pandas dataframe containing data from an api call. 
    '''
    data = pd.read_json("data_single.json")        #swap this to skip the saving and reopening step
    labels = data['sentisight'].loc['items'][0]
    labels_pd = pd.DataFrame([labels])

    return labels_pd

def draw_square(im_filepath, labels):
    '''
    draws a rectangle on the image according to what was identified in the json data
    saves this as a svg
    **need to update this to work with multiple images**
    :param filepath: filepath to a single image to process
    :param labels: dictionary of data received from the api
    :return: none
    '''
    #open image
    im = Image.open(im_filepath)

    #make a rectangle
    rect = Rectangle((labels['x_min'][0]*im.width, labels['y_min'][0]*im.height),labels['x_max'][0]*im.width, labels['y_max'][0]*im.height,linewidth=2,edgecolor='r',facecolor='none')

    #add rectangle to image
    plt.imshow(im)
    ax = plt.gca()
    ax.add_patch(rect)

    plt.savefig("image_square.svg")

def check_label(im_filepath, labels):
    '''
    Asks the user to confirm if the label is correct. 
    If not asks the user for a new label and stores that value. 
    :parem data: dictionary of the data given by the api. It should contain the key "label"
    :return: updated dataframe
    '''
    #save image with a sqaure around the object
    draw_square(im_filepath, labels)
    ans1 = input("\nIs the object in the square a " + labels['label'][0] + "? Y/N: \n")

    if(ans1 == "Y"):
         return labels
    else: 
        labels["label"] = input("\nPlease enter the name of the object: \n")

    return labels

def save_data_csv(image_data, csv_path):
    '''
    appends the new csv data to the given csv file
    :parem image_data: dictionary of the data given by the api. It should contain the key "label"
    :parem csv_name: string of the path to the csv to save the data to
    :return: none
    '''
    
    ### need to add check for if there was no csv 
    # with open('total_data.csv', 'a') as csv_object:
    #     writer_object = writer(csv_object)
    #     writer_object.writerow(image_data)
    if os.path.isfile(csv_path):
        check_contents_df = pd.read_csv(csv_path, names=[""])
        if(~check_contents_df.empty):
            image_data.to_csv(csv_path, mode='a', index=False, header=False)
    else: 
        image_data.to_csv(csv_path, mode='a', index=False, header=True)

        
def label_images():
    '''
    runs all functions from getting the user input, getting labels for the image
    checking the labels with the user, storing the confirmed label and repeating for 
    all remaining images. 
    :return: none
    '''
    #GET FOLDER OF PHOTOS FROM THE USER
    filepath = input("\nPlease enter a path to the new image: ")
    images = get_image_paths(filepath)        #get array of filepaths to images

    #GET LABELS FROM API -- temporarily disabled for testing other functions
    # image_data_arr = []
    # for image in images:
    #     temp_labels = get_labels(filepath)
    #     image_data_arr.append(temp_labels)

    ##TEMP: LOAD SAVED JSON DATA
    data = load_json_temp()             #delete later and use the get_labels(images[0])
    
    #CHECK LABELS WITH USER
    data = check_label(images[0], data)

    #STORE DATA
    save_data_csv(data, "test.csv")





