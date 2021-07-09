import healpy as hp
from glob import glob
import numpy as np

wcovs = []
maps = []

for folder in glob('./toast_maps/*'):
    print(folder)
    maps.append(hp.read_map(f'{folder}/data_telescope_all_time_all_binned.fits', dtype=np.float64, verbose=False))
    wcovs.append(hp.read_map(f'{folder}/data_telescope_all_time_all_invnpp.fits', dtype=np.float64, verbose=False))

coadded_map = np.sum(np.array(wcovs) * np.array(maps), axis=0) / np.sum(wcovs, axis=0) 

hp.write_map('coadded_map.fits', coadded_map, overwrite=True, dtype=np.float64)