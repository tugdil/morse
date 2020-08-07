import os
from PIL import Image
import csv


def combine_csv():
    with open(os.path.join('/home/matthias/morse/bboxes/simulationData/images/data', 'meta_data.csv'), mode='w') as out_file:
        writer = csv.writer(out_file)
        reader = csv.reader(open(os.path.join('/home/matthias/morse/bboxes/simulationData/images/Fri Jul 31 17:20:16 2020', 'meta_data.csv')))
        header = True
        idx = 0
        for row in reader:
            if header:
                header = False
                writer.writerow([row[0], row[2], row[3], row[4], row[5], row[6]])
                continue

            image = Image.open(os.path.join('/home/matthias/morse/bboxes/simulationData/images/Fri Jul 31 17:20:16 2020', '{}.png'.format(int(row[0]))))
            new_path = os.path.join('/home/matthias/morse/bboxes/simulationData/images/data', '{}.png'.format(idx))
            image.save(new_path)
            new_row = [str(idx), row[2], row[3], row[4], row[5], row[6]]
            writer.writerow(new_row)
            idx += 1

        reader = csv.reader(open(os.path.join('/home/matthias/morse/bboxes/simulationData/images/Fri Jul 31 17:29:13 2020','meta_data.csv')))
        header = True
        for row in reader:
            if header:
                header = False
                continue

            image = Image.open(
                os.path.join('/home/matthias/morse/bboxes/simulationData/images/Fri Jul 31 17:29:13 2020',
                             '{}.png'.format(int(row[0]))))
            new_path = os.path.join('/home/matthias/morse/bboxes/simulationData/images/data', '{}.png'.format(idx))
            image.save(new_path)
            new_row = [str(idx), row[2], row[3], row[4], row[5], row[6]]
            writer.writerow(new_row)
            idx += 1


combine_csv()
print('done')