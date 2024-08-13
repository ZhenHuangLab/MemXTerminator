import numpy as np
import matplotlib.pyplot as plt
from ._utils import *
from .template_centerfitting import *
from .radon_analyser import *
from .calculate_curve import *
from .generate_membrane_mask import *
from scipy.interpolate import interp1d

class average_membrane:
    def __init__(self, image, extra_mem_dist, edge_sigma, rlnCenterY, rlnCenterX, rlnAngleTheta, rlnMembraneDistance, rlnSigma1, rlnSigma2, rlnCurveKappa):
        self.image = image
        self.x0 = rlnCenterY
        self.y0 = rlnCenterX
        self.theta = rlnAngleTheta * np.pi / 180
        self.membrane_distance = rlnMembraneDistance
        self.kappa = rlnCurveKappa
        self.edge_sigma = edge_sigma
        self.sigma1 = rlnSigma1
        self.sigma2 = rlnSigma2
        self.image_size = image.shape[0]
        self.distance_mat = np.zeros((self.image_size, self.image_size))
        self.test_img = np.zeros((self.image_size, self.image_size))
        self.membrane_average_1d = []
        self.membrane_average_2d = np.zeros((self.image_size, self.image_size))
        self.membrane_dist_lst = [i for i in np.arange(-self.membrane_distance-extra_mem_dist, self.membrane_distance+extra_mem_dist+1)]
    def generate_dist_mat(self):
        curve_generator = Curve(self.image, y0=self.y0, x0=self.x0, theta=self.theta, kappa=self.kappa, rlnSigma1=self.sigma1, rlnSigma2=self.sigma2, rlnMembraneDistance=self.membrane_distance)
        distance_mat = curve_generator.compute()
        return distance_mat
    
    def calculate_membrane_average(self):
        self.distance_mat = self.generate_dist_mat()
        for k in self.membrane_dist_lst:
            mask = (k - 1 < self.distance_mat) & (self.distance_mat <= k)
            gray_values = self.image[mask]
            gray_value_average = np.average(gray_values)
            self.membrane_average_1d.append(gray_value_average)
        self.membrane_average_1d = np.array(self.membrane_average_1d)
        return self.membrane_average_1d

    def generate_2d_average_mem(self):
        membrane_average_2d = np.zeros_like(self.distance_mat)
        self.membrane_dist_lst = np.array(self.membrane_dist_lst)
        min_mem_dist = min(self.membrane_dist_lst)
        max_mem_dist = max(self.membrane_dist_lst)
        f = interp1d(self.membrane_dist_lst, self.membrane_average_1d, kind='linear')
        in_range_mask = (self.distance_mat >= min_mem_dist) & (self.distance_mat <= max_mem_dist)
        membrane_average_2d[in_range_mask] = np.array(f(self.distance_mat[in_range_mask]))
        gray_value = np.exp(-(np.abs(self.distance_mat) - self.membrane_distance)**2 / (2 * self.edge_sigma**2))
        membrane_average_2d[np.abs(self.distance_mat) > self.membrane_distance] *= gray_value[np.abs(self.distance_mat) > self.membrane_distance]
        membrane_average_2d[(gray_value < 0.001) & (np.abs(self.distance_mat) > self.membrane_distance)] = 0
        self.membrane_average_2d = membrane_average_2d
        return membrane_average_2d
    
    def visualize_membrane_average(self):
        fig, ax = plt.subplots(1,3,figsize=(10,5))
        ax[0].title.set_text('Original Image')
        ax[0].imshow(self.image, cmap='gray', origin='lower')
        ax[1].title.set_text('1D Membrane Average')
        ax[1].plot(self.membrane_average_1d, '-x', color='red')    
        ax[2].title.set_text('2D Membrane Average')
        ax[2].imshow(self.membrane_average_2d, cmap='gray', origin='lower')
        plt.show()

