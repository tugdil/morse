import os
import base64
import math
import numpy as np
from pymorse import Morse
from PIL import Image
import time
import csv

base_path = os.path.join(os.getcwd(), 'simulationData')
this_time = time.asctime()
images_path = os.path.join(base_path, 'images')
out_path = os.path.join(images_path, this_time)
os.mkdir(out_path)
idx = 0


def send_destination(s, simu, x, y, yaw):
    s.publish({'x': x, 'y': y, 'z': 0, 'yaw': yaw, 'pitch': 0.0, 'roll': 0.0})
    simu.sleep(0.5)


with Morse() as morse:
    semantic_camera = morse.robot.semantic_camera
    video_camera = morse.robot.video_camera
    teleport_client = morse.robot.motion
    with open(os.path.join(out_path, 'meta_data.csv'), mode='w') as meta_file:
        meta_writer = csv.writer(meta_file)
        with open(os.path.join(base_path, 'positions.csv')) as positions:
            positions_reader = csv.reader(positions)
            counter = 0
            for position in positions_reader:
                send_destination(teleport_client, morse, float(position[0]), float(position[1]), float(position[2]))
                semantic_camera_data = semantic_camera.get()
                print(semantic_camera_data)
                video_camera_data = video_camera.get()
                view_projection = video_camera_data['view_projection_matrix']
                view_projection_matrix = np.array([np.array(x) for x in view_projection])
                intrinsic = video_camera_data['intrinsic_matrix']
                width = intrinsic[0][2] * 2
                height = intrinsic[1][2] * 2

                image_data = video_camera_data['image']
                image_bytes = base64.b64decode(image_data)
                image = Image.frombytes('RGBA', (int(height), int(width)), image_bytes)

                for visible_object in semantic_camera_data['visible_objects']:
                    bbox = visible_object['bbox']
                    x_min = width
                    x_max = 0
                    y_min = height
                    y_max = 0
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
                    print(''+str(x_min)+', '+str(x_max))
                    img = image.crop((x_min, y_max, x_max, y_min))
                    img_name = str(idx) + '_' + visible_object['name'] + '.png'
                    image_path = os.path.join(out_path, img_name)
                    img.save(image_path)
                    object_category = visible_object['name'].split('.')[0]
                    meta_writer.writerow([idx, image_path, object_category, visible_object['name']])
                    idx += 1
                counter += 1
