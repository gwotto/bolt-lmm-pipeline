## Environment

The pipeline needs software and python packages installed and in the
environment path. On Imperial hpc cluster, this is achieved by two
methods:

1. Modules to load installed software into the search path. this is
   carried out by the pipeline itself. A list of required modules
   needs to be in the configuration file.
2. Conda enironment, a virtual enverinment of the user, providing
   python, python packages and other software defined by the user. For
   instructions on how to use a conda environment see
   https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/support/applications/python/
   Before using the conda environment for this pipeline for the first
   time, you need to set it up and install some python modules.

```bash
module load anaconda3/personal
anaconda-setup
conda install pandas
conda install yaml
```

## Configuration

The pipeline run is configured by the yaml-format file config.yml. An
example configuration file is located in
~/project/bolt-lmm-pipeline/bolt-lmm-pipeline/config/config.yml. Copy
this file to a convenient location and edit the configuration to your
needs. For pipeline tests, the phenotype file in
~/project/bolt-lmm-pipeline/bolt-lmm-pipeline/data/sample.phenotype.txt
can be used. At least the output directory needs to be adjusted. For
debug purposes, the pipline currently keeps many intermediate files
that need a large storage space, therefore it is recommended to choose
an output directory on the ephemeral space.


## How to run the pipeline

First load the conda environment

```bash
module load anaconda3/personal
```

1. Pipeline help message

``` bash
python3 ~/project/bolt-lmm-pipeline/bolt-lmm-pipeline/bin/initialise-pipeline.py -h

```

2. Start the pipeline

``` bash
python3 ~/project/bolt-lmm-pipeline/bolt-lmm-pipeline/bin/initialise-pipeline.py --config-file config.yml

```



## Data files

To compute association statistics at SNPs in one or more BGEN data files, specify the .bgen file(s) with --bgenFile and the corresponding .sample file with --sampleFile.

1. phenotype file
   phenotypes and covariates
2. sample file
   To compute association statistics at SNPs in one or more BGEN data files, specify the .bgen file(s) with --bgenFile and the corresponding .sample file with --sampleFile.

## Version history
  * 0.01 (2022-07-22)
	First version running on hpc cluster

## TODO
  * multiple models in parallel
  * bolt core SNPs concatenation?
  * job names in logs
  * mail upon job completion
  * resource allocation, multi-threading
  * check queues (medbio?)
  * check warning: Overlap of sample file and fam file < 50%
  
