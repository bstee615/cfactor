#!/bin/bash
# Slurm batch script to run refactoring

#SBATCH -p whatever 
#SBATCH -n 16
#SBATCH -t 1-00:00:00
#SBATCH --mail-user=benjis@iastate.edu   # email address
#SBATCH --mail-type=FAIL
#SBATCH --output="sbatch-%j.out" # job standard output file (%j replaced by job id)

module load miniconda3 gcc curl
module load libarchive openssl openjdk/1.8.0_222-b10-ipodmgy
source activate $PWD/env
# python devign.py --mode gen
python devign.py --mode gen --remainder
