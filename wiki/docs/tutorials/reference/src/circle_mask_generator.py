import numpy as np
import matplotlib.pyplot as plt
from ._utils import *

class circle_mask:
    def __init__(self, image_array, x0, y0, radius, sigma):
        self.image = image_array
        self.image_size = self.image.shape[0]
        self.x0 = x0
        self.y0 = y0
        self.radius = radius
        self.sigma = sigma
        self.distance_matrix = np.zeros((self.image_size, self.image_size))
        self.mask = np.zeros((self.image_size, self.image_size))
    def calculate_distance(self):
        Y, X = np.meshgrid(np.arange(self.image_size), np.arange(self.image_size))
        self.distance_matrix = np.sqrt((X - self.x0)**2 + (Y - self.y0)**2) - self.radius
        return self.distance_matrix
    def generate_mask(self):
        mask_positive = self.distance_matrix <= 0
        self.mask = np.where(mask_positive, 1, np.exp(-self.distance_matrix**2 / (2 * self.sigma**2)))
        return self.mask

    def apply_mask(self):
        self.distance_matrix = self.calculate_distance()
        self.mask = self.generate_mask()
        self.masked_image = self.image * self.mask
        return self.masked_image
    def visualize_mask(self):
        plt.imshow(self.masked_image, cmap='gray')
        plt.show()
