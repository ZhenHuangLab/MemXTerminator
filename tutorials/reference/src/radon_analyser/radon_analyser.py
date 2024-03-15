import numpy as np
import matplotlib.pyplot as plt
from skimage.transform import radon
from scipy.ndimage import maximum_filter
from ._utils import *
from .circle_mask_generator import *

class RadonAnalyzer:
    def __init__(self, image, crop_rate, thr, theta_start=0, theta_end=180, print_results=True):
        self.gray_image = image
        self.theta_start = theta_start
        self.theta_end = theta_end
        self.image_size = self.gray_image.shape[0]
        self.crop_rate = crop_rate
        radius = (self.image_size/2) * self.crop_rate
        circle_masker = circle_mask(self.gray_image, x0=self.image_size/2, y0=self.image_size/2, radius=radius, sigma=3)
        self.image_masked = circle_masker.apply_mask()
        self.threshold = thr
        self.print_results = print_results
        try:
            self.theta, self.projection, self.peaks = self.find_2_peaks()
        except:
            self.theta, self.projection, self.peaks = None, None, None
            print('No peaks found, try again')
        
        if self.theta is not None:
            self.average_theta = np.average(self.peaks[1]+self.theta_start)
            self.membrane_distance = self.get_mem_dist()
            self.a = np.cos(self.average_theta * np.pi / 180)
            self.b = np.sin(self.average_theta * np.pi / 180)
            if print_results:     
                print('average_theta:', self.average_theta)
                print('membrane_distance:', self.membrane_distance)
    
    def radon_transform(self, theta_start, theta_end):
        theta = np.linspace(theta_start, theta_end, abs(theta_end-theta_start))
        projection = radon(self.image_masked, theta=theta)
        return theta, projection

    def find_peaks_2d(self, image, neighborhood_size, threshold):
        image = np.asarray(image)
        filtered = maximum_filter(image, size=neighborhood_size, mode='constant')
        peaks = (image == filtered) & (image > threshold)
        peaks_positions = np.where(peaks)
        return peaks_positions


    def find_2_peaks(self):
        theta_start = self.theta_start
        theta_end = self.theta_end
        theta, projection = self.radon_transform(theta_start, theta_end)
        peaks = self.find_peaks_2d(np.flipud(projection), 7, self.threshold * np.max(projection))
        if self.print_results:
            print('peaks:', peaks)
            print(f'point1: {peaks[0][0]}, {peaks[1][0]}; point2: {peaks[0][1]}, {peaks[1][1]}')
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
        x = np.linspace(0, self.image_size, self.image_size*5)
        if not np.isclose(self.a, 0):
            vertical_k =  - self.b / self.a
            y = vertical_k * (x-self.image_size/2)  + self.image_size/2
            mask = (x > 0) & (x < (self.image_size-1)) & (y > 0) & (y < (self.image_size-1))
            x = np.linspace(min(x[mask]), max(x[mask]), 500)
            y = vertical_k * (x-self.image_size/2)  + self.image_size/2
        else:
            x = (self.image_size / 2) * np.ones(self.image_size)
            y = np.linspace(0, self.image_size-1, self.image_size)
        return x, y

    def visualize_analyze(self):
        theta_start = min(self.theta)
        theta_end = max(self.theta)
        # 显示原始图像和Radon变换结果
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(self.gray_image, cmap='gray', origin='lower')
        axes[0].set_title("Original Image")
        axes[1].imshow(self.image_masked, cmap='gray', origin='lower')
        axes[1].set_title("Masked Image")
        axes[2].imshow(self.projection, cmap='gray', aspect='auto', extent=(theta_start, theta_end, 0, self.projection.shape[0]))
        axes[2].set_title("Radon Transform")
        axes[2].set_xlabel("Angle (degrees)")
        axes[2].set_ylabel("Projection Distance")
        axes[2].scatter(self.peaks[1]+self.theta_start, self.peaks[0], color='red', marker='x')
        print('b:', self.b)
        if self.b != 0:
           x = np.linspace(0, self.image_size, 100)
           y1 = (self.c1 + self.a * x) / self.b - self.a/self.b * self.x0 + self.y0
           y2 = (self.c2 + self.a * x) / self.b - self.a/self.b * self.x0 + self.y0
           ycc = (self.cc + self.a * x) / self.b - self.a/self.b * self.x0 + self.y0
           mask1 = (x > 0) & (x < self.image_size) & (y1 > 0) & (y1 < self.image_size)
           mask2 = (x > 0) & (x < self.image_size) & (y2 > 0) & (y2 < self.image_size)
           maskcc = (x > 0) & (x < self.image_size) & (ycc > 0) & (ycc < self.image_size)
           axes[1].plot(x[mask1], y1[mask1], color='red')
           axes[1].plot(x[mask2], y2[mask2], color='red')
           axes[1].plot(x[maskcc], ycc[maskcc], color='blue')
        else:
           x1 = (self.x0 + self.c1) * np.ones(self.image_size)
           x2 = (self.x0 + self.c2) * np.ones(self.image_size)
           xcc = (self.x0 + self.cc) * np.ones(self.image_size)
           y = np.linspace(0, self.image_size, self.image_size)
           axes[1].plot(x1, y, color='red')
           axes[1].plot(x2, y, color='red')
           axes[1].plot(xcc, y, color='blue')
        x_v, y_v = self.get_vertical_points() 
        axes[1].plot(x_v, y_v, 'x', color='yellow')
        plt.tight_layout()
        plt.show()
    
    def return_results(self):
        if self.theta is not None:
            average_theta = np.average(self.peaks[1]+self.theta_start)
            membrane_distance = self.get_mem_dist()
            if self.print_results:
                print('====Radon Analysis Results====')
                print('average_theta:', average_theta)
                print('membrane_distance:', membrane_distance)
        return average_theta, membrane_distance


# if __name__ == '__main__':
#     image = readmrc('J320/templates_selected.mrc', section=3, mode='gpu')
#     analyzer = RadonAnalyzer(0, image, crop_rate=0.9, thr=0.8)
#     analyzer.visualize_analyze()

