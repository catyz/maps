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

from simons_array_python import sa_toast_pipeline_tools as sa_tpt
from toast.utils import memreport
import toast.pipeline_tools as tpt
import toast
from mpi4py import MPI

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

data_prefix = 'data'

sa_data = sa_ob.create_data_from_IDs(
        (22300880, 42),
        (22300880, 46), 
        (22300880, 50),
        (22300880, 54),
        (22300880, 58),

        (22300881, 41),
        (22300881, 45),
        (22300881, 49),
        (22300881, 53),
        (22300881, 57),
        (22300881, 61),

        (22300884, 41),
        (22300884, 45),
        (22300884, 49),
        (22300884, 53),
        (22300884, 57),
        (22300884, 61),
        (22300884, 65),

        (22300907, 41), 
        (22300907, 45),
        (22300907, 49), 
)

for obs in sa_data.obs:
    #obs.detectors = ['13.13_135.150T','13.13_155.150T','13.13_155.150B']
    obs.detectors = sa_tpt.get_dets_by_obsID(obs)[:150]
    obs.load_metadata()

sa_data.all_requested_dets = sa_tpt.gen_all_requested_detectors(sa_data)

pi = sa_pi.InputLevel0CachedByObsID(
    all_detectors = sa_data.all_requested_dets,
    #all_detectors = obs.detectors,
    n_per_cache = 150,
    load_slowdaq = False,
    load_hwp = False,
    load_dets = True, 
    load_g3 = True,
    load_gcp = True,
    ignore_faulty_frame = True,
    record_frame_time = False,
    ts_rounding_error=1e+10,
    input_name = data_prefix, #For TOAST purposes, default is 'data' anyway
)

sa_operator_stack = sa_pf.OperatorComposite(
#     sa_pf.OperatorApplyCalibrationFromDB(),
    sa_p.ComputeBoresightQuaternions(),
    sa_pf.OperatorTelescopeDataInterpolator(prefix='corrected_'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_el_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_az_pos', 'raw_antenna_time_mjd'),
#     sa_op.OperatorTODNaNFiller(eval_attr_name='tes_nans'),
    sa_pf.OperatorDataInitializer(pi),
)
sa_operator_stack.exec(sa_data) 

memreport('after data loading')
sa_tpt.apply_calibration_from_dqdb(sa_data)

data = sa_tpt.make_toast_data(args, comm, sa_data, sims_prefix=None, data_prefix=data_prefix)
sa_tpt.remove_suffix_from_detname(data, suffix='-I')

#print(f'I AM RANK {comm.comm_world.rank}')
tpt.expand_pointing(args, comm, data)
memreport('after expand pointing')

tpt.apply_polyfilter(args, comm, data, 'data')

tpt.apply_mapmaker(args, comm, data, args.outpath, 'data', bin_only=True) 


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
