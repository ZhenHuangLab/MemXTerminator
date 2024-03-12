import numpy as np
import cupy as cp
import matplotlib.pyplot as plt
from ._utils import *
from .template_centerfitting import *
from .radonanalyser import *
from .calculate_curve import *
from cupyx.scipy.ndimage import zoom

class mem_mask:
    def __init__(self,output_filename, i, image, edge_sigma):
        self.i = i
        self.output_filename = output_filename
        df_star = readstar(output_filename)
        self.gray_image = image
        self.edge_sigma = edge_sigma
        self.x0, self.y0 = df_star.loc[i, 'rlnCenterY'], df_star.loc[i, 'rlnCenterX']
        self.theta = df_star.loc[i, 'rlnAngleTheta'] * np.pi / 180
        self.membrane_distance = df_star.loc[i, 'rlnMembraneDistance']
        self.kappa = df_star.loc[i, 'rlnCurveKappa']
        self.edge_sigma = edge_sigma
        self.image_size = image.shape[0]
        self.distance_mat = cp.zeros((self.image_size, self.image_size))
        self.membrane_mask = cp.zeros((self.image_size, self.image_size))
        self.masked_image = cp.zeros((self.image_size, self.image_size))
    def compute_dist_mat(self):
        curve_generator = Curve(self.output_filename, self.i, self.gray_image, self.y0, self.x0, self.theta, self.kappa)
        self.distance_mat = curve_generator.compute()
        return self.distance_mat

    def generate_mem_mask(self):
        print('>>>Start generating membrane mask...')
        distance_mat_gpu = self.compute_dist_mat()
        mask_within_distance = cp.abs(distance_mat_gpu) <= self.membrane_distance
        gray_value = cp.exp(-(cp.abs(distance_mat_gpu) - self.membrane_distance)**2 / (2 * self.edge_sigma**2))
        mask_small_gray_value = gray_value < 0.001
        mask_outside_distance = ~mask_within_distance
        membrane_mask_gpu = cp.zeros_like(distance_mat_gpu)
        membrane_mask_gpu[mask_within_distance] = 1
        membrane_mask_gpu[mask_outside_distance & ~mask_small_gray_value] = gray_value[mask_outside_distance & ~mask_small_gray_value]
        self.membrane_mask = membrane_mask_gpu.get()
        return self.membrane_mask

    def visualize_mem_mask(self):
        self.masked_image = self.apply_mem_mask()
        fig, ax = plt.subplots(1,3,figsize=(15,5))
        ax[0].imshow(self.gray_image, cmap='gray', origin='lower')
        ax[1].imshow(self.membrane_mask, cmap='gray', origin='lower')
        ax[2].imshow(self.masked_image, cmap='gray', origin='lower')
        plt.show()
    def save_mem_mask(self, filename):
        self.membrane_mask = self.membrane_mask.astype('float32')
        savemrc(self.membrane_mask, filename)