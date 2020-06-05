from morse_connection import MorseConnection
import os
import time
import csv
from PIL import Image
import shutil

positions_mode = True
positions_file = 'positions.csv'
trajectory_file = 'trajectory.csv'
base_path = os.path.join(os.getcwd(), 'simulationData')
print(base_path)
this_time = time.asctime()
images_path = os.path.join(base_path, 'images')
out_path = os.path.join(images_path, this_time)
os.mkdir(out_path)
out_dict = {}
img_dict = {}
idx = 0

morse_connection = MorseConnection()

if positions_mode:
    with open(os.path.join(base_path, positions_file)) as positions:
        positions_reader = csv.reader(positions)
        counter = 0
        for row in positions_reader:
            frame_path = os.path.join(base_path, 'frames', 'frame' + str(counter))
            filename = 'screenshot_' + str(counter)
            morse_connection.position_robot([float(row[0]), float(row[1]), float(row[2])],
                                            [float(row[3]), float(row[4]), float(row[5])])
            time.sleep(1)
            # send message via socket
            bbox_message = 'simulation get_b_boxes ["' + frame_path + '", "' + filename + '"]'
            morse_connection.morse_write(bbox_message)
            jpg_filename = os.path.join(frame_path, filename + '.jpg')
            while not os.path.exists(jpg_filename):
                continue
            time.sleep(1)
            screenshot = Image.open(jpg_filename)
            csv_filename = os.path.join(frame_path, filename + '.csv')
            while not os.path.exists(csv_filename):
                continue
            time.sleep(1)
            with open(csv_filename) as bbox_data:
                bbox_reader = csv.reader(bbox_data)
                line_count = 0
                for row in bbox_reader:
                    if line_count == 0:
                        width = int(row[0])
                        height = int(row[1])
                    if line_count > 1:
                        if int(row[1]) >= 0 and int(row[2]) < width and int(row[3]) >= 0 and int(
                                row[4]) < height and float(row[5]) <= 1:
                            bbox_img = screenshot.crop((int(row[1]), int(row[4]), int(row[2]), int(row[3])))
                            img_dict[idx] = bbox_img
                            out_dict[idx] = [idx, row[0], os.path.join(out_path, row[0] + str(idx) + '.png'), row[6],
                                             row[7],
                                             row[8], row[9], row[10], row[11]]
                            idx += 1
                            # bbox_img.save(os.path.join(scene_path, row[0] + '_' + str(counter) + '.png'))
                    line_count += 1
            counter += 1

        morse_connection.close_connection()

        print('writing files...')
        with open(os.path.join(out_path, 'meta_data.csv'), mode='w') as meta_file:
            writer = csv.writer(meta_file)
            for idx in list(out_dict):
                meta_data = out_dict[idx]
                img_dict[idx].save(meta_data[2])
                writer.writerow(meta_data)

    shutil.rmtree(os.path.join(base_path, 'frames'))