import healpy as hp
from glob import glob
import numpy as np
import argparse

def get_3x3(cov, pixel):
    cov_pp = np.array([
        [cov[0][pixel], cov[1][pixel], cov[2][pixel]], 
        [cov[1][pixel], cov[3][pixel], cov[4][pixel]], 
        [cov[2][pixel], cov[4][pixel], cov[5][pixel]] ], dtype=np.float64)
    
    return cov_pp

def apply_cov(cov, m):
    new_map = np.zeros_like(m)

    for pixel in observed_pixels:
        m_pp = np.array([
            [m[0][pixel]],
            [m[1][pixel]],
            [m[2][pixel]] ], dtype=np.float64
        )
        cov_pp = get_3x3(cov, pixel)
        reconstructed_pixel = cov_pp @ m_pp
        new_map[:, pixel] = reconstructed_pixel.flatten()
        
    return new_map

def invert_cov(cov):
    invcov = np.zeros_like(cov)
    
    for pixel in observed_pixels:
        matrix = get_3x3(cov, pixel)
        inv_matrix = np.linalg.pinv(matrix, rcond=1e-3)
            
        if not np.allclose(inv_matrix @ matrix, np.identity(3)):
            inv_matrix = np.zeros((3,3))

        invcov[:,pixel] = np.array([
            inv_matrix[0][0],
            inv_matrix[0][1],
            inv_matrix[0][2],
            inv_matrix[1][1],
            inv_matrix[1][2],
            inv_matrix[2][2] ], dtype=np.float64)
        
    return invcov


parser = argparse.ArgumentParser()
parser.add_argument(
    '--outdir'
)
args = parser.parse_args()


invnpps = []
nws = []
hits = []

for folder in glob('./2bcoadded/*'):
    print(folder)
    nws.append(hp.read_map(f'{folder}/data_telescope_all_time_all_noise_weighted.fits', field=None, dtype=np.float64, verbose=False))
    invnpps.append(hp.read_map(f'{folder}/data_telescope_all_time_all_invnpp.fits', field=None, dtype=np.float64, verbose=False))
    hits.append(hp.read_map(f'{folder}/data_telescope_all_time_all_hits.fits', dtype=np.float64, verbose=False))

total_hits = np.sum(hits, axis=0)
observed_pixels = np.where(total_hits!=0)[0]

coadded_noise_weighted = np.sum(nws, axis=0)
coadded_invnpp = np.sum(invnpps, axis=0)
coadded_npp = invert_cov(coadded_invnpp)
coadded_binned = apply_cov(coadded_npp, coadded_noise_weighted)

hp.write_map(f'{args.outdir}/coadded_map.fits', coadded_binned, overwrite=True, dtype=np.float64)
hp.write_map(f'{args.outdir}/total_hits.fits', total_hits, overwrite=True, dtype=np.float64)