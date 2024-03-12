import numpy as np
import cupy as cp
import matplotlib.pyplot as plt
from skimage.transform import radon
from cupyx.scipy.ndimage import maximum_filter
# from cupyx.scipy.signal import convolve
from ._utils import *
from .circle_mask_generator import *

class RadonAnalyzer:
    def __init__(self, output_filename, i, image, crop_rate, thr, theta_start=0, theta_end=180):
        self.gray_image = image
        self.theta_start = theta_start
        self.theta_end = theta_end
        self.image_size = self.gray_image.shape[0]
        self.crop_rate = crop_rate
        radius = (self.image_size/2) * self.crop_rate
        circle_masker = circle_mask(self.gray_image, x0=self.image_size/2, y0=self.image_size/2, radius=radius, sigma=3)
        self.image_masked = circle_masker.apply_mask()
        
        self.threshold = thr

        print('>>>Start radon analysis...')
        try:
            self.theta, self.projection, self.peaks = self.find_2_peaks()
        except:
            self.theta, self.projection, self.peaks = None, None, None
            print('No peaks found, try again')
        
        if self.theta is not None:
            self.average_theta = np.average(self.peaks[1]+self.theta_start)
            print('average_theta:', self.average_theta)
            self.membrane_distance = self.get_mem_dist()
            print('membrane_distance:', self.membrane_distance)
            self.a = np.cos(self.average_theta * np.pi / 180)
            self.b = np.sin(self.average_theta * np.pi / 180)
            if output_filename == 'None':
                pass
            else:
                self.df_star = readstar(output_filename)
                self.df_star.loc[i, 'rlnAngleTheta'] = self.average_theta
                self.df_star.loc[i, 'rlnMembraneDistance'] = self.membrane_distance
                write_star(self.df_star, output_filename)
    
    def radon_transform(self, theta_start, theta_end):
        theta = np.linspace(theta_start, theta_end, abs(theta_end-theta_start))
        projection = radon(cp.asnumpy(self.image_masked), theta=theta)
        return theta, projection

    def find_peaks_2d(self, image, neighborhood_size, threshold):
        image = cp.asarray(image)
        filtered = maximum_filter(image, size=neighborhood_size, mode='constant')
        peaks = (image == filtered) & (image > threshold)
        peaks_positions = np.where(peaks)
        return peaks_positions


    def find_2_peaks(self):
        theta_start = self.theta_start
        theta_end = self.theta_end
        theta, projection = self.radon_transform(theta_start, theta_end)
        peaks = self.find_peaks_2d(np.flipud(projection), 7, self.threshold * np.max(projection))
        print('peaks:', peaks)
        return theta, projection, peaks

    def get_mem_dist(self):
        self.x0 = self.image_size / 2
        self.y0 = self.image_size / 2
        self.c1 = self.peaks[0][1] - self.x0
        self.c2 = self.peaks[0][0] - self.x0
        self.cc = (self.c1 + self.c2) / 2
        membrane_distance = abs(self.c1 - self.c2)
        # print('membrane_distance:', membrane_distance)
        return membrane_distance

    def get_vertical_points(self): 
        x = cp.linspace(0, self.image_size, self.image_size*5)
        if not cp.isclose(self.a, 0):
            vertical_k =  - self.b / self.a
            y = vertical_k * (x-self.image_size/2)  + self.image_size/2
            mask = (x > 0) & (x < self.image_size) & (y > 0) & (y < self.image_size)
            x = cp.linspace(min(x[mask]), max(x[mask]), 500)
            y = vertical_k * (x-self.image_size/2)  + self.image_size/2
        else:
            x = (self.image_size / 2) * np.ones(self.image_size)
            y = cp.linspace(0, self.image_size-1, self.image_size)
        return x, y


    def visualize_analyze(self):
        theta_start = min(self.theta)
        theta_end = max(self.theta)
        # print(theta)
        # 显示原始图像和Radon变换结果
        fig, axes = plt.subplots(1, 3, figsize=(10, 5))
        axes[0].imshow(self.gray_image.get(), cmap='gray', origin='lower')
        axes[0].set_title("Original Image")
        axes[1].imshow(self.image_masked.get(), cmap='gray', origin='lower')
        axes[1].set_title("Masked Image")
        axes[2].imshow(self.projection, cmap='gray', aspect='auto', extent=(theta_start, theta_end, 0, self.projection.shape[0]))
        axes[2].set_title("Radon Transform")
        axes[2].set_xlabel("Angle (degrees)")
        axes[2].set_ylabel("Projection Distance")
        axes[2].scatter(self.peaks[1].get()+self.theta_start, self.peaks[0].get(), color='red', marker='x')
        # print('b:', self.b)
        #if self.b != 0:
        #    x = np.linspace(0, self.image_size, 100)
        #    y1 = (self.c1 + self.a * x) / self.b - self.a/self.b * self.x0 + self.y0
        #    y2 = (self.c2 + self.a * x) / self.b - self.a/self.b * self.x0 + self.y0
        #    ycc = (self.cc + self.a * x) / self.b - self.a/self.b * self.x0 + self.y0
        #    axes[0].plot(x, y1, color='red')
        #    axes[0].plot(x, y2, color='red')
        #    axes[0].plot(x, ycc, color='blue')
        #else:
        #    x1 = (self.x0 + self.c1) * np.ones(self.image_size)
        #    x2 = (self.x0 + self.c2) * np.ones(self.image_size)
        #    xcc = (self.x0 + self.cc) * np.ones(self.image_size)
        #    y = np.linspace(0, self.image_size, self.image_size)
        #    axes[0].plot(x1, y, color='red')
        #    axes[0].plot(x2, y, color='red')
        #    axes[0].plot(xcc, y, color='blue')
        x_v, y_v = self.get_vertical_points() 
        # axes[0].scatter(x_v, y_v, color='red', marker='x')
        plt.tight_layout()
        plt.show()

