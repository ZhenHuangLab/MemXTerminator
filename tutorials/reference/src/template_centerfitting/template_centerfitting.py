import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom
from scipy.signal import correlate2d
from .generate_gaussian_template import *
from ._utils import *
from .radon_analyser import *

class Template_centerfitting:
    def __init__(self, sigma1, sigma2, image, crop_rate, thr, theta_start, theta_end, template_size, sigma_range, sigma_step):
        radonanalyze = RadonAnalyzer(image, crop_rate=crop_rate, thr=thr, theta_start=theta_start, theta_end=theta_end, print_results=False)
        self.gray_image = image
        self.image_size = self.gray_image.shape[0]
        self.theta, self.membrane_distance = radonanalyze.return_results()
        self.template_size = template_size
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.sigma_range = sigma_range
        self.sigma_step = sigma_step
        self.template = generate_template(self.template_size, self.theta+90, self.membrane_distance, self.sigma1, self.sigma2)
        self.y0, self.x0 = radonanalyze.get_vertical_points()
        self.y, self.x = radonanalyze.get_vertical_points()
        self.n = self.template_size
        self.x = self.x.astype(np.int32)
        self.y = self.y.astype(np.int32)
        self.corr_lst = []

    def get_region(self, i):
        center_x = self.x[i]
        center_y = self.y[i]
        padding = self.n // 2
        padded_array = np.pad(self.gray_image, padding, mode='constant', constant_values=0)
        region = padded_array[center_x: center_x + self.n, center_y: center_y + self.n]
        return region

    def centerfinder(self):
        for i in range(len(self.x)):
            region = self.get_region(i)
            region = (region - np.mean(region)) / np.std(region)
            template = (self.template - np.mean(self.template)) / np.std(self.template)
            correlation_result = correlate2d(region, template, mode='full')
            corr_score = np.max(correlation_result)
            self.corr_lst.append(corr_score)
        self.corr_max = max(self.corr_lst)
        self.corr_max_index = self.corr_lst.index(self.corr_max)
        self.yc = self.x0[self.corr_max_index]
        self.xc = self.y0[self.corr_max_index]
        print('====Center fitting results====')
        print('membrane center y:', self.yc)
        print('membrane center x:', self.xc)
        return self.xc, self.yc

    def visualize_center(self):
        fig, axes = plt.subplots(1, 4, figsize=(10, 5))
        axes[0].title.set_text('Cross-Correlation score')
        axes[0].plot(self.corr_lst, 'x-', color = 'yellow')
        axes[1].title.set_text('Template')
        axes[1].imshow(self.template, cmap='gray', origin='lower')
        axes[2].title.set_text('Region(max score)')
        axes[2].imshow(self.get_region(self.corr_max_index), cmap='gray', origin='lower')
        axes[3].title.set_text('Original image with center')
        axes[3].imshow(self.gray_image, cmap='gray', origin='lower')
        axes[3].plot(self.xc, self.yc, 'x', color = 'yellow')
        plt.show()
    
    def fit_sigma(self):
        self.cc_region = self.get_region(self.corr_max_index)
        self.cc_region = (self.cc_region - np.mean(self.cc_region)) / np.std(self.cc_region)
        self.corr_sigma_score1 = []
        number1 = int(self.sigma_range*self.sigma1/self.sigma_step)
        number2 = int(self.sigma_range*self.sigma2/self.sigma_step)
        corr_sigma = np.linspace(0.1, self.sigma_range*self.sigma1, number1)
        print('====Sigma fitting results====')
        for i in corr_sigma:
            sigma_temp = i
            template_n = generate_template(self.template_size, self.theta+90, self.membrane_distance, sigma_temp, self.sigma2)
            template_n = (template_n - np.mean(template_n)) / np.std(template_n)
            corr_result = correlate2d(self.cc_region, template_n, mode='same')
            self.corr_sigma_score1.append(np.max(corr_result))
        corr_best_sigma_score = max(self.corr_sigma_score1)
        corr_best_sigma_index = self.corr_sigma_score1.index(corr_best_sigma_score)
        best_sigma1 = corr_sigma[corr_best_sigma_index]
        print('best sigma1:', best_sigma1)
        self.corr_sigma_score2 = []
        corr_sigma = np.linspace(0.1, self.sigma_range*self.sigma2, number2)
        for i in corr_sigma:
            sigma_temp = i
            template_n_n = generate_template(self.template_size, self.theta+90, self.membrane_distance, best_sigma1, sigma_temp)
            template_n_n = (template_n - np.mean(template_n_n)) / np.std(template_n_n)
            corr_result = correlate2d(self.cc_region, template_n_n, mode='same')
            self.corr_sigma_score2.append(np.max(corr_result))
        corr_best_sigma_score = max(self.corr_sigma_score2)
        corr_best_sigma_index = self.corr_sigma_score2.index(corr_best_sigma_score)
        best_sigma2 = corr_sigma[corr_best_sigma_index]
        print('best sigma2:', best_sigma2)
        self.template = generate_template(self.template_size, self.theta+90, self.membrane_distance, best_sigma1, best_sigma2)
        return best_sigma1, best_sigma2
    
    def fit_sigma_visualize(self):
        fig, axes = plt.subplots(1, 4, figsize=(10, 5))
        axes[0].title.set_text('Center Region')
        axes[0].imshow(self.cc_region, cmap='gray', origin='lower')
        axes[1].title.set_text('Template with best sigmas')
        axes[1].imshow(self.template, cmap='gray', origin='lower')
        axes[2].title.set_text('CC score(sigma1)')
        axes[2].plot(self.corr_sigma_score1, 'x')
        axes[3].title.set_text('CC score(sigma2)')
        axes[3].plot(self.corr_sigma_score2, 'x')
        plt.show()