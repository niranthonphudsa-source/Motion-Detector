import csv

def init_csv(filename):
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(["X", "Y"])

def append_keypoints(filename, keypoints):
    with open(filename, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        for kpx, kpy in keypoints:
            writer.writerow([kpx, kpy])
