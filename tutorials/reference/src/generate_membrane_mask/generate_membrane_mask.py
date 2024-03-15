import numpy as np
import matplotlib.pyplot as plt
from ._utils import *
from .template_centerfitting import *
from .radon_analyser import *
from .calculate_curve import *

class mem_mask:
    def __init__(self, image, edge_sigma, rlnSigma1, rlnSigma2, rlnMembraneDistance, rlnCurveKappa, rlnAngleTheta, rlnCenterX, rlnCenterY):
        self.gray_image = image
        self.edge_sigma = edge_sigma
        self.x0, self.y0 = rlnCenterY, rlnCenterX
        self.theta = rlnAngleTheta * np.pi / 180
        self.membrane_distance = rlnMembraneDistance
        self.kappa = rlnCurveKappa
        self.sigma1, self.sigma2 = rlnSigma1, rlnSigma2
        self.edge_sigma = edge_sigma
        self.image_size = image.shape[0]
        self.distance_mat = np.zeros((self.image_size, self.image_size))
        self.membrane_mask = np.zeros((self.image_size, self.image_size))
        self.masked_image = np.zeros((self.image_size, self.image_size))
    def compute_dist_mat(self):
        curve_generator = Curve(self.gray_image, self.y0, self.x0, self.theta, self.kappa, self.sigma1, self.sigma2, self.membrane_distance)
        self.distance_mat = curve_generator.compute()
        return self.distance_mat
    def generate_mem_mask(self):
        distance_mat_gpu = self.compute_dist_mat()
        mask_within_distance = np.abs(distance_mat_gpu) <= self.membrane_distance
        gray_value = np.exp(-(np.abs(distance_mat_gpu) - self.membrane_distance)**2 / (2 * self.edge_sigma**2))
        mask_small_gray_value = gray_value < 0.001
        mask_outside_distance = ~mask_within_distance
        membrane_mask = np.zeros_like(distance_mat_gpu)
        membrane_mask[mask_within_distance] = 1
        membrane_mask[mask_outside_distance & ~mask_small_gray_value] = gray_value[mask_outside_distance & ~mask_small_gray_value]
        self.membrane_mask = membrane_mask
        return self.membrane_mask
    # def apply_mem_mask(self):
    #     self.membrane_mask = self.generate_mem_mask()
    #     self.masked_image = self.gray_image * self.membrane_mask
    #     return self.masked_image
    def visualize_mem_mask(self):
        self.masked_image = self.apply_mem_mask()
        fig, ax = plt.subplots(1,3,figsize=(15,5))
        ax[0].imshow(self.gray_image, cmap='gray', origin='lower')
        ax[1].imshow(self.membrane_mask, cmap='gray', origin='lower')
        ax[2].imshow(self.masked_image, cmap='gray', origin='lower')
        plt.show()
