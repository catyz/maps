from simons_array_python import sa_pipeline_filters as sa_pf
from simons_array_python import sa_pipeline_inputs as sa_pi
from simons_array_python import sa_tod as sa_tod
from simons_array_python import sa_observation as sa_ob
from simons_array_python import sa_config
from simons_array_python import sa_sql
from simons_array_python import sa_pointing as sa_p
from simons_array_python import sa_timestream_operators as sa_to
from simons_array_python import sa_hwp 
from simons_array_python import sa_cuts
from simons_array_python.calibration.planet import fit_planet as sa_planet
from simons_array_python.calibration.planet import flat_map as sa_fm


from simons_array_python import sa_toast_operators as sa_toast
from simons_array_python import sa_toast_pipeline_tools as sa_tpt

import numpy as np
# from toast.utils import memreport

args = sa_tpt.add_args()
comm = sa_tpt.get_toast_comm()
data = sa_tpt.get_toast_data(comm)

obsid_list = [
#     (22300750, 6),

    #rcw38
#     (22300935, 0),
#     (22301014, 0),
    #Tau A
#     (22301862, 10),
#     (22301851, 10),
    (22300719,8),

#     (22300625,8), #no valid stim runs
#     (22300719,8),   #has some small encoder gaps
    
#     (22300714, 11), #Moon
    
]


for obsid in obsid_list:
    obs = sa_ob.Observation(obsid)
#     obs.detectors = ['13.13_175.90B','13.13_195.90T'] #RCW38
#     obs.detectors = [[]'13.13_189.90B','13.31_93.90B'] #Good moon det with mapping
    obs.detectors = ['13.15_5.90T',
                     '13.15_71.90B',
                     '13.15_59.90T',
                     '13.15_88.90T',
                     '13.28_256.90B',
                     '13.28_255.90T']
    obs.load_metadata()
#     obs.load_calibratable_list()
#     obs.detectors=obs.detectors[0:50]
#     obs.detectors = sa_tpt.get_dets_by_obsID(obs, mapping_only=True)[100:130]
#     obs.load_det_properties()
    
    data.obs.append(obs)
    
all_requested_dets = sa_tpt.get_all_requested_dets(data)

pi = sa_pi.InputLevel0CachedByObsID(
    all_detectors = all_requested_dets,
    n_per_cache = len(all_requested_dets),
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

preprocessing = sa_pf.OperatorComposite(
#     sa_hwp.OperatorRotateDetAngle(polarity=False),
#     sa_hwp.OperatorLoadDetAngle(),
#     sa_hwp.HWPSignalFilter(demod_modes=[0, 4], decimate_factor=1, polarity=False),
#     sa_hwp.HWPAngleCalculator(encoder_reference_angle=0),

#     sa_planet.OperatorPointSourceFit(target='rcw38', scan_direction='all', name='bn'),

#     sa_planet.OperatorRmNoneDets(),
#     sa_cuts.OperatorMaskManager(
#         load_glitches=True,
#         load_nans=True,
#         load_gcp_gaps=True,
#         mask_turnarounds=True,
#         write_tes_masks=True,
#     ),
#     sa_to.OperatorTODNaNFiller(eval_attr_name='tes_nans', NaN_fraction_cutoff=0.1),
    sa_cuts.OperatorSubscanRange(az_field_name='az_pos', prefix=''),
#     sa_pf.OperatorApplyCalibrationFromDQDB(), 
    sa_p.ComputeBoresightQuaternions(),    
#     sa_p.PointingModelCorrection(),
    sa_pf.OperatorTelescopeDataInterpolator(prefix='corrected_'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_scan_flag', 'raw_antenna_time_mjd'), 
#     sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_el_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_az_rate', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_az_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorDataInitializer(pi),
#     outer_loop_on_filters=False,
)
preprocessing.exec(data) 

# np.save('boresight_no_pressure', data.obs[0].tod_list[0].read('boresight'))
# np.save('bolo_time', data.obs[0].tod_list[0].read('bolo_time'))
# np.save('az', data.obs[0].tod_list[0].read('az_pos'))
# np.save('el', data.obs[0].tod_list[0].read('el_pos'))
# breakpoint()

# sa_fm.CutFirstScan().exec(data)
sa_fm.ComputeSourceCenteredAzEl(rn=False).exec(data)
sa_fm.CenterMaskedPolyfilter(sigma=0.2, degree=3).exec(data)
# sa_fm.MakeFlatMapsFromTimestream(map_range=[-6,6,-6,6], pixel_size=0.005, savedir='', save=False).exec(data)

# coadd = sa_fm.flat_mapping.coadd([obs.tod_list[0].read(key) for key in obs.tod_list[0].cache.keys() if 'flat_map' in key])
# coadd.nan_to_zero()
# coadd.save('flat_map')

# breakpoint()

sa_toast.ToastDataWrapper(args, comm).exec(data)
sa_toast.OperatorToastExpandPointing(args, comm, mode='I').exec(data)

# sa_toast.SetupDemodPointing().exec(data)        
# sa_toast.ChangeToDemodDetList().exec(data)

sa_toast.OperatorToastApplyMapmaker(args, comm, prefix='data', nnz=1).exec(data)

    
