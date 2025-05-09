import healpy as hp
from glob import glob
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '--outdir'
)
args = parser.parse_args()


invnpps = []
nws = []
hits = []

for folder in glob('./2bcoadded_I/*'):
    print(folder)
    nws.append(hp.read_map(f'{folder}/toast_telescope_all_time_all_noise_weighted.fits', field=None, dtype=np.float64, verbose=False))
    invnpps.append(hp.read_map(f'{folder}/toast_telescope_all_time_all_invnpp.fits', field=None, dtype=np.float64, verbose=False))
    hits.append(hp.read_map(f'{folder}/toast_telescope_all_time_all_hits.fits', dtype=np.float64, verbose=False))

total_hits = np.sum(hits, axis=0)
observed_pixels = np.where(total_hits!=0)[0]

coadded_noise_weighted = np.sum(nws, axis=0)
coadded_invnpp = np.sum(invnpps, axis=0)

coadded_npp = np.zeros_like(coadded_invnpp)
coadded_npp[observed_pixels] = 1/coadded_invnpp[observed_pixels]

coadded_binned = coadded_npp* coadded_noise_weighted

hp.write_map(f'{args.outdir}/total_binned.fits', coadded_binned, overwrite=True, dtype=np.float64)
hp.write_map(f'{args.outdir}/total_hits.fits', total_hits, overwrite=True, dtype=np.float64)