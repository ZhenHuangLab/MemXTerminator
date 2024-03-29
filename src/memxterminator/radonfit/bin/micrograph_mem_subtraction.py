import numpy as np
import cupy as cp
import mrcfile
import starfile
import matplotlib.pyplot as plt
import os
import argparse
import multiprocessing
from multiprocessing import Pool
from setproctitle import setproctitle
import time

class MicrographMembraneSubtract:
    def __init__(self, particles_selected_filename):
        self.df_star = starfile.read(particles_selected_filename)
        self.rawimage_stacks_name_lst = self.get_rawimage_stacks_name_lst()
        self.subtracted_stacks_name_lst = self.get_subtracted_stacks_name_lst()
        self.micrograph_name_lst = self.get_MicrographName_lst()
        self.raw_mg_name_lst = list(zip(self.rawimage_stacks_name_lst, self.micrograph_name_lst))
        with mrcfile.open(self.raw_mg_name_lst[0][0]) as f:
            self.rawimage_size = f.data.shape[1]
        sigma = 0.6
        x, y = cp.meshgrid(cp.linspace(-1,1,self.rawimage_size), cp.linspace(-1,1,self.rawimage_size))
        d = cp.sqrt(x*x+y*y)
        self.weights = cp.exp(-(d**2) / (2.0 * sigma**2))
        self.mask = cp.ones((self.rawimage_size, self.rawimage_size))

    def get_rawimage_stacks_name_lst(self):
        rawimage_lst = list(self.df_star['rlnImageName'].apply(lambda x: x.split('@')[1]))
        rawimage_name_lst = list(dict.fromkeys(rawimage_lst))
        return rawimage_name_lst
    def get_subtracted_stacks_name_lst(self):
        subtracted_stacks_name_lst = [rawimage_stacks_name.replace('/extract/', '/subtracted/').replace('.mrc', '_subtracted.mrc') for rawimage_stacks_name in self.rawimage_stacks_name_lst]
        return subtracted_stacks_name_lst
    def get_MicrographName_lst(self):
        micrograph_lst = list(self.df_star['rlnMicrographName'])
        micrograph_name_lst = list(dict.fromkeys(micrograph_lst))
        if len(micrograph_name_lst) != len(self.rawimage_stacks_name_lst):
            print('Error: Micrograph and rawimage stacks do not match!')
            exit()
        return micrograph_name_lst
    def get_df_temp(self, rawimage_stacks_name):
        df_temp = self.df_star[self.df_star['rlnImageName'].apply(lambda x: x.split('@')[1]) == rawimage_stacks_name]
        return df_temp
    def get_df_temp_X_Y(self, df_temp):
        rawimage_sections_lst = list(map(lambda x: int(x), list(df_temp['rlnImageName'].apply(lambda x: x.split('@')[0]))))
        CoordinateX_lst = list(df_temp['rlnCoordinateX'])
        CoordinateY_lst = list(df_temp['rlnCoordinateY'])
        zip_lst = list(zip(CoordinateX_lst, CoordinateY_lst))
        df_temp_dict_X_Y = dict(zip(rawimage_sections_lst, zip_lst))
        return df_temp_dict_X_Y
    
    def fill_nan_with_gaussian_noise(self, image):
        image_copy = image.copy()
        mean_val = cp.nanmean(image_copy)
        std_val = cp.nanstd(image_copy)
        nan_mask = cp.isnan(image_copy)
        noise = cp.random.normal(mean_val, std_val, image_copy.shape)
        image_copy[nan_mask] = noise[nan_mask]
        return image_copy
    
    def process_micrograph_mem_subtract(self, raw_mg_name):
        setproctitle('MemXTerminator-MMS')
        rawimage_stacks_name = raw_mg_name[0]
        micrograph_name = raw_mg_name[1]
        with mrcfile.open(rawimage_stacks_name.replace('/extract/', '/subtracted/').replace('.mrc', '_subtracted.mrc')) as f:
            subtracted_images_stacks = cp.asarray(f.data)
        if subtracted_images_stacks.ndim == 2:
            subtracted_images_stacks = cp.expand_dims(subtracted_images_stacks, axis=0)
        else:
            pass
        for i in range(subtracted_images_stacks.shape[0]):
            subtracted_image = subtracted_images_stacks[i]
            if cp.isnan(subtracted_image).any():
                # print(f'{rawimage_stacks_name} has {cp.isnan(subtracted_image).sum()} nan values.')
                subtracted_images_stacks[i] = self.fill_nan_with_gaussian_noise(subtracted_image)
                # print(f'Finished filling nan values with gaussian noise. Now {rawimage_stacks_name} has {cp.isnan(subtracted_images_stacks[i]).sum()} nan values.')
            else:
                pass
        # subtracted_images_stacks = cp.asarray(mrcfile.open(rawimage_stacks_name.replace('/extract/', '/subtracted/').replace('.mrc', '_subtracted.mrc')).data)
        with mrcfile.open(micrograph_name) as f:
            micrograph = cp.asarray(f.data)
        # micrograph = cp.asarray(mrcfile.open(micrograph_name).data)
        micrograph_subtracted = micrograph.copy()
        mem_mosaic_image = cp.zeros_like(micrograph)
        weight_sum_image = cp.zeros_like(micrograph)
        mem_mosaic_image_mask = cp.zeros_like(micrograph)
        subtracted_images = []
        df_rawimage_temp = self.get_df_temp(rawimage_stacks_name)
        for df_rawimage_temp_section_num, df_rawimage_temp_X_Y in self.get_df_temp_X_Y(df_rawimage_temp).items():
            subtracted_image_temp = subtracted_images_stacks[df_rawimage_temp_section_num-1]
            # subtracted_image_temp = cp.nan_to_num(subtracted_image_temp)
            X, Y = df_rawimage_temp_X_Y
            particle_be_replaced = micrograph[Y-self.rawimage_size//2:Y+self.rawimage_size//2, X-self.rawimage_size//2:X+self.rawimage_size//2]
            subtracted_image_temp = - subtracted_image_temp
            subtracted_image_temp = (subtracted_image_temp - cp.mean(subtracted_image_temp)) / cp.std(subtracted_image_temp) * cp.std(particle_be_replaced) + cp.mean(particle_be_replaced)
            # micrograph_subtracted[Y-rawimage_size//2:Y+rawimage_size//2, X-rawimage_size//2:X+rawimage_size//2] = subtracted_image_temp
            subtracted_images.append((subtracted_image_temp, (Y, X)))
        for subtracted_image, center in subtracted_images:
            # print(subtracted_image.shape, center)
            start_x = center[0] - self.rawimage_size // 2
            start_y = center[1] - self.rawimage_size // 2
            mem_mosaic_image[start_x:start_x + self.rawimage_size, start_y:start_y + self.rawimage_size] += subtracted_image * self.weights
            weight_sum_image[start_x:start_x + self.rawimage_size, start_y:start_y + self.rawimage_size] += self.weights
            mem_mosaic_image_mask[start_x:start_x+self.rawimage_size, start_y:start_y+self.rawimage_size] = self.mask
        
        epsilon = 1e-10
        weight_sum_image = cp.where(weight_sum_image == 0, epsilon, weight_sum_image)
        mem_mosaic_image /= weight_sum_image
        # mem_mosaic_image = cp.nan_to_num(mem_mosaic_image)
        micrograph_subtracted = micrograph_subtracted * (1 - mem_mosaic_image_mask) + mem_mosaic_image * mem_mosaic_image_mask
        micrograph_name_split_list = os.path.dirname(micrograph_name).split('/')
        subtracted_folder_path = os.path.join(micrograph_name_split_list[0], 'subtracted')
        os.makedirs(subtracted_folder_path, exist_ok=True)
        subtracted_membrane_name = micrograph_name.replace(f'/{micrograph_name_split_list[1]}/', '/subtracted/').replace('.mrc', '_subtracted.mrc')
        with mrcfile.new(subtracted_membrane_name, overwrite=True) as f:
            f.set_data(micrograph_subtracted.get())
        # mrcfile.new(subtracted_membrane_name, micrograph_subtracted.get(), overwrite=True)
        print(f'>>> {subtracted_membrane_name} finished')

        with open('mms_run_data.log', 'a') as f:
            f.write(micrograph_name + '\n')

        del micrograph_subtracted
        del subtracted_images_stacks
        del mem_mosaic_image
        del weight_sum_image
        del mem_mosaic_image_mask
        del subtracted_image_temp
        del subtracted_images
        del df_rawimage_temp
        del df_rawimage_temp_section_num
        del df_rawimage_temp_X_Y
        del rawimage_stacks_name
        del micrograph_name
        del subtracted_membrane_name
        del subtracted_folder_path
        del subtracted_image
        cp.cuda.Stream.null.synchronize()
        cp.cuda.MemoryPool().free_all_blocks()
    
    # def worker(self, raw_mg_name):
    #     setproctitle('MemXTerminator-MMS')
    #     self.process_micrograph_mem_subtract(raw_mg_name)

    def micrograph_mem_subtract_multiprocessing(self, num_cpus, batch_size):
        multiprocessing.set_start_method('spawn')
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        print('>>> Preparing Micrograph Membrane Subtraction dataset...')
        if not os.path.exists('mms_run_data.log'):
            with open('mms_run_data.log', 'w') as f:
                f.write('')
            print('>>> Did not find mms history. Creating a new mms_run_data.log file.')
        
        with open('mms_run_data.log', 'r') as file:
            finished_micrographs_lst = [line.rstrip('\n') for line in file]
        print(f'>>> Found {len(self.raw_mg_name_lst)} raw micrographs in total.')
        for rawimage_micrograph_name in self.raw_mg_name_lst:
            if rawimage_micrograph_name[1] in finished_micrographs_lst:
                self.raw_mg_name_lst.remove(rawimage_micrograph_name)
            else:
                pass
        print(f'>>> Found {len(finished_micrographs_lst)} finished micrographs in mms_run_data.log file. Removing them...')
        print(f'>>> {len(self.raw_mg_name_lst)-len(finished_micrographs_lst)} micrographs left to process.')
        minibatches = list(chunks(self.raw_mg_name_lst, batch_size))
        i = 1
        total_len = len(minibatches)
        for minibatch in minibatches:
            with Pool(num_cpus) as p:
                start_time = time.time()
                p.map(self.process_micrograph_mem_subtract, minibatch)
                end_time = time.time()
                print(f'>>> {i} / {total_len} minibatch finished.')
                print(f">>> {len(minibatch)} micrograph stacks took {end_time - start_time:.4f} seconds.")
                i += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Micrograph membrane subtraction')
    parser.add_argument('--particles_selected_filename', '-ps',  type=str, help='particles_selected.star')
    parser.add_argument('--cpu', type=int, default=15)
    parser.add_argument('--batch_size', type=int, default=30)
    args = parser.parse_args()
    mms = MicrographMembraneSubtract(args.particles_selected_filename)
    mms.micrograph_mem_subtract_multiprocessing(args.cpu, args.batch_size)