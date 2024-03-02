import numpy as np
import cupy as cp
import starfile
from ..lib._utils import *
from ..lib.mem_subtract import *
import argparse
import os
from multiprocessing import Pool
import multiprocessing
from setproctitle import setproctitle
import time

class MembraneSubtract:
    def __init__(self, particles_selected_filename, membrane_analysis_filename, bias, extra_mem_dist, scaling_factor_start, scaling_factor_end, scaling_factor_step):
        self.membrane_analysis_filename = membrane_analysis_filename
        self.df_star = starfile.read(particles_selected_filename)
        self.df_mem_analysis = starfile.read(membrane_analysis_filename)
        self.bias = bias
        self.extra_mem_dist = extra_mem_dist
        self.scaling_factor_start = scaling_factor_start
        self.scaling_factor_end = scaling_factor_end
        self.scaling_factor_step = scaling_factor_step

        self.rawimage_stacks_name_lst = self.get_rawimage_stacks_name_lst()
        self.average2ds_dict, self.average2d_name, self.averaged_mem_name, self.mem_mask_name = self.get_2daverage_averaged_mask_stack_name()
        with mrcfile.open(self.average2d_name) as mrc:
            self.average2ds = cp.asarray(mrc.data)
        with mrcfile.open(self.averaged_mem_name) as mrc:
            self.averaged_membranes = cp.asarray(mrc.data)
        with mrcfile.open(self.mem_mask_name) as mrc:
            self.membrane_masks = cp.asarray(mrc.data)
        # self.average2ds = cp.asarray(mrcfile.open(self.average2d_name).data)
        # self.averaged_membranes = cp.asarray(mrcfile.open(self.averaged_mem_name).data)
        # self.membrane_masks = cp.asarray(mrcfile.open(self.mem_mask_name).data)
        
    def get_rawimage_stacks_name_lst(self):
        rawimage_lst = list(self.df_star['rlnImageName'].apply(lambda x: x.split('@')[1]))
        rawimage_name_lst = list(dict.fromkeys(rawimage_lst))
        # rawimage_name_lst = rawimage_name_lst[1:4000]
        return rawimage_name_lst
    def get_2daverage_averaged_mask_stack_name(self):
        average2d_lst = list(map(lambda x: int(x), list(self.df_mem_analysis['rln2DAverageimageName'].apply(lambda x: x.split('@')[0]))))
        average2ds_dict = dict(zip(average2d_lst, [i for i in range(len(average2d_lst))]))
        average2d_name = list(dict.fromkeys(list(self.df_mem_analysis['rln2DAverageimageName'].apply(lambda x: x.split('@')[1]))))[0]
        averaged_mem_name = list(dict.fromkeys(list(self.df_mem_analysis['rlnAveragedMembraneName'].apply(lambda x: x.split('@')[1]))))[0]
        mem_mask_name = list(dict.fromkeys(list(self.df_mem_analysis['rlnMembraneMaskName'].apply(lambda x: x.split('@')[1]))))[0]
        return average2ds_dict, average2d_name, averaged_mem_name, mem_mask_name
    def get_center_posi_theta_memdist_kappa(self, class_number):
        index = self.average2ds_dict[class_number]
        center_posi_theta_memdist_kappa = self.df_mem_analysis['rlnCenterX'][index], self.df_mem_analysis['rlnCenterY'][index], self.df_mem_analysis['rlnAngleTheta'][index], self.df_mem_analysis['rlnMembraneDistance'][index], self.df_mem_analysis['rlnCurveKappa'][index]
        return center_posi_theta_memdist_kappa
    def get_df_temp(self, rawimage_stacks_name):
        df_temp = self.df_star[self.df_star['rlnImageName'].apply(lambda x: x.split('@')[1]) == rawimage_stacks_name]
        return df_temp
    def get_class_number_lst(self, df_temp):
        class_number_lst = list(map(lambda x: int(x), list(df_temp['rlnClassNumber'])))
        return class_number_lst
    def get_df_temp_psi_dx_dy_class(self, df_temp):
        rawimage_sections_lst = list(map(lambda x: int(x), list(df_temp['rlnImageName'].apply(lambda x: x.split('@')[0]))))
        psi_lst = list(df_temp['rlnAnglePsi'])
        dx_lst = list(df_temp['rlnOriginX'])
        dy_lst = list(df_temp['rlnOriginY'])
        rawimage_class_lst = self.get_class_number_lst(df_temp)
        zip_lst = list(zip(psi_lst, dx_lst, dy_lst, rawimage_class_lst))
        df_temp_dict_psi_dx_dy_class = dict(zip(rawimage_sections_lst, zip_lst))
        return df_temp_dict_psi_dx_dy_class
    def fill_nan_with_gaussian_noise(self, image):
        image_copy = image.copy()
        mean_val = cp.nanmean(image_copy)
        std_val = cp.nanstd(image_copy)
        nan_mask = cp.isnan(image_copy)
        noise = cp.random.normal(mean_val, std_val, image_copy.shape)
        image_copy[nan_mask] = noise[nan_mask]
        return image_copy
    def process_rawimage_stack(self, rawimage_stacks_name):
        setproctitle('MemXTerminator-radPMS')
        with mrcfile.open(rawimage_stacks_name) as mrc:
            rawimages_stacks = cp.asarray(mrc.data)
        # rawimages_stacks = cp.asarray(mrcfile.open(rawimage_stacks_name).data)
        rawimages_stacks_subtracted = rawimages_stacks.copy()
        df_rawimage_temp = self.get_df_temp(rawimage_stacks_name)
        df_rawimage_temp_dict_psi_dx_dy_class = self.get_df_temp_psi_dx_dy_class(df_rawimage_temp)
        for df_rawimage_temp_section_num, df_rawimage_temp_psi_dx_dy_class in df_rawimage_temp_dict_psi_dx_dy_class.items():
            try:
                if rawimages_stacks.ndim == 2:
                    rawimage_temp = rawimages_stacks
                else:
                    rawimage_temp = rawimages_stacks[df_rawimage_temp_section_num-1]
                psi, dx, dy, class_number = df_rawimage_temp_psi_dx_dy_class
                x0, y0, theta, memdist, kappa = self.get_center_posi_theta_memdist_kappa(class_number)
                index = self.average2ds_dict[class_number]
                average2d = self.average2ds[class_number-1]
                averaged_membrane = self.averaged_membranes[index]
                membrane_mask = self.membrane_masks[index]
                get_to_raw = Get2Raw(self.membrane_analysis_filename, average2d, averaged_membrane, rawimage_temp, membrane_mask, x0, y0, theta, memdist, kappa, psi, dx, dy)
                get_to_raw.rotate_average_to_raw()
                subtracted_membrane = get_to_raw.raw_membrane_average_subtract(self.bias, self.extra_mem_dist, self.scaling_factor_start, self.scaling_factor_end, self.scaling_factor_step)
                if cp.isnan(subtracted_membrane).any():
                    subtracted_membrane = self.fill_nan_with_gaussian_noise(subtracted_membrane)
                # print(f'{df_rawimage_temp_section_num}@{rawimage_stacks_name} membrane subtracted')
            except Exception as e:
                print(f"Error processing {df_rawimage_temp_section_num}@{rawimage_stacks_name}: {e}")
                raise e
            if rawimages_stacks_subtracted.ndim == 2:
                rawimages_stacks_subtracted = subtracted_membrane
            else:
                rawimages_stacks_subtracted[df_rawimage_temp_section_num-1] = subtracted_membrane
            del get_to_raw
            del subtracted_membrane
            del rawimage_temp
            del average2d
            del averaged_membrane
            del membrane_mask
            cp.cuda.Stream.null.synchronize()
            cp.cuda.MemoryPool().free_all_blocks()
        subtracted_folder_path = os.path.join(os.path.dirname(rawimage_stacks_name).split('/')[0], 'subtracted')
        os.makedirs(subtracted_folder_path, exist_ok=True)
        
        subtracted_stacks_name = rawimage_stacks_name.replace('/extract/', '/subtracted/').replace('.mrc', '_subtracted.mrc')
        rawimages_stacks_subtracted = rawimages_stacks_subtracted.get().astype(np.float32)
        with mrcfile.new(subtracted_stacks_name, overwrite=True) as mrc:
            mrc.set_data(rawimages_stacks_subtracted)
        # mrcfile.new(subtracted_stacks_name, rawimages_stacks_subtracted.get(), overwrite=True)
        print(f'>>> {subtracted_stacks_name} saved')
        with open('radfit_pms_run_data.log', 'a') as f:
            f.write(rawimage_stacks_name + '\n')
        del rawimages_stacks
        del rawimages_stacks_subtracted
        cp.cuda.Stream.null.synchronize()
        cp.cuda.MemoryPool().free_all_blocks()

    def membrane_subtract_multiprocess(self, num_cpus, batch_size):
        multiprocessing.set_start_method('spawn')

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        
        print('>>> Preparing Radonfit Particle Membrane Subtraction dataset...')
        if not os.path.exists('radfit_pms_run_data.log'):
            with open('radfit_pms_run_data.log', 'w') as f:
                f.write('')
            print('>>> Did not find radfit pms history. Creating a new radfit_pms_run_data.log file.')
        with open('radfit_pms_run_data.log', 'r') as file:
            finished_radfit_particles_lst = [line.rstrip('\n') for line in file]
        print(f'>>> Found {len(self.rawimage_stacks_name_lst)} raw particle stacks in total.')
        for rawimage_particle_name in self.rawimage_stacks_name_lst:
            if rawimage_particle_name in finished_radfit_particles_lst:
                self.rawimage_stacks_name_lst.remove(rawimage_particle_name)
            else:
                pass
        print(f'>>> Found {len(finished_radfit_particles_lst)} finished particle stacks in radfit_pms_run_data.log file. Removing them...')
        print(f'>>> {len(self.rawimage_stacks_name_lst)-len(finished_radfit_particles_lst)} particle stacks left to process.')

        minibatches = list(chunks(self.rawimage_stacks_name_lst, batch_size))
        i = 1
        total_len = len(minibatches)
        for minibatch in minibatches:
            with Pool(num_cpus) as p:
                start_time = time.time()
                p.map(self.process_rawimage_stack, minibatch)
                end_time = time.time()
                print(f'>>> {i} / {total_len} minibatch finished.')
                print(f">>> {len(minibatch)} particle stacks took {end_time - start_time:.4f} seconds.")
                i += 1

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--particles_selected_filename', '-ps', type=str, default='J419/particles_selected.star')
    parser.add_argument('--membrane_analysis_filename', '-ms',  type=str, default='J419/mem_analysis.star')
    parser.add_argument('--bias', '-b', type=float, default=0.05)
    parser.add_argument('--extra_mem_dist', type=float, default=20)
    parser.add_argument('--scaling_factor_start', type=float, default=0.1)
    parser.add_argument('--scaling_factor_end', type=float, default=1)
    parser.add_argument('--scaling_factor_step', type=float, default=0.01)
    parser.add_argument('--cpu', type=int, default=10)
    parser.add_argument('--batch_size', type=int, default=20)
    args = parser.parse_args()
    particles_selected_filename = args.particles_selected_filename
    membrane_analysis_filename = args.membrane_analysis_filename
    bias = args.bias
    extra_mem_dist = args.extra_mem_dist
    scaling_factor_start = args.scaling_factor_start
    scaling_factor_end = args.scaling_factor_end
    scaling_factor_step = args.scaling_factor_step
    cpus_num = args.cpu
    batch_size = args.batch_size
    membrane_subtract = MembraneSubtract(particles_selected_filename, membrane_analysis_filename, bias, extra_mem_dist, scaling_factor_start, scaling_factor_end, scaling_factor_step)
    membrane_subtract.membrane_subtract_multiprocess(num_cpus=cpus_num, batch_size=batch_size)