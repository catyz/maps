from simons_array_python import sa_pipeline_filters as sa_pf
from simons_array_python import sa_pipeline_inputs as sa_pi
from simons_array_python import sa_tod as sa_tod
from simons_array_python import sa_observation as sa_ob
from simons_array_python import sa_config
from simons_array_python import sa_sql
from simons_array_python import sa_pointing as sa_p
from simons_array_python import sa_timestream_operators as sa_op
from simons_array_python import sa_hwp 
from simons_array_python import sa_cuts

from simons_array_python import sa_toast_operators as sa_toast
from simons_array_python import sa_toast_pipeline_tools as sa_tpt

# from toast.utils import memreport

args = sa_tpt.add_toast_args()

data, comm = sa_ob.create_data_from_IDs(
    (22300750, 6),
#     (22300750, 10),
#     (22300750, 14),
#     (22300750, 18),
    use_toast_data=True,
)


for obs in data.obs:
#     obs.detectors = ['13.13_189.90B'] #Good moon det with mapping
#     obs.detectors = ['13.12_212.90B']
#     obs.detectors = sa_tpt.get_dets_by_obsID(obs)[0:10]
    obs.load_metadata()
#     obs.load_calibratable_list()
#     obs.detectors=obs.detectors[0:500]
    obs.detectors = ['13.13_15.90T']
#     obs.detectors = sa_op.gen_bolo_list()[0:1]
#     obs.load_det_properties()


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
#     sa_hwp.HWPAngleCalculator(encoder_reference_angle=0),
#     sa_cuts.OperatorMaskManager(
#         load_glitches=True,
#         load_nans=True,
#         load_gcp_gaps=True,
#         mask_turnarounds=True,
#         write_tes_masks=True,
#     ),
#     sa_cuts.OperatorSubscanRange(az_field_name='az_pos', prefix=''),
    sa_p.ComputeBoresightQuaternions(),
    sa_pf.OperatorTelescopeDataInterpolator(prefix='corrected_'),    
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_scan_flag', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_el_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_az_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorDataInitializer(pi),
    outer_loop_on_filters=False,
)
preprocessing.exec(data) 

sa_toast.OperatorDataWrapperToast(args, comm).exec(data)
sa_toast.OperatorToastExpandPointing(args, comm, mode='I').exec(data)

sa_toast.OperatorLoopMC(args, 
#     sa_toast.OperatorToastAddSignal(args,comm),
#     sa_toast.OperatorToastSimulateNoise(args,comm),
    sa_toast.OperatorToastScanSkySignal(args,comm, nnz=1), 
).exec(data)


sa_hwp.HWPSignalFilter(demod_modes=[0, 4], decimate_factor=1, suffix='', polarity=True).exec(data)
sa_hwp.OperatorLoadDetAngle().exec(data)
sa_hwp.OperatorRotateDetAngle(suffix='', polarity=True).exec(data)
sa_toast.OperatorQURotation(polarity=True).exec(data)
sa_toast.OperatorSetupDemodToast().exec(data)

sa_toast.OperatorLoopMC(args,  
    sa_toast.OperatorToastApplyMapmaker(args,comm),
    include_data=False, 
).exec(data)
    
    

breakpoint()

