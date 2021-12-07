import numpy as np
import argparse
from scipy import signal

from simons_array_python import sa_pipeline_filters as sa_pf
from simons_array_python import sa_pipeline_inputs as sa_pi
from simons_array_python import sa_tod as sa_tod
from simons_array_python import sa_observation as sa_ob
from simons_array_python import sa_config
from simons_array_python import sa_sql
from simons_array_python import sa_pointing as sa_p
from simons_array_python import sa_timestream_operators as sa_op
from simons_array_python import sa_hwp 

from simons_array_python import sa_toast_pipeline_tools as sa_tpt
from toast.utils import memreport
import toast.pipeline_tools as tpt
import toast
    

parser = argparse.ArgumentParser(
        fromfile_prefix_chars="@",
    )

sa_tpt.add_general_args(parser)
tpt.add_noise_args(parser)
tpt.add_atmosphere_args(parser)
tpt.add_sss_args(parser)
tpt.add_sky_map_args(parser)
tpt.add_pointing_args(parser)
tpt.add_mapmaker_args(parser)
tpt.add_polyfilter_args(parser)
tpt.add_groundfilter_args(parser)

args = parser.parse_args()

comm = toast.Comm()

sa_data = sa_ob.create_data_from_IDs(
#     (22300892,8) #tau A
#     (22300714, 11), #Moon
    (22300755, 10), #Good encoder

#     (22301174, 41),
#     (22301174, 45),
#     (22301174, 49),
    
#     # BAD WEATRHER RUNS
#     (22301151, 41),
#     (22301151, 45),
#     (22301151, 49),
#     # END
    
#     (22301010, 41),
#     (22301010, 45),
#     (22301010, 49),
#     (22301010, 53),
#     (22301010, 57),
    
    
    
#     (22300880, 42),
#     (22300880, 46), 
#     (22300880, 50),
#     (22300880, 54),
#     (22300880, 58),

#     (22300881, 41), 
#     (22300881, 45),
#     (22300881, 49),
#     (22300881, 53),
#     (22300881, 57),
#     (22300881, 61),

#     (22300884, 41),
#     (22300884, 45),
#     (22300884, 49),
#     (22300884, 53), #good
#     (22300884, 57),
#     (22300884, 61), #good
#     (22300884, 65), #good

#     (22300907, 41), 
#     (22300907, 45),
#     (22300907, 49), 
)

for obs in sa_data.obs:
#     obs.detectors = ['13.13_135.150T','13.13_155.150T','13.13_155.150B']
#     obs.detectors = ['13.13_113.90T'] #good moon detector
#     obs.detectors = ['13.13_189.90B'] #good moon detector with mapping
    obs.detectors = ['13.12_212.90B']
#     obs.detectors = sa_tpt.get_dets_by_obsID(sa_ob.Observation((22300880, 42)), percentile=1.0)
    obs.load_metadata()

sa_data.all_requested_dets = sa_tpt.get_all_requested_detectors(sa_data)


pi = sa_pi.InputLevel0CachedByObsID(
    all_detectors = obs.detectors,
    n_per_cache = 1,
    readout_phase = 'I',
    load_slowdaq = False,
    load_hwp = True,
    load_dets = True, 
    load_g3 = True,
    load_gcp = True,
    ignore_faulty_frame = True,
    record_frame_time = False,
    ts_rounding_error=1e+10,
)

sa_operator_stack = sa_pf.OperatorComposite(
    sa_hwp.HWPAngleCalculator(encoder_reference_angle=0),
#     sa_pf.OperatorApplyCalibrationFromTOD(),
#     sa_pf.OperatorCalculateCalibrationFromDB(),    
    sa_p.ComputeBoresightQuaternions(),
    sa_pf.OperatorTelescopeDataInterpolator(prefix='corrected_'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_el_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_az_pos', 'raw_antenna_time_mjd'),
#     sa_op.OperatorTODNaNFiller(eval_attr_name='tes_nans'),
    sa_pf.OperatorDataInitializer(pi),
)
sa_operator_stack.exec(sa_data) 

# def save_satod(sa_data):
#     tod = sa_data.obs[0].tod_list[0]
#     np.save('I', tod.read(obs.detectors[0]+'-I_0'))
#     np.save('Q', np.real(tod.read(obs.detectors[0]+'-I_4')))
#     np.save('U', np.imag(tod.read(obs.detectors[0]+'-I_4')))
    
# save_satod(sa_data)
                                                                                
# sa_tpt.apply_calibration_from_dqdb(sa_data)

# def save_tod(data):
#     np.save('demod0', data.obs[0].tod_list[0].cache['13.12_212.90B-I_0'])
#     np.save('demod4r', np.real(data.obs[0].tod_list[0].cache['13.12_212.90B-I_4']))
#     np.save('demod4i', np.imag(data.obs[0].tod_list[0].cache['13.12_212.90B-I_4']))
    
# save_tod(sa_data)


                
# sa_tpt.setup_hwp(sa_data)
            
data = sa_tpt.make_toast_data(args, comm, sa_data, sims_prefix=None)

def save_tod(data):
    tod = data.obs[0]['tod']
    np.save('toast_demod0', tod.cache[f'data_demod0_{obs.detectors[0]}'])
    np.save('toast_demod4r', tod.cache[f'data_demod4r_{obs.detectors[0]}'])
    np.save('toast_demod4i', tod.cache[f'data_demod4i_{obs.detectors[0]}'])
                               
tpt.expand_pointing(args, comm, data)

sa_hwp.HWPSignalFilter(demod_modes=[0, 4], decimate_factor=1, use_toast=True).exec(data)
# sa_tpt.rotate_QU(data)

# sa_tpt.setup_hwp(data)


# tpt.apply_polyfilter(args, comm, data, 'data')
sa_tpt.remove_suffix_from_detname(data, suffix='-I')
save_tod(data)

sa_tpt.demodulate_other(data)
tpt.apply_mapmaker(args, comm, data, 'toast_maps_demod', 'data', nnz=3, bin_only=True) 

# tpt.apply_mapmaker(args, comm, data, 'maps_demod/I', 'demod0', nnz=1, bin_only=True) 
# tpt.apply_mapmaker(args, comm, data, 'maps_demod/Q', 'demod4r', nnz=1, bin_only=True) 
# tpt.apply_mapmaker(args, comm, data, 'maps_demod/U', 'demod4i', nnz=1, bin_only=True) 




# mc_start = args.mc_start 
# nsims = args.nsims 

# tpt.expand_pointing(args, comm, data)

# from scipy import signal
# sos = signal.butter(2, 1, 'hp', fs=152.58789, output='sos')
# high_pass_filter(sos, data, total_prefix)

# def high_pass_filter(sos, data, total_prefix):            
#     print('High pass filtering')
#     for obs in data.obs:
#         for det in obs['tod'].detectors:
#             ref = obs['tod'].cache[f'{total_prefix}_{det}']
#             filtered = signal.sosfilt(sos, ref)
#             obs['tod'].cache[f'{total_prefix}_{det}'] = filtered
    
# for mc in range(mc_start, mc_start + nsims):
    
#     total_prefix = sims_prefix+str(mc)        

#     print(f'Processing {total_prefix}')
    
#     outpath = "{}/{}".format(args.outpath, mc) 

# #    tpt.simulate_atmosphere(args, comm, data, mc, total_prefix) 
    
# #    tpt.scale_atmosphere_by_frequency(args, comm, data, freq=None, mc=mc, cache_name=total_prefix) 

#     tpt.scan_sky_signal(args, comm, data, total_prefix, mc=mc)
    
# #    tpt.simulate_noise(args, comm, data, mc, total_prefix)

# #    tpt.simulate_sss(args, comm, data, mc, total_prefix)  
    
#     high_pass_filter(sos, data, total_prefix)

# #     tpt.apply_polyfilter(args, comm, data, total_prefix)
    
# #     tpt.apply_groundfilter(args, comm, data, total_prefix)

#     tpt.apply_mapmaker(args, comm, data, outpath, total_prefix, bin_only=True) 
            
    

#sa_tpt.add_suffix_to_detname(data, sims_prefix, data_prefix, suffix='-I')

# import matplotlib.pyplot as plt
# fig,ax = plt.subplots(2,1, sharex=True)

# for obs in data.obs:
#     for tod in obs['tod']:
#         signal = tod.read('13.10_112.90B-I')
#         if tod._source_prefix == data_prefix+'_':
#             ax[0].plot(signal)
#         else:
#             ax[1].plot(signal)

# fig.savefig('tods.png')

# def save_std(sa_data):
#     import pickle
#     std = {}
#     for obs in sa_data.obs:
#         obs_id = f'{obs.obs_id[0]}.{obs.obs_id[1]}'
#         std[obs_id] = {}
#         std[obs_id]['90'] = {}
#         std[obs_id]['150'] = {}
#         for tod in obs.tod_list:
#             for det in obs.detectors:
#                 if any(freq in det for freq in ['90T', '90B']):
#                     try:
#                         std[obs_id]['90'][det] = np.nanstd(tod.read(det+'-I'))
#                     except AttributeError:
#                         pass
#                 if any(freq in det for freq in ['150T', '150B']):
#                     try:
#                         std[obs_id]['150'][det] = np.nanstd(tod.read(det+'-I'))
#                     except AttributeError:
#                         pass
       
#     with open(f'std_{obs.obs_id[0]}.pkl', 'wb') as f:
#         pickle.dump(std, f)