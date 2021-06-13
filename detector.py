"""
Author: Pedro F. Proenza

Copyright (c) 2017 Matterport, Inc.
Licensed under the MIT License
Written by Waleed Abdulla

"""

import os
import time
import numpy as np
import json
import csv
import random
from imgaug import augmenters as iaa

from dataset import Taco
import model as modellib
from model import MaskRCNN
from config import Config
import visualize
import utils
import matplotlib.pyplot as plt
import keras

from pycocotools.cocoeval import COCOeval
from pycocotools import mask as maskUtils

# Root directory of the models
ROOT_DIR = os.path.abspath("./models")

# Directory to save logs and model checkpoints
DEFAULT_LOGS_DIR = os.path.join(ROOT_DIR, "logs")

############################################################
#  Testing functions
############################################################

def test_dataset(model, dataset):

    image_id = random.choice(dataset.image_ids)

    image, image_meta, gt_class_id, gt_bbox, gt_mask = \
        modellib.load_image_gt(dataset, config, image_id, use_mini_mask=False)
    info = dataset.image_info[image_id]

    r = model.detect([image], verbose=0)[0]

    name = visualize.display_instances(image, r['rois'], r['masks'], r['class_ids'],
                                dataset.class_names, r['scores'])
    # plt.show()
    return ([dataset.class_names[i] for i in r['class_ids']], name)

# Read map of target classes
class_map = {}
with open('./taco_config/map_10.csv') as csvfile:
    reader = csv.reader(csvfile)
    class_map = {row[0]: row[1] for row in reader}

dataset_test = Taco()
taco = dataset_test.load_taco('../data', 0, "test", class_map=class_map, return_taco=True)
dataset_test.prepare()
nr_classes = dataset_test.num_classes

class TacoTestConfig(Config):
    NAME = "taco"
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    DETECTION_MIN_CONFIDENCE = 0.85
    NUM_CLASSES = nr_classes
config = TacoTestConfig()
config.display()

model = MaskRCNN(mode="inference", config=config, model_dir=DEFAULT_LOGS_DIR)

# Select weights file to load
model_path = 'models/logs/mask_rcnn_coco.h5'
model.load_weights(model_path, by_name=True)

def shrek():
    return test_dataset(model, dataset_test)