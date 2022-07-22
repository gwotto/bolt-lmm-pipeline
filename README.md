## Environment

Needs conda environment (see https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/support/applications/python/ )


```bash
module load anaconda3/personal
pip3 install pandas
pip3 install pyyaml
```


## How to run

Python3 installed on the system

1. getting help

``` bash
python3 ~/project/bolt-lmm-pipeline/bolt-lmm-pipeline/bin/initialise-pipeline.py -h

```

2. Initializing pipeline

``` bash
python3 ~/project/bolt-lmm-pipeline/bolt-lmm-pipeline/bin/initialise-pipeline.py --config-file /rds/general/user/gotto/home/project/bolt-lmm-pipeline/bolt-lmm-pipeline/config/config.yml

```

## Output directory

large temporary output files, output preferably to ephemeral directory;

/rds/general/user/<user-id>/ephemeral/

## Accessory file

To compute association statistics at SNPs in one or more BGEN data files, specify the .bgen file(s) with --bgenFile and the corresponding .sample file with --sampleFile.

1. phenotype file
   phenotypes and covariates
2. sample file
   To compute association statistics at SNPs in one or more BGEN data files, specify the .bgen file(s) with --bgenFile and the corresponding .sample file with --sampleFile.



## bolt-lmm

### Location

/rds/general/project/uk-biobank-2017/live/sresources_latest/bin/

or in

/apps/bolt-lmm/

loaded by module

