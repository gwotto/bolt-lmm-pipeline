import argparse
import os
import os.path
import shutil
import filecmp
import re

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

