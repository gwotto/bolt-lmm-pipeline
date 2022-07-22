import os.path
import subprocess
import yaml
import argparse
import socket
import sys
import time
import uuid
import json
import pandas as pd
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

## this is a trick to list the following arguments as required
## arguments instead of optional arguments, see
## https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments
requiredNamed = parser.add_argument_group('required named arguments')

requiredNamed.add_argument('-c', '--config-file', dest = 'config_file', required = True,
                    help = 'path to yaml configuration file',
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

# parser.add_argument('-h', '--help',
#                     ## metavar = '',
#                     help='prints out the version of the program')

args = parser.parse_args()

## run mode
run_mode = args.debug_mode

print('\nProgram: ' + program)
print('\nVersion: ' + version)

## get configurations from yaml file
yaml_file = args.config_file

yaml_fh = open(yaml_file, 'r')
cfg = yaml.safe_load(yaml_fh)

sample_file = cfg['sample-file']
gen_base = cfg['gen-base']
imp_base = cfg['imp-base']

outdir = cfg['outdir']
data_dir = cfg['data-dir']

chunksize = cfg['chunksize']

## print(sample_file)


## == modules ==

print("using environment modules")
   
# module_lib = cfg['module-lib']
module_init = cfg['module-init']
module_list = cfg['module-list']

## to get module environment working
exec(open(module_init).read())

## setting the modules library
## module('use', '-a', module_lib)
   
print('removing loaded modules....')
module('purge')

## necessary to remove all white space here
module_list = module_list.replace(" ", "")
module_list = module_list.split(',')

print("now loading modules....")

for mod in module_list:
    module('load', mod)
    
## write to log file
module('list')


## == output, log and temporary directories ==

Path(outdir).mkdir(parents=True, exist_ok=True)

log_dir = os.path.join(outdir, 'logs')
Path(log_dir).mkdir(parents=True, exist_ok=True)

plink_dir = os.path.join(outdir, 'plink')
Path(plink_dir).mkdir(parents=True, exist_ok=True)

bolt_dir = os.path.join(outdir, 'bolt')
Path(bolt_dir).mkdir(parents=True, exist_ok=True)

## don't think I need this
# snp_dir = os.path.join(outdir, 'snpinfo')
# Path(snp_dir).mkdir(parents=True, exist_ok=True)
    
tempdir = os.path.join(outdir, 'temp')
Path(tempdir).mkdir(parents=True, exist_ok=True)

plink_tempdir = os.path.join(tempdir, 'temp-plink')
Path(plink_tempdir).mkdir(parents=True, exist_ok=True)

bolt_tempdir = os.path.join(tempdir, 'temp-bolt')
Path(bolt_tempdir).mkdir(parents=True, exist_ok=True)

    
## == chromosomes, list of input files ==
if 'chr-list' in cfg:
    chr_list = cfg['chr-list']
    chr_list = chr_list.replace(" ", "")
    chr_list = chr_list.split(',')
else:
    chr_list = [*range(1, 23, 1)]
    print("no chromosome list in config file, using default set: " + str(chr_list) + '\n')
    
n_chr = len(chr_list)


## concatenating gen_base string with each chromosome name
gen_base_list = list(map(lambda chr: gen_base + str(chr), chr_list))

print('\ngen base list: ', gen_base_list)

imp_base_list = list(map(lambda chr: imp_base + str(chr), chr_list))

print('\nimp base list: ', imp_base_list)

n_gen_base = len(gen_base_list)

if n_chr != n_gen_base:
    sys.exit('number of chromosomes ' + n_chr +  ' and number of basenames ' + n_gen_base + ' do not match.')

    
## == serialising gen_base_list ==
    
tmp = uuid.uuid4().hex

json_file_name = 'data_file_' + tmp + '.json'

serial_data = {'chr-list': chr_list,
               'gen-list': gen_base_list,
              'imp-list': imp_base_list}

with open(json_file_name , "w" ) as fh:
    json.dump(serial_data, fh )

pipeline_command = 'python3 ' + os.path.join(bindir, 'run-plink.py') + ' --config-file ' + yaml_file + ' --json-file ' + json_file_name

echo_command = ["echo", "-e", "'%s'" % pipeline_command]

## maybe take the qsub variables from config file
## qsub_var = cfg['qsub-var'] 

qsub_command = ['qsub', '-S', '/bin/bash', '-o', log_dir, '-e', log_dir, '-V','-N', 'run-plink', '-J', ('1-' + str(n_gen_base)), '-l', 'select=1:ncpus=1:mem=16gb', '-l', 'walltime=01:00:00']

## because I use shell=TRUE, I can join array to string
cmd = " ".join(echo_command) + " | " + " ".join(qsub_command)

print('\nrunning run-plink.py on the pbs queue')

print('\npipeline command: ' + pipeline_command)
      
print('\nqsub command: ' + str(qsub_command))

print('\ncommand: ' + cmd)

out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
out = out.communicate()

job_id = out[0].decode('UTF-8').replace('.pbs', '').rstrip()
print("\nrunning script run-plink.py as job-id: " + job_id)

while True:
    qstat = subprocess.Popen(['qstat', job_id], shell=True, stdout=subprocess.PIPE)
    qstat = qstat.communicate()
    qstat = qstat[0].decode('ascii')
    # print(qstat)
    # print(job_id)
    # if(qstat.find(job_id)):
    #     print("task in queue")
    if(job_id in str(qstat)):
        print('task ' + job_id + ' in queue')
        time.sleep(60)
    else:
        print('task ' + job_id + ' finished')
        break


## == merging core SNP sets ==

print('\nmerging core SNP sets.')

## gen_base_list = list(map(lambda chr: gen_base + str(chr), chr_list))

coreset_list_file = os.path.join(plink_tempdir, 'basename.list')

ch = open(coreset_list_file, "w")

for gb in gen_base_list:
   gb_path = os.path.join(plink_tempdir, (gb + '.coreset'))
   ch.write(gb_path + '\n')

ch.close()

coreset_path = os.path.join(plink_dir, 'coreset')

plink_command = 'plink --merge-list ' + coreset_list_file + ' --make-bed --out ' + coreset_path

print('\nplink commamd: ' + plink_command)

plink_out = subprocess.Popen(plink_command, shell=True, stdout=subprocess.PIPE)
plink_out = plink_out.communicate()


## == creating subsets of bgen files in chunksize bins ==

## ((chr1, (chunk1, chunk2)), (chr1, (chunk3, chunk4)), (chr2, (chunk1, chunk2)))

chunk_list = []

for idx, chr in enumerate(chr_list):

    bgen_file = os.path.join(data_dir, (imp_base + str(chr) + '.bgen'))
    snps_file = os.path.join(data_dir, (imp_base + str(chr) + '.bim'))

    ## reading in bim file from ukb_imp_chr* file and putting positions in array

    f = open(snps_file, 'r')
    snp_array = f.readlines()

    ## only need snp position, i.e. 4th column
    snp_array = list(map(lambda snp: snp.split('\t')[3], snp_array))

    nsnps = len(snp_array)

    ## print('number of snps: ' + str(nsnps))

    # print(snp_array[0])
    # print(snp_array[-1])

    ## ceiling division (sign inverted floor division) to get number of chunks
    ## TODO: check if the chunk size and number of snps matters
    nchunks = -1 * (-nsnps // chunksize)

    ## print('number of chunks: ' + str(nchunks))

    ## is the position of the first snp be the right begin of the range?

    ## tuple of boundaries
    limit_lower_idx = 0
    limit_upper_idx = chunksize -1

    ## limits of chunks as an array of tuples
    limit_lower_pos = snp_array[limit_lower_idx]

    if limit_upper_idx < (nsnps - 1):
        limit_upper_pos = snp_array[limit_upper_idx]
    else:
        limit_upper_pos = snp_array[-1]

    ## array of tuples. array because it needs to be appended
    chunk_list.append((chr, (limit_lower_pos, limit_upper_pos)))

    ## while the upper limit is position is not the last snp
    while limit_upper_idx < (nsnps - 1):

        limit_lower_idx = limit_upper_idx + 1
        limit_upper_idx = limit_upper_idx + chunksize

        limit_lower_pos = snp_array[limit_lower_idx]
        
        if limit_upper_idx < (nsnps - 1):
            limit_upper_pos = snp_array[limit_upper_idx]
            chunk_list.append((chr, (limit_lower_pos, limit_upper_pos)))
        else:
            limit_upper_pos = snp_array[-1]
            chunk_list.append((chr, (limit_lower_pos, limit_upper_pos)))
        
print('\nlist of chunks:\n', chunk_list)

## serialising chunk_list
tmp = uuid.uuid4().hex

json_file_name = 'data_file_' + tmp + '.json'

serial_data = {'chr-list': chr_list,
               'chunk-list': chunk_list,
               'imp-list': imp_base_list}

with open(json_file_name , "w" ) as fh:
    json.dump(serial_data, fh )


### now step 3 for each chunk

pipeline_command_1 = 'python3 ' + os.path.join(bindir, 'run-bolt.py') + ' --config-file ' + yaml_file + ' --json-file ' + json_file_name

echo_command_1 = ["echo", "-e", "'%s'" % pipeline_command_1]

qsub_command_1 = ['qsub', '-S', '/bin/bash', '-o', log_dir, '-e', log_dir, '-V','-N', 'run-bolt', '-J', ('1-' + str(len(chunk_list))), '-l', 'select=1:ncpus=1:mem=48gb', '-l', 'walltime=12:00:00']

## because I use shell=TRUE, I can join array to string
cmd_1 = " ".join(echo_command_1) + " | " + " ".join(qsub_command_1)

print('\nrunning run-bolt.py on the pbs queue')

print('\npipeline command: ' + pipeline_command_1)
      
print('\nqsub command: ' + str(qsub_command_1))

print('\ncommand: ' + cmd_1)

out_1 = subprocess.Popen(cmd_1, shell=True, stdout=subprocess.PIPE)
out_1 = out_1.communicate()

job_id_1 = out_1[0].decode('UTF-8').replace('.pbs', '').rstrip()
print("\nrunning script run-bolt.py as job-id: " + job_id_1)

while True:
    qstat_1 = subprocess.Popen(['qstat', job_id_1], shell=True, stdout=subprocess.PIPE)
    qstat_1 = qstat_1.communicate()
    qstat_1 = qstat_1[0].decode('ascii')
    #
    print(qstat_1) ## to debug
    print(job_id_1) ## to debug
    if(qstat.find(job_id_1)): ## to debug
        print("task in queue") ## to debug
    #
    if(job_id_1 in str(qstat_1)):
        print('task ' + job_id_1 + ' in queue')
        time.sleep(300)
    else:
        print('task ' + job_id_1 + ' finished')
        print('\nqstat: ' + str(qstat_1)) ## to debug
        break


## == concatenating bolt chunks ==

bolt_tempfile_list = []

for chunk in chunk_list:

    print('chunk: ' + str(chunk))
    chr = chunk[0]
    print('chr: ' + chr)
    interval = chunk[1]

    bolt_tempfile = os.path.join(bolt_tempdir, (imp_base + str(chr) + '_' + interval[0] + '-' +
                                            interval[1] + '.model_1.bolt'))

    bolt_tempfile_list.append(bolt_tempfile)

## print(bolt_tempfile_list)

bolt_df = pd.concat((pd.read_csv(f, sep = '\t', dtype={'CHR': 'str', 'BP': 'str', 'GENPOS' : 'str', 'CHISQ_BOLT_LMM_INF' : 'str'}) for f in bolt_tempfile_list), ignore_index=True)

bolt_outfile = os.path.join(bolt_dir, 'model_1.bolt.txt')

bolt_df.to_csv(bolt_outfile, sep='\t', index=False, quoting=None)



## TODO remove temp dir



## os.remove(tempdir)

## os.remove(binary_file_name)

print('\nfinished pipeline at ' + str(datetime.now()))
