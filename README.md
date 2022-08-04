## Environment

The pipeline needs software and python packages installed and in the
environment path. On Imperial hpc cluster, this is achieved by two
methods:

1. Modules to load installed software into the search path. This is
   carried out by the pipeline itself. Required modules need to be
   listed in the configuration file.
2. The Conda enironment, providing python, python packages and other
   software defined by the user. For instructions on how to use a
   conda environment see
   https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/support/applications/python/
   Before using the conda environment for this pipeline for the first
   time, you need to set it up and install some python modules.

```bash
module load anaconda3/personal
anaconda-setup
conda install pandas
conda install pyyaml
```


## Configuration

A pipeline run is configured by the yaml-format file config.yml. An
example configuration file is located in
/rds/general/project/uk-biobank-2020/live/software/bolt-lmm-pipeline/config/config.yml. Copy
this file to a convenient location and edit the configuration to your
needs. For pipeline tests, the phenotype file in
/rds/general/project/uk-biobank-2020/live/software/bolt-lmm-pipeline/data/sample.phenotype.txt
can be used. At least the output directory needs to be adjusted.

The program produces temporary files and directories, the location of
which can be set with the 'tempdir' variable. These files take a lot
of space, therefore it is recommended to choose a location on the
ephemeral directory (default is
/rds/general/user/$USER/ephemeral/). The variable temp-delete
(True/False) determines if the temporary directory gets deleted at the
end of the pipeline run.


## How to run the pipeline

1. Loading the conda environment.

```bash
module load anaconda3/personal
```

2. Starting the pipeline

``` bash
python /rds/general/project/uk-biobank-2020/live/software/bolt-lmm-pipeline/bin/initialise-pipeline.py --config-file config.yml

```

3. Pipeline help message

``` bash
python /rds/general/project/uk-biobank-2020/live/software/bolt-lmm-pipeline/bin/initialise-pipeline.py -h

```

## Data files

To compute association statistics at SNPs in one or more BGEN data
files, specify the .bgen file(s) with --bgenFile and the corresponding

1. Phenotype file, containing phenotypes and covariates, with the
   first line containing column headers and subsequent lines
   containing records, one per individual. bolt-lmm requires this to
   be a whitespace-delimited file, i.e. tab-delimited will do. The
   first two columns must be FID and IID (the PLINK identifiers of an
   individual). Any number of columns may follow. Values of -9 and NA
   are interpreted as missing data. All other values in the column
   should be numeric.
2. fam file (plink --bfile argument).
3. Sample file (bolt --sampleFile argument).
4. Genotype file in .bgen format (bolt --bgenFile argument).
5. File listing missing samples to remove (bolt --remove argument),
   e.g. if samples in fam-file are missing in
   sample-file. Tab-delimited text file, no header, FID IID must be
   first two columns. If this is the case and no remove-file is
   provided, bolt-lmm produces a file listing the samples to remove
   and exits with an error. The generated file can be used as
   remove-file in a new run.

## Version history
  * 0.01 (2022-07-28)
	First version running on hpc cluster

## TODO
  * variant annotation
  * multiple models in parallel
  * bolt core SNPs concatenation?
  * mail upon job completion
  * resource allocation, multi-threading
  * check queues (medbio?)
  * check warning: Overlap of sample file and fam file < 50%
  * dedicated conda environment?
  * accessible location

