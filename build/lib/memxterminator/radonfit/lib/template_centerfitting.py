import numpy as np
import cupy as cp
import matplotlib.pyplot as plt
from cupyx.scipy.signal import correlate2d
from .generate_gaussian_template import *
from ._utils import *
from .radonanalyser import *
from cupyx.scipy.ndimage import zoom

class Template_centerfitting:
    def __init__(self, output_filename, i, sigma1, sigma2, image, crop_rate, thr, theta_start, theta_end, template_size, sigma_range, sigma_step):
        df_star = readstar(output_filename)
        self.output_filename = output_filename
        radonanalyze = RadonAnalyzer(output_filename, i, image, crop_rate=crop_rate, thr=thr, theta_start=theta_start, theta_end=theta_end)
        self.i = i
        self.gray_image = image
        self.image_size = self.gray_image.shape[0]
        self.theta = df_star.loc[self.i, 'rlnAngleTheta']
        self.membrane_distance = df_star.loc[self.i, 'rlnMembraneDistance']
        self.template_size = template_size
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.sigma_range = sigma_range
        self.sigma_step = sigma_step
        self.template = generate_template(self.template_size, self.theta+90, self.membrane_distance, self.sigma1, self.sigma2, mode='gpu')
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
        padded_array = cp.pad(self.gray_image, padding, mode='constant', constant_values=0)
        region = padded_array[center_x: center_x + self.n, center_y: center_y + self.n]
        return region

    def centerfinder(self):
        print('>>>Start center fitting...')
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
        print('membrane center y:', self.yc)
        print('membrane center x:', self.xc)

        df_star = readstar(self.output_filename)
        df_star.loc[self.i, 'rlnCenterX'] = self.xc
        df_star.loc[self.i, 'rlnCenterY'] = self.yc
        write_star(df_star, self.output_filename)
        return self.xc, self.yc
    
    def fit_sigma(self):
        self.cc_region = self.get_region(self.corr_max_index)
        self.cc_region = (self.cc_region - cp.mean(self.cc_region)) / cp.std(self.cc_region)
        self.corr_sigma_score1 = []
        number1 = int(self.sigma_range*self.sigma1/self.sigma_step)
        number2 = int(self.sigma_range*self.sigma2/self.sigma_step)
        corr_sigma = cp.linspace(0.1, self.sigma_range*self.sigma1, number1)
        print('>>>Start fitting sigma...')
        for i in corr_sigma:
            sigma_temp = i
            template_n = generate_template(self.template_size, self.theta+90, self.membrane_distance, sigma_temp, self.sigma2, mode='gpu')
            template_n = (template_n - cp.mean(template_n)) / cp.std(template_n)
            corr_result = correlate2d(self.cc_region, template_n, mode='same')
            self.corr_sigma_score1.append(cp.max(corr_result))
        corr_best_sigma_score = max(self.corr_sigma_score1)
        corr_best_sigma_index = self.corr_sigma_score1.index(corr_best_sigma_score)
        best_sigma1 = corr_sigma[corr_best_sigma_index]
        print('best sigma1:', best_sigma1)
        self.corr_sigma_score2 = []
        corr_sigma = cp.linspace(0.1, self.sigma_range*self.sigma2, number2)
        for i in corr_sigma:
            sigma_temp = i
            template_n_n = generate_template(self.template_size, self.theta+90, self.membrane_distance, best_sigma1, sigma_temp, mode='gpu')
            template_n_n = (template_n - cp.mean(template_n_n)) / cp.std(template_n_n)
            corr_result = correlate2d(self.cc_region, template_n_n, mode='same')
            self.corr_sigma_score2.append(cp.max(corr_result))
        corr_best_sigma_score = max(self.corr_sigma_score2)
        corr_best_sigma_index = self.corr_sigma_score2.index(corr_best_sigma_score)
        best_sigma2 = corr_sigma[corr_best_sigma_index]
        print('best sigma2:', best_sigma2)        
        df_star = readstar(self.output_filename)
        df_star.loc[self.i, 'rlnSigma1'] = best_sigma1
        df_star.loc[self.i, 'rlnSigma2'] = best_sigma2
        write_star(df_star, self.output_filename)
        return best_sigma1, best_sigma2

