#!/bin/bash
# Slurm batch script to run refactoring

#SBATCH -p whatever 
#SBATCH -n 12
#SBATCH -t 1-00:00:00

module load miniconda3 gcc curl libarchive openssl openjdk/1.8.0_222-b10-ipodmgy
source activate $PWD/env
python devign.py
