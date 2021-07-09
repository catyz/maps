import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    '--run-id'
)

parser.add_argument(
    '--run-subid'
)
parser.add_argument(
    '--outpath'
)


args = parser.parse_args()

np.save(args.outpath, 'kek')
