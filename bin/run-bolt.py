import os.path
import subprocess
import yaml
import re
import argparse
import sys
import uuid
import socket
import json
from datetime import datetime
from pathlib import Path

## path to library files
bindir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(bindir, "../lib/"))

import bolt

program = os.path.basename(sys.argv[0])
version = bolt.__version__()
host = socket.gethostname()

## If not in debug mode, change to current working directory
## (directory where qsub was executed) within PBS job (workaround for
## SGE option "-cwd")

## needs python 3.8
if 'PBS_O_WORKDIR' in os.environ:
    wd = os.environ['PBS_O_WORKDIR']
    os.chdir(wd)

print('\nProgram: ' + program)
print('Version: ' + version)
print('Host: ' + host)
print('Start time: ' + str(datetime.now()))


## parse import arguments
parser = argparse.ArgumentParser(description = "initializing bolt-lmm analysis pipeline")


## list the following arguments as required arguments instead of optional arguments

requiredNamed = parser.add_argument_group('required named arguments')

requiredNamed.add_argument('-c', '--config-file', dest = 'config_file', required = True,
                    help = 'path to yaml configuration file',
                    type = lambda x: bolt.is_valid_file(parser, x))

requiredNamed.add_argument('-f', '--data-file', dest = 'data_file',
                    required = True,
                    help = 'path to json data file', metavar = 'FILE',
                    type = lambda x: bolt.is_valid_file(parser, x))

## optional arguments

parser.add_argument('-d', '--debug-mode',
                    dest = 'debug_mode',
                    action='store_true',
                    help='run in debug mode if set')

parser.add_argument('-v', '--version',
                    ## metavar = '',
                    action = 'version', version='%(prog)s ' + version,
                    help='prints out the version of the program')


args = parser.parse_args()

## run mode
debug_mode = args.debug_mode

data_file = args.data_file

## get configurations from yaml file
yaml_file = args.config_file

yaml_fh = open(yaml_file, 'r')
cfg = yaml.safe_load(yaml_fh)

## import parameters from yaml
outdir = cfg['outdir']
sample_file = cfg['sample-file']
pheno_file = cfg['pheno-file']
data_dir = cfg['data-dir'] 
imp_base = cfg['imp-base']

pheno_1 = cfg['pheno-1']
cov_1 = cfg['cov-1']
nnodes = cfg['nnodes']
ldscore_file = cfg['ldscore-file']
min_maf = cfg['min-maf']
min_info = cfg['min-info']
##

## serialised json_list
serial_list = json.load(open(data_file, 'rb'))


## == file paths ==

plink_dir = serial_list['plink-dir']
bolt_dir = serial_list['bolt-dir']
bolt_tempdir = serial_list['bolt-tempdir']
tempdir = serial_list['tempdir']
coreset_path = serial_list['coreset-path']

## creating directory, dealing with race condition
bgen_tempdir = os.path.join(tempdir, 'temp-bgen')
Path(bgen_tempdir).mkdir(parents=True, exist_ok=True)


## to debug
if debug_mode:
    pbs_array_index = 6
else:
    pbs_array_index = os.environ['PBS_ARRAY_INDEX']

base_index = int(pbs_array_index) - 1

print('pbs array index: ' + str(pbs_array_index))
print('debug mode: ' + str(debug_mode)) 
print('base index: ' + str(base_index))
    
## == generate bgenfile for range ==

chunk = serial_list['chunk-list'][base_index]

print('chunk: ' + str(chunk))

chr = chunk[0]
print('chr: ' + chr)

interval = chunk[1]

bgen_file = os.path.join(data_dir, (imp_base + str(chr) + '.bgen'))
bgen_tempfile= (os.path.join(bgen_tempdir, (imp_base + str(chr) + '_' + interval[0] + '-' +
                                            interval[1] + '.bgen')))

## bgen range needs a leading 0 for 1-digit chromosomes (WTF!)
bgen_range = str(chr).zfill(2) + ':' + interval[0] + '-' + interval[1]

bgen_c = 'bgenix -g ' + bgen_file + ' -incl-range ' + bgen_range + ' > ' + bgen_tempfile

print('\ngenerating bgen file for range ' + bgen_range + ' with command')
print('\n' + bgen_c)

os.system(bgen_c)

bgen_idx_c = 'bgenix -g ' + bgen_tempfile + ' -index'

print('\nindexing bgen file ' + bgen_tempfile)
print('\n' + bgen_idx_c)

os.system(bgen_idx_c)


## == run bolt-lmm ==

## TODO multiple models
stats_file = (os.path.join(bolt_tempdir, (imp_base + str(chr) + '_' + interval[0] + '-' +
                                            interval[1] + '.model_1.coresnps')))

stats_file_bgen_snps = (os.path.join(bolt_tempdir, (imp_base + str(chr) + '_' + interval[0] +
                                                    '-' + interval[1] + '.model_1.bolt')))

# phenotypes
pheno_col = pheno_1.split(';')[0].split(',')[0]
print(pheno_col)

# categorial covariates
ccovar = cov_1.split(';')[0].split(',')
ccovar_string = ''.join([(' --covarCol=' + x) for x in ccovar])

## print(ccovar_string)

# quantitative covariates
qcovar = cov_1.split(';')[1].split(',')
qcovar_string = ''.join([(' --qCovarCol=' + x) for x in qcovar])

## TODO multiple models
## TODO get betas
bolt_c = ('bolt ' +
          ' --bfile=' + coreset_path +
          ' --noBgenIDcheck' +
          ' --bgenFile=' + bgen_tempfile +
          ' --sampleFile=' + sample_file +
          ' --phenoFile=' + pheno_file +
          ' --phenoCol=' + pheno_col +
          ' --lmm' +
          ' --covarMaxLevels=50 ' +
          ' --h2gGuess=0.15 ' +
          ' --numThreads=' + str(nnodes) +
          ' --LDscoresFile=' + ldscore_file +
          ' --LDscoresMatchBp' +
          ' --verboseStats' +
          ' --bgenMinMAF=' + str(min_maf) +
          ' --bgenMinINFO=' + str(min_info) +
          ' --statsFile=' + stats_file +
          ' --statsFileBgenSnps=' + stats_file_bgen_snps +
          ' --covarFile=' + pheno_file +
          ccovar_string +
          qcovar_string
          )

print('\nrunning bolt-lmm with command')
print('\n' + bolt_c)

os.system(bolt_c)

print('\nfinished running bolt-lmm at: ' + str(datetime.now()))


# $(find ${BINPATH}/ -name bolt) \
#     --bfile="$OUTPATH/plink/coreset" \
#     --noBgenIDcheck \
#     --bgenFile="$BASENAME.$RANGE.bgen" \
#     --sampleFile="$(basename $SAMPLEFILE)" \
#     --phenoFile="$(basename $PHENOFILE)" \
#     --phenoCol="log_Mean_cIMT_Max" \
#     --lmm \
#     --covarMaxLevels=50 \
#     --h2gGuess=0.15 \
#     --numThreads=$NUMTHREADS \
#     --LDscoresFile="$(basename $LDSCOREFILE)" \
#     --LDscoresMatchBp \
#     --verboseStats \
#     --bgenMinMAF=0.01 \
#     --bgenMinINFO=0.1 \
#     --statsFile="$BASENAME.$RANGE.model_1.coresnps" \
#     --statsFileBgenSnps="model1_$BASENAME.$RANGE.bolt" \
# --covarFile="$(basename $PHENOFILE)" \
#     --qCovarCol="Age" \
#     --qCovarCol="PC1" \
#     --qCovarCol="PC2" \
#     --qCovarCol="PC3" \
#     --qCovarCol="PC4" \
#     --covarCol="Sex" \
#     --covarCol="Center" 

#     command = paste0('$(find ${BINPATH}/ -name bolt) \\
#     --bfile="$OUTPATH/plink/coreset" \\
#     --noBgenIDcheck \\
#     --bgenFile="$BASENAME.$RANGE.bgen" \\
#     --sampleFile="$SAMPLEFILE" \\
#     --phenoFile="$PHENOFILE" \\
#     --phenoCol="',pheno_var,'" \\
#     --lmm \\
#     --covarMaxLevels=50 \\
#     --h2gGuess=0.15 \\
#     --numThreads=$NUMTHREADS \\
#     --LDscoresFile="$LDSCOREFILE" \\
#     --LDscoresMatchBp \\
#     --verboseStats \\
#     --bgenMinMAF=',minmaf,' \\
#     --bgenMinINFO=',mininfo,' \\
#     --statsFile="$BASENAME.$RANGE.model_',modelIndex,'.coresnps" \\
#     --statsFileBgenSnps="model',modelIndex,'_$BASENAME.$RANGE.bolt" \\\n')
    
#     if (getbetas) command = paste0(command, paste0('--predBetasFile = "model', modelIndex, '_$BASENAME.$RANGE.bolt_betas" \\\n'))
#     if (length(q_cov)+length(c_cov)) command = paste0(command, '--covarFile="$(basename $PHENOFILE)" \\\n')
#     if (length(q_cov)) command = paste0(command, makeFlag("qCovarCol",q_cov))
#     if (length(c_cov)) command = paste0(command, makeFlag("covarCol",c_cov))
#     command = substr(command,1,nchar(command)-2)
#     commands = c(commands, command)
#     commands = c(commands, paste0("Rscript ",filter_file," model",modelIndex,"_$BASENAME.$RANGE.bolt ",minmaf," ",mininfo," ",snpstokeep))
#     commands = c(commands, paste0("cp model",modelIndex,"_$BASENAME.$RANGE.bolt $OUTPATH/ranges/"))
#     if (getbetas) commands = c(commands, paste0("cp model", modelIndex, "_$BASENAME.$RANGE.bolt_betas $OUTPATH/ranges_betas/"))
    
#     resultspath = paste0(outpath,"/results/")
#     filename = paste0(resultspath,"/model",modelIndex,"_.bolt")
#     if (!file.exists(filename)) {
#       dir.create(resultspath)
#       fileConn = file(filename)
#       writeLines(c(paste0("#Phenotype: ",pheno_var), 
#                    paste0("#Categorical covariates: ",c_cov), 
#                    paste0("#Quantitative covariates: ",q_cov)), fileConn)
#       close(fileConn)
#     }

#     modelIndex = modelIndex + 1 
#   }
# }




# ### CALCULATING WHERE TO SPLIT INTO CHUNKS
# NSNPS=$(wc -l < $SNPSFILE)
# NCHUNKS=$(($(($NSNPS+$CHUNKSIZE-1))/$CHUNKSIZE))
# split -n l/$NCHUNKS $SNPSFILE --filter='tail -n1' | cut -f4 > $LIMITSFILE
# sed -i "1i 0" $LIMITSFILE

# ### GENERATE AND RUN THE MASTER SCRIPT WITH THE JOB ARRAY
# # reserve N*M/4 bytes, as suggested by Bolt-LMM's author
# # running time scales with N*Me1.5
# MEMORY=72
# #WALLTIMEHOURS=$(qmgr -c "list queue med-bio" | grep resources_max.walltime | sed 's/.* \([0-9]\+\).*/\1/')
# #WALLTIMEHOURS=$(qmgr -c 'p s' | grep medbio-large | grep resources_max.walltime | awk {'print $6'})
# WALLTIMEHOURS=72
# # run the R script that generates and runs the PBS script
# source ${CMDPATH}/r_env.sh 
# Rscript $CMDPATH/step4.r $PARAMS $WALLTIMEHOURS $NNODES $MEMORY $NCHUNKS $LIMITSFILE $BGENFILE $CHR $ANALYSISID $OUTPATH


## generate bgenfile for range
## /rds/general/project/uk-biobank-2017/live/sresources_latest/bin/bgen/apps/bgenix -g  /rds/general/project/uk-biobank-2017/live/reference/sdata_latest/ukb_imp_chr1.bgen -incl-range 01:1-100000 > output.bgen

