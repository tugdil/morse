import base64
import math
import numpy as np
from pymorse import Morse
from PIL import Image
import time


def get_bounding_boxes():
    with Morse() as morse:
        semantic_camera = morse.robot.semantic_camera
        semantic_camera_data = semantic_camera.get()
        print(semantic_camera_data)
        video_camera = morse.robot.video_camera
        video_camera_data = video_camera.get()
        view_projection = video_camera_data['view_projection_matrix']
        view_projection_matrix = np.array([np.array(x) for x in view_projection])
        intrinsic = video_camera_data['intrinsic_matrix']
        width = intrinsic[0][2] * 2
        height = intrinsic[1][2] * 2

        image_data = video_camera_data['image']
        image_bytes = base64.b64decode(image_data)
        image = Image.frombytes('RGBA',(int(height), int(width)), image_bytes)

        for visible_object in semantic_camera_data['visible_objects']:
            bbox = visible_object['bbox']
            x_min = width + 1
            x_max = -1
            y_min = height + 1
            y_max = -1
            for corner in bbox:
                corner.append(1)
                corner = np.array(corner)
                corner = view_projection_matrix @ corner
                corner /= corner[3]
                corner = corner[:3]
                screen_x = (corner[0] + 1) / 2 * width
                screen_y = (corner[1] + 1) / 2 * height
                if screen_x < x_min:
                    x_min = screen_x
                if screen_x > x_max:
                    x_max = screen_x
                if screen_y < y_min:
                    y_min = screen_y
                if screen_y > y_max:
                    y_max = screen_y
            x_min = math.floor(x_min)
            x_max = math.ceil(x_max)
            y_min = height - math.floor(y_min)
            y_max = height - math.ceil(y_max)
            visible_object['image'] = image.crop((x_min, y_max, x_max, y_min))
    return semantic_camera_data['visible_objects']

time.sleep(2)
for i in range(0, 10):
    visible_objects = get_bounding_boxes()
    for visible_object in visible_objects:
        img = visible_object['image']
        img.save(str(i) + '_' + visible_object['name'] + '.png')
    time.sleep(1)