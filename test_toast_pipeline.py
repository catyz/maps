import numpy as np

from simons_array_python import sa_pipeline_filters as sa_pf
from simons_array_python import sa_pipeline_inputs as sa_pi
from simons_array_python import sa_tod as sa_tod
from simons_array_python import sa_observation as sa_ob
from simons_array_python import sa_config
from simons_array_python import sa_sql
from simons_array_python import sa_pointing as sa_p
from simons_array_python import sa_timestream_operators as sa_op
from simons_array_python import sa_hwp 

from simons_array_python import sa_toast_operators as sa_toast
from simons_array_python import sa_toast_pipeline_tools as sa_tpt

# from toast.utils import memreport

args = sa_tpt.add_toast_args()

comm, data = sa_ob.create_data_from_IDs(
#     (22300714, 11), #Moon
#     (22300755, 10), #Good encoder

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

    (22300907, 41), 
#     (22300907, 45),
#     (22300907, 49), 
    
    toast_data=True,
)

for obs in data.obs:
#     obs.detectors = ['13.13_135.150T','13.13_155.150T','13.13_155.150B']
#     obs.detectors = ['13.13_113.90T'] #good moon detector
#     obs.detectors = ['13.13_189.90B'] #Good moon det with mapping
#     obs.detectors = ['13.12_212.90B']
    obs.detectors = sa_tpt.get_dets_by_obsID(obs)[0:3]
    obs.load_metadata()

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

operator_stack = sa_pf.OperatorComposite(
    sa_toast.OperatorToastRunMC(args, 
        sa_toast.OperatorToastApplyMapmaker(args,comm),
        sa_toast.OperatorToastAddSignal(args,comm),
        sa_toast.OperatorToastSimulateNoise(args,comm),
        sa_toast.OperatorToastScanSkySignal(args,comm), 
    ),
    
#     sa_toast.OperatorToastApplyMapmaker(args,comm, prefix='sim0'),
#     sa_toast.OperatorToastAddSignal(args,comm, prefix_out='sim0', prefix_in='sim0_noise'),
#     sa_toast.OperatorToastSimulateNoise(args,comm, prefix='sim0_noise', mc=0),
#     sa_toast.OperatorToastScanSkySignal(args,comm, prefix='sim0', mc=0), 
    
    sa_toast.OperatorToastExpandPointing(args, comm),
    sa_toast.OperatorToastDataWrapper(args, comm),

#     sa_pf.OperatorApplyCalibrationFromTOD(),
#     sa_pf.OperatorCalculateCalibrationFromDB(), 
    sa_p.ComputeBoresightQuaternions(),
    sa_pf.OperatorTelescopeDataInterpolator(prefix='corrected_'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_el_pos', 'raw_antenna_time_mjd'),
    sa_pf.OperatorScanCorrector('raw_scan_flag', 'raw_az_pos', 'raw_antenna_time_mjd'),
#     sa_op.OperatorTODNaNFiller(eval_attr_name='tes_nans'),
    sa_pf.OperatorDataInitializer(pi),
    outer_loop_on_filters=True,
)
operator_stack.exec(data) 

breakpoint()

