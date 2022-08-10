import argparse
import os
import os.path
import shutil
import filecmp
import re
import subprocess
import sys
import glob

def __version__():
    version = 'v0.0.1'
    return(version)

## use argparse to parse input options
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg
        ## return open(arg, 'r')  # return an open file handle




## == monitoring the qsub processes ==

## using qstat to monitor processes running run-bolt.py on the queue
## in order to wait until all of them are finished. TODO: put this
## into a function

def monitor_qsub(job_id):
    while True:
        ## subprocess.run is synchronous, waits until it finishes and
        ## returns a CompletedProcess object

        ## would prefer to use qstat with job id but that does not seem to
        ## work (qstat_stdout empty). Does not seem to find the process

        ## qstat = subprocess.run(['qstat', job_id], capture_output=True)

        qstat = subprocess.run(['qstat'], capture_output=True)
        qstat_args = qstat.args
        qstat_stdout = qstat.stdout.decode('ascii')
        qstat_stderr = qstat.stderr.decode('ascii')
        qstat_returncode = qstat.returncode
    
        # print('\njob id:\n' + job_id) ## to debug
        # print('\nqstat stdout:\n' + qstat_stdout) ## to debug
        # print('\nqstat stderr:\n' + qstat_stderr) ## to debug
        # print('\nqstat returncode:\n' + str(qstat_returncode)) ## to debug

    
        ## checking if the job id is listed in the qstat stdoutput, if
        ## not, wait 5 min until checking again
        if(job_id in qstat_stdout):
            time.sleep(300)
        
        else:

            ## if something unexpected happened and the return code of the qstat process is not 0, try again in 5 minutes
            if(qstat_returncode != 0):
                print('\nqstat returncode:\n' + str(qstat_returncode))
                print('\nsomething unexpected')
                time.sleep(300)
            else:
                print('\nqstat stdout:\n' + qstat_stdout)
                print('\njob ' + job_id + ' has finished.') 
                break

    # ## check if qstat stderr states that the process is unknown
    # ## (i.e. finished). If so, break out of the loop. escape
    # ## special characters in pattern.
    # qstat_stderr_pattern = r'.*Unknown.*' + re.escape(job_id)
    # ## print('stderr search pattern: ' + qstat_stderr_pattern) ## to debug
        
    # if(re.match(qstat_stderr_pattern, qstat_stderr)):
    #     print('\nqstat stderr:\n' + qstat_stderr)
    #     print('task ' + job_id + ' finished')
    #     break
    ## if something unexpected happens, try again in 5 minutes
    # else:
    #     print('\nsomething unexpected')
    #     time.sleep(300)





## snp chunks, array of tuples
## ((chr1, (chunk1, chunk2)), (chr1, (chunk3, chunk4)), (chr2, (chunk1, chunk2)))

def snp_chunks(snp_array, chunksize):

    chunk_list = []
    
    nsnps = len(snp_array)

    ## print('number of snps: ' + str(nsnps))

    # print(snp_array[0])
    # print(snp_array[-1])

    ## ceiling division (sign inverted floor division) to get number of chunks
    nchunks = -1 * (-nsnps // chunksize)

    ## print('number of chunks: ' + str(nchunks))

    ## is the position of the first snp be the right begin of the range?

    ## tuple of boundaries
    limit_lower_idx = 0
    limit_upper_idx = chunksize -1

    limit_lower_pos = snp_array[limit_lower_idx]

    if limit_upper_idx < (nsnps - 1):
        limit_upper_pos = snp_array[limit_upper_idx]
    else:
        limit_upper_pos = snp_array[-1]

    ## limits of chunks as an array of tuples. array because it needs
    ## to be appended
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
