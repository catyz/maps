from mpi4py import MPI
import subprocess
comm = MPI.COMM_WORLD

if comm.rank == 0:
    total_obs_list = (
        (22300880, 42),
#         (22300880, 46), 
#         (22300880, 50),
#         (22300880, 54),
#         (22300880, 58),

#         (22300881, 41),
#         (22300881, 45),
#         (22300881, 49),
#         (22300881, 53),
#         (22300881, 57),
#         (22300881, 61),

#         (22300884, 41),
#         (22300884, 45),
#         (22300884, 49),
#         (22300884, 53),
#         (22300884, 57),
#         (22300884, 61),
#         (22300884, 65),

#         (22300907, 41), 
#         (22300907, 45),
#         (22300907, 49),       
    )
    assert len(total_obs_list) == comm.size
else:
    total_obs_list = None
    
obs_id = comm.scatter(total_obs_list, root=0)
    
run_id = obs_id[0]
run_subid = obs_id[1]

outpath = f'/global/cscratch1/sd/yzh/maps/toast_maps/{run_id}_{run_subid}'

subprocess.run(f"python pipeline.py @pars --run-id {run_id} --run-subid {run_subid} --outpath {outpath}", shell=True)




