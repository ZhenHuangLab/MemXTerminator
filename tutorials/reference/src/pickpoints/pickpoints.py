import numpy as np
from scipy.ndimage import maximum_filter

def max_filter(image):
    max_filtered_image = maximum_filter(image, size=9, mode='constant')
    threshold = np.sum(max_filtered_image) / np.sum(max_filtered_image > 0)
    max_filtered_image[max_filtered_image <= threshold * max_filtered_image.max()] = 0
    # normalization
    max_filtered_image = max_filtered_image / max_filtered_image.max()
    return max_filtered_image

def pickpoints(image, num_points):
    points = []
    for _ in range(num_points):
        while True:
            i, j = np.random.randint(0, image.shape[0]), np.random.randint(0, image.shape[1])
            if np.random.random() < image[i, j]:
                points.append((j, i))  # 保存(x, y)坐标，注意索引的顺序
                break

    return points

def generate_data_points(image, num_points):
    max_filtered_image = max_filter(image)
    data_points = np.array(pickpoints(max_filtered_image, num_points))
    if np.std(data_points[:, 1]) > np.std(data_points[:, 0]):
        data_points = data_points[np.argsort(data_points[:, 1])]
    else:
        data_points = data_points[np.argsort(data_points[:, 0])]
    return data_points