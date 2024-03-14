import numpy as np
from deap import base, creator, tools, algorithms
from scipy.interpolate import griddata
from scipy.interpolate import interp1d
from scipy.spatial.distance import cdist
from scipy.special import comb
from .pickpoints import generate_data_points
from scipy.signal import correlate2d
import random


def bezier_curve(control_points, t):
    n = len(control_points) - 1
    B = np.zeros_like(control_points[0], dtype=float)
    for i, point in enumerate(control_points):
        B += comb(n, i) * (1 - t) ** (n - i) * t ** i * point
    return B

def bezier_curve_derivative(control_points, t):
    n = len(control_points) - 1
    B_prime = np.zeros(2)
    for i in range(n):
        coef = n * comb(n-1, i) * t**i * (1-t)**(n-1-i)
        B_prime += coef * (control_points[i+1] - control_points[i])
    return B_prime

def bezier_curvature(control_points, t, threshold=1e-6, high_curvature_value=1e6):
    n = len(control_points) - 1
    
    dB = np.zeros(2)
    ddB = np.zeros(2)
    
    for i in range(n):
        coef = n * comb(n-1, i) * t**i * (1-t)**(n-1-i)
        dB += coef * (control_points[i+1] - control_points[i])
        
    for i in range(n-1):
        coef = n * (n-1) * comb(n-2, i) * t**i * (1-t)**(n-2-i)
        ddB += coef * (control_points[i+2] - 2*control_points[i+1] + control_points[i])

    dx, dy = dB
    ddx, ddy = ddB
    
    magnitude_squared = dx * dx + dy * dy
    
    # 规避除数接近零的问题
    if magnitude_squared < threshold:
        return high_curvature_value

    curvature = abs(dx * ddy - dy * ddx) / magnitude_squared ** 1.5
    return curvature

def gaussian_pdf(x, mean, std):
    coefficient = 1.0 / (std * np.sqrt(2 * np.pi))
    exponential = np.exp(- (x - mean) ** 2 / (2 * std ** 2))
    return coefficient * exponential

def gaussian2(x, membrane_dist, std1, std2):
    mean1 = - membrane_dist / 2
    mean2 = membrane_dist / 2
    gaussian1 = gaussian_pdf(x, mean1, std1)
    gaussian2 = gaussian_pdf(x, mean2, std2)
    g = gaussian1 + gaussian2
    g = g / np.max(g)
    return g

def bilinear_interpolation(image, x, y):
    # Define the coordinates of the image
    x_coords = np.arange(image.shape[1])
    y_coords = np.arange(image.shape[0])
    x_mesh, y_mesh = np.meshgrid(x_coords, y_coords)   
    # Flatten the image and meshgrids
    points = np.array([x_mesh.flatten(), y_mesh.flatten()]).T
    values = image.flatten()
    # Use griddata for interpolation
    interpolated_values = griddata(points, values, (x, y), method='linear')
    return interpolated_values

def points_along_normal(control_points, t_values):
    derivatives = np.array([bezier_curve_derivative(control_points, t) for t in t_values])
    # Normalize the derivatives to get the unit tangent vectors
    tangents = derivatives / np.linalg.norm(derivatives, axis=-1)[:, np.newaxis]
    # Compute the normals from the tangents
    normals = np.zeros_like(tangents)
    normals[:, 0] = -tangents[:, 1]
    normals[:, 1] = tangents[:, 0]
    return normals

def coarsefit_evaluate_individual(ind, obj, data_points):
    return (obj.loss_function(np.array(ind), data_points),)

def evaluate_individual(ind, obj, base_image):
    # assert len(ind) == 8, f"Unexpected length of individual: {len(ind)}"
    return (obj.cross_correlation_fitness(np.array(ind).reshape(obj.degree+1, 2), base_image, obj.penalty_threshold),)

def generate_curve_within_boundaries(control_points, image_shape, step):
    t_values = []
    t = 0

    # Find the first t value within the image boundaries
    while t < 2:  # Limit to avoid infinite loop
        point = bezier_curve(control_points, t)
        if 0 <= point[0] < image_shape[0] and 0 <= point[1] < image_shape[1]:
            t_values.append(t)
            break
        t += step

    # Generate curve points moving forward
    while True:
        t += step
        point = bezier_curve(control_points, t)
        if 0 <= point[0] < image_shape[0] and 0 <= point[1] < image_shape[1]:
            t_values.append(t)
        else:
            break

    # Reset t to the initial point and generate curve points moving backward
    t = t_values[0] - step
    while t > -2:  # Limit to avoid infinite loop
        point = bezier_curve(control_points, t)
        if 0 <= point[0] < image_shape[0] and 0 <= point[1] < image_shape[1]:
            t_values.insert(0, t)  # Insert at the beginning
            t -= step
        else:
            break
    fitted_curve_points = np.array([bezier_curve(control_points, t_val) for t_val in t_values])
    return np.array(fitted_curve_points), np.array(t_values)

class Coarsefit:
    def __init__(self, image, num_points, degree, iteration):
        self.image = image
        self.num_points = num_points
        self.img_sz = image.shape[0]
        self.degree = degree
        self.iteration = iteration
    def __call__(self):
        data_points = generate_data_points(self.image, self.num_points)
        control_points = self.coarse_fitting_ga(data_points)
        # t_values = np.linspace(-2, 2, 1000)
        # fitted_curve_points = np.array([bezier_curve(control_points, t) for t in t_values])
        # mask = (fitted_curve_points[:, 0] >= 0) & (fitted_curve_points[:, 0] <= 256) & (fitted_curve_points[:, 1] >= 0) & (fitted_curve_points[:, 1] <= 256)
        # fitted_curve_points = fitted_curve_points[mask]
        # filtered_t_values = t_values[mask]
        # t_values = np.linspace(min(filtered_t_values), max(filtered_t_values), 500)
        # fitted_curve_points = np.array([bezier_curve(control_points, t) for t in t_values])
        return control_points
    def loss_function(self, control_points_flat, data_points):
        control_points = control_points_flat.reshape(self.degree+1, 2)
        t_values = np.linspace(0, 1, len(data_points))
        curve_points = np.array([bezier_curve(control_points, t) for t in t_values])
        return np.sum((curve_points - data_points) ** 2)
    def coarse_fitting_ga(self, data_points):
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", np.ndarray, fitness=creator.FitnessMin)
        toolbox = base.Toolbox()
        toolbox.register("attr_float", np.random.uniform, -self.img_sz // 2, self.img_sz // 2)
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=(self.degree+1)*2)  # 四个控制点，每个控制点有两个坐标，所以n=8
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        # toolbox.register("evaluate", lambda ind: (self.loss_function(np.array(ind), data_points),))
        toolbox.register("evaluate", coarsefit_evaluate_individual, obj=self, data_points=data_points)
        toolbox.register("mate", tools.cxBlend, alpha=0.5)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=5)
        pop = toolbox.population(n=100)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)
        algorithms.eaSimple(pop, toolbox, cxpb=0.6, mutpb=0.3, ngen=self.iteration, 
                                stats=stats, halloffame=None, verbose=True)
        # best_individual = tools.selBest(pop, 1)[0]
        # best_control_points = np.array(best_individual).reshape(4, 2)
        # print("Best Control Points:")
        # print(best_control_points)
        best_ind = tools.selBest(pop, 1)[0]
        return np.array(best_ind).reshape(self.degree+1, 2)

class GA_Refine:
    def __init__(self, image, pixel_size, penalty_threshold, dithering_range, iterations):
        self.image = image
        self.img_sz = image.shape[0]
        physical_membrane_dist = 35.0
        self.pixel_size = pixel_size
        self.penalty_threshold = penalty_threshold
        self.mem_dist = int(physical_membrane_dist / self.pixel_size)
        self.dithering_range = dithering_range
        self.iterations = iterations

    # def __call__(self, initial_control_points, image):
    #     refined_control_points = self.ga_refine_controlpoints(image, initial_control_points)
    #     t_values = np.linspace(-2, 2, 1000)
    #     fitted_curve_points = np.array([bezier_curve(refined_control_points, t) for t in t_values])
    #     mask = (fitted_curve_points[:, 0] >= 0) & (fitted_curve_points[:, 0] <= self.img_sz) & (fitted_curve_points[:, 1] >= 0) & (fitted_curve_points[:, 1] <= self.img_sz)
    #     fitted_curve_points = fitted_curve_points[mask]
    #     filtered_t_values = t_values[mask]
    #     t_values = np.linspace(min(filtered_t_values), max(filtered_t_values), 500)
    #     fitted_curve_points = np.array([bezier_curve(refined_control_points, t) for t in t_values])
    #     average_1d_lst = self.average_1d(image, fitted_curve_points, points_along_normal(refined_control_points, t_values), self.mem_dist)
    #     return refined_control_points, average_1d_lst
    def __call__(self, initial_control_points, image):
        self.degree = len(initial_control_points) - 1
        refined_control_points = self.ga_refine_controlpoints(image, initial_control_points)
        return refined_control_points

    # def average_1d(self, image, fitted_points, normals, extra_mem_dist):
    #     average_1d_lst = []
    #     for membrane_dist in range(-extra_mem_dist, extra_mem_dist+1):
    #         normals_points = fitted_points + membrane_dist * normals
    #         # Ensure the points are within the image boundaries
    #         mask = (normals_points[:, 0] >= 0) & (normals_points[:, 0] < image.shape[1]) & \
    #             (normals_points[:, 1] >= 0) & (normals_points[:, 1] < image.shape[0])
    #         normals_points = normals_points[mask]
    #         # Get interpolated gray values for the normal points
    #         interpolated_values = bilinear_interpolation(image, normals_points[:, 0], normals_points[:, 1])
    #         # convert nan to 0
    #         interpolated_values = np.nan_to_num(interpolated_values)
    #         average_1d_lst.append(np.mean(interpolated_values))
    #     return average_1d_lst
    def generate_2d_average(self, image, fitted_points, average_1d_lst, membrane_distance):
        # Create an empty image of the same size as the original
        new_image = np.zeros_like(image)

        # Create a meshgrid for the image
        y, x = np.mgrid[:image.shape[0], :image.shape[1]]
        coords = np.stack((x, y), axis=-1).reshape(-1, 2)

        # Calculate distances from each pixel to the fitted_curve_points
        distances = cdist(coords, fitted_points)
        min_distances = np.min(distances, axis=1).reshape(image.shape)
        edge_sigma = 5
        mask_within_distance = np.abs(min_distances) <= membrane_distance
        gray_value = np.exp(-(np.abs(min_distances) - membrane_distance)**2 / (2 * edge_sigma**2))
        mask_small_gray_value = gray_value < 0.001
        mask_outside_distance = ~mask_within_distance
        membrane_mask = np.zeros_like(min_distances)
        membrane_mask[mask_within_distance] = 1
        membrane_mask[mask_outside_distance & ~mask_small_gray_value] = gray_value[mask_outside_distance & ~mask_small_gray_value]

        # Use the distances to interpolate values from average_1d_lst
        f = interp1d(np.arange(-membrane_distance, membrane_distance+1), average_1d_lst, kind='linear', bounds_error=False, fill_value=0)
        new_image = f(min_distances) * membrane_mask

        return new_image, membrane_mask
    
    def cross_correlation_fitness(self, control_points, base_image, penalty_threshold):
        fitted_curve_points, filtered_t_values = generate_curve_within_boundaries(control_points, base_image.shape, 0.01)
        curvatures = [bezier_curvature(control_points, t) for t in filtered_t_values]
        curvatures_abs = [abs(curvature) for curvature in curvatures]
        control_points_out_of_bounds = [max(0, point[0] - self.img_sz, point[1] - self.img_sz, -point[0], -point[1]) for point in control_points]
        control_points_penalty = sum([10*(2**out_of_bound) for out_of_bound in control_points_out_of_bounds])
        if any(curvature > penalty_threshold for curvature in curvatures_abs):
            cur_penalty = 1e4*max(curvatures_abs)
        else:
            cur_penalty = 0
        std = 3
        new_image, membrane_mask = self.generate_2d_average(base_image, fitted_curve_points, gaussian2(np.arange(-self.mem_dist*2, self.mem_dist*2+1), self.mem_dist, std, std), self.mem_dist*2)
        cc_value = correlate2d(new_image, base_image*membrane_mask, mode='valid')
        return cc_value - cur_penalty - control_points_penalty
    def custom_mutGaussian(self, individual, mu, sigma, indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                individual[i] += random.gauss(mu, sigma)
        return individual,
    def ga_refine_controlpoints(self, base_image, initial_control_points):
        initial_control_points = np.array(initial_control_points)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        def attr_around_initial(index):
            return initial_control_points.flatten()[index] + np.random.uniform(-self.dithering_range, self.dithering_range)
        toolbox = base.Toolbox()
        toolbox.register("attr_float", attr_around_initial, index=np.arange((self.degree+1)*2))
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.attr_float)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", evaluate_individual, obj = self, base_image = base_image)
        toolbox.register("mate", tools.cxUniform, indpb=0.5)
        toolbox.register("mutate", self.custom_mutGaussian, mu=0, sigma=1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=5)
        pop = toolbox.population(n=30)
        pop.append(creator.Individual(initial_control_points.flatten()))

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        algorithms.eaSimple(pop, toolbox, cxpb=0.6, mutpb=0.4, ngen=self.iterations, 
                                stats=stats, halloffame=None, verbose=True)
        best_individual = tools.selBest(pop, 1)[0]
        best_control_points = np.array(best_individual).reshape(self.degree+1, 2)
        return best_control_points

class MemAverage:
    def __init__(self, image, control_points, pixel_size):
        self.image = image
        self.control_points = control_points
        self.pixel_size = pixel_size
        physical_membrane_dist = 35.0
        self.mem_dist = int(physical_membrane_dist / self.pixel_size)
    def generate_2d_mask(self, image, fitted_points, membrane_distance):
        y, x = np.mgrid[:image.shape[0], :image.shape[1]]
        coords = np.stack((x, y), axis=-1).reshape(-1, 2)
        distances = cdist(coords, fitted_points)
        min_distances = np.min(distances, axis=1).reshape(image.shape)
        edge_sigma = 5
        mask_within_distance = np.abs(min_distances) <= membrane_distance
        gray_value = np.exp(-(np.abs(min_distances) - membrane_distance)**2 / (2 * edge_sigma**2))
        mask_small_gray_value = gray_value < 0.001
        mask_outside_distance = ~mask_within_distance
        membrane_mask = np.zeros_like(min_distances)
        membrane_mask[mask_within_distance] = 1
        membrane_mask[mask_outside_distance & ~mask_small_gray_value] = gray_value[mask_outside_distance & ~mask_small_gray_value]
        return membrane_mask
    def average_1d(self, image, fitted_points, normals, extra_mem_dist):
        average_1d_lst = []
        for membrane_dist in range(-extra_mem_dist, extra_mem_dist+1):
            normals_points = fitted_points + membrane_dist * normals
            # Ensure the points are within the image boundaries
            mask = (normals_points[:, 0] >= 0) & (normals_points[:, 0] < image.shape[1]) & \
                (normals_points[:, 1] >= 0) & (normals_points[:, 1] < image.shape[0])
            normals_points = normals_points[mask]
            # Get interpolated gray values for the normal points
            interpolated_values = bilinear_interpolation(image, normals_points[:, 0], normals_points[:, 1])
            # convert nan to 0
            interpolated_values = np.nan_to_num(interpolated_values)
            average_1d_lst.append(np.mean(interpolated_values))
        return average_1d_lst

    def average_2d(self, image, fitted_points, normals, average_1d_lst, extra_mem_dist):
        new_image = np.zeros_like(image)
        count_image = np.zeros_like(image)
        def distribute_bilinearly(image, count_image, x, y, value):
            x1, y1 = int(x), int(y)
            x2, y2 = x1 + 1, y1 + 1
            if x2 >= image.shape[1] or y2 >= image.shape[0]:
                image[y1, x1] += value  # 如果超出范围，全部分给最近的像素
                count_image[y1, x1] += 1
                return
            # 计算双线性权重
            w11 = (x2 - x) * (y2 - y)
            w21 = (x - x1) * (y2 - y)
            w12 = (x2 - x) * (y - y1)
            w22 = (x - x1) * (y - y1)
            # 将 value 分配到四个邻近像素上
            image[y1, x1] += value * w11
            image[y1, x2] += value * w21
            image[y2, x1] += value * w12
            image[y2, x2] += value * w22
            count_image[y1, x1] += w11
            count_image[y1, x2] += w21
            count_image[y2, x1] += w12
            count_image[y2, x2] += w22
        for membrane_dist, average_1d in zip(range(-extra_mem_dist, extra_mem_dist+1), average_1d_lst):
            normals_points = fitted_points + membrane_dist * normals
            # Ensure the points are within the image boundaries
            mask = (normals_points[:, 0] >= 0) & (normals_points[:, 0] < image.shape[1]) & \
                (normals_points[:, 1] >= 0) & (normals_points[:, 1] < image.shape[0])
            normals_points = normals_points[mask]
            # Give the normal points the average gray value with interpolation
            for point in normals_points:
                distribute_bilinearly(new_image, count_image, point[0], point[1], average_1d)
            # Normalize the new_image by the count_image
        with np.errstate(divide='ignore', invalid='ignore'):
            new_image /= count_image
            new_image[np.isnan(new_image)] = 0
        return new_image.astype(image.dtype)
    def mem_average(self):
        fitted_curve_points, t_values = generate_curve_within_boundaries(self.control_points, self.image.shape, 0.001)
        mem_mask = self.generate_2d_mask(self.image, fitted_curve_points, self.mem_dist)
        extra_mem_dist = 10
        average_1d_lst = self.average_1d(self.image, fitted_curve_points, points_along_normal(self.control_points, t_values), self.mem_dist+extra_mem_dist)
        image_average_2d = self.average_2d(self.image, fitted_curve_points, points_along_normal(self.control_points, t_values), average_1d_lst, self.mem_dist+extra_mem_dist)
        return mem_mask, image_average_2d