
"""
Title: miSRA.py
Description: Allows the expression profiling of user provided reference sequences 
using publicly available *** small RNA-seq *** data sets. 
The preprocessed and adapter trimmed datasets are hosted at the University of Granada (miSRAdb)
and do not need to be downloaded by the user. 
The user needs to provide only reference sequences (like putative novel microRNAs) and the 
sample (SRX/ERX/DRX) or study IDs (SRP/ERP/DRP) from SRA.  
The requiered information is specified in a config file (json or key=value format)

Launch the miSRA without paramters to obtain a commented config file

Git hub: https://github.com/bioinfoUGR/miSRA/

Manual: https://github.com/bioinfoUGR/miSRA/blob/main/manual.pdf

Example config: https://github.com/bioinfoUGR/miSRA/blob/main/examples/mirna/annotated_config.json
Authors:
- Ernesto Aparicio Puerta <>
- Michael Hackenberg <hackenberg@ugr.es>


Installation:

All dependencies should be installed already in a standard python installation.
Installing through pip, will make the script runable from any working directory resolving also dependencies issues.

pip3 install miSRA


Version: 0.0.2
Date: July 12th, 2023

Dependencies:
- Python 3.7 or higher



"""
from genericpath import isfile
import requests
import sys
import argparse
import os.path
import os
import json
import time
import shutil

####################################################
#### the api urls
profiler_url = "https://arn.ugr.es/miSRA/profiler/"
check_url = "https://arn.ugr.es/miSRA/profiler/status"
dbstat_url = "https://arn.ugr.es/miSRA/profiler/dbstat"
taxonstat_url = "https://arn.ugr.es/miSRA/profiler/taxonstat"
jobid_url = "https://arn.ugr.es/miSRA/profiler/jobid"
#####################################################

## get information contained in original config file & get running status of the job
def getResult_fromJobID(jobID):
    back = {}
    back['job_id'] = jobID
    back['getjob'] = True
    r = requests.post(jobid_url, data=back, stream=True)

    print("Obtained status of job " + jobID)
    check1 = checkBackValue(r)
    ## check1 is true --> job has finished
    if check1:
        localOut = checkLocalOut(r.headers['localOut'])
        correct = postProcess(r, localOut)
        return correct
    # otherwise, pass job to checkProcess to handle it
    else:
        back['localOut'] = r.json()['localOut']
        return checkProcess(r.json(), back)


## check local output (basically important when -jobID option is used from a different place)
def checkLocalOut(localOut):
    if (os.path.exists(localOut)):
        inp = input("It seems that the output already exists. Do you want to overwrite it? (type y o n)")
        if inp.startswith("n"):
            return True

    if not os.path.exists(localOut):
        local = os.path.basename(localOut)
        print("It seems that the local output directory does not exist.")
        print("If you want to create -- ", localOut, " -- (enter 1) ")
        dec = input("If you want to create -- " + local + " -- in your current directory (enter 2) ")
        dec = dec.strip()
        if dec == "1":
            os.mkdir(localOut)
        elif dec == "2":
            if not os.path.exists(local):
                os.mkdir(local)
            localOut = local
        else:
            print("You need to enter either 1 or 2!")
            sys.exit(0)
    return localOut


# handle a job: write data once finished or error/warnings
def checkProcess(backJson, data):

    ## the script can go here with an error if the user sequences have errors (too long, to many, not in fasta format etc.)
    if "error" in backJson:
        print (backJson['backtext'])
        sys.exit(0)
        
	## if the job was handed to the scheduler, the script will go here
    if ('launched' in backJson or 'finished' in backJson):

        time.sleep(10)
        print (backJson['backtext'])  
        
    # repeat until job has finished or error was raised
        while True:
            ## check state of the job
            r = requests.post(check_url, data=backJson, stream=True)
            ## check what was returned by the api
            check1 = checkBackValue(r)
            ## if job was finished correctly - download zip and extract it
            if check1:
                correct = postProcess(r, data['localOut'])
                return correct
            time.sleep(30)

    else:
        print("Unexpected error. Probably the web-server is down. Please contact: ")
        sys.exit(0)



#  gives back False if job is still running (or dies if an error occured)
def checkBackValue(r):
    ## check if JsonResponse (still running) or HTMLResponse (finished) was obtained

    if 'json' in r.headers.get('content-type'):

        if "error" in r.json():
            print("Your job failed and produced the following error: " + r.json()["backtext"])
            print("Please let us know about the error writing to srnabench@gmail.com")
            sys.exit(0)
        elif 'nodata' in r.json():
            print(r.json()['backtext'])
            sys.exit(0)
        else:
            print(r.json()['backtext'])
        return False

    ## no JsonResponse was obtained --> job has finished
    else:
        #        print (r.headers)
        if 'finished' in r.headers:
            return True
        else:
            print("Your job failed.")
            print("Please let us know about the error writing to srnabench@gmail.com")
            sys.exit(0)


## download the results
def postProcess(r, localOut):
    """
    Takes the response object and the path to the local output
    return boolean
    """

    outfile = os.path.join(localOut, "back.zip")
    if r.status_code == 200:
        print("Retrieving result files. Will write them to ", outfile)

        handle = open(outfile, "wb")
        for chunk in r.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                handle.write(chunk)
        handle.close()
        import zipfile
        with zipfile.ZipFile(outfile, 'r') as zip_ref:
            zip_ref.extractall(localOut)
        return True
    else:
        return False


def post_profiler(data, files):
    """
    send query to server
    This function gives back a JsonResponse response json dictionary
    """
    if files == None:
        r = requests.post(profiler_url, data=data, stream=True)
        return r.json()
    else:
        postfiles = {}
        for k in files:
#            print ("file: "+files[k])
            postfiles[k] = open(files[k], "rb")

        r = requests.post(profiler_url, files=postfiles, data=data, stream=True)
        return r.json()

def msg():
    text = "miSRA --config /path/to/config.json\n" + \
           "### To see an example config: ###\n" + \
           "miSRA --ewxample-config\n" + \
           "Use only one of the optional parameters"
    return text

def parseArgs():
    parser = argparse.ArgumentParser(
        description='miSRA: a command line tool to remotely query over 90,000 miRNA-seq samples from the Sequence ' +
                    'Read Archive. You can:' +
                    ' i) receive precalculated miRNA expression values, ' +
                    'ii) profile samples with user-provided annotations,' +
                    'iii) download preprocessed sample reads',

        usage="miSRA --config /path/to/config.json\n" +
           "### To see an example config: ###\n\n" +
           "miSRA --example-config\n" +
           "Use only one of the optional parameters",

    )
    parser.add_argument('--config', '-c', type=str,
                        help='The path to a config file in json format specifying the parameters of your query. ')

    parser.add_argument('--example-config', '-e', action='store_true', # type=str,
                        help='show an example config file in json format and copy it to the current working directory' +
                        ' with the name miSRA_example_config.json. ' +
                             'For additional config examples, please refer to https://github.com/bioinfoUGR/miSRA')

    parser.add_argument('--db-stat', '-db', action='store_true',
                        help='show database statistics and dump them to miSRAdb_stat.csv')

    parser.add_argument('--taxonID', '-t', type=str,
                        help='show database content (studies and samples) for a specific species using its ' +
                             'NCBI\'s taxon ID and dump them to miSRAdb_taxonID_[TAXONID].csv')
    parser.add_argument('--jobID', '-j', type=str, help='once a job is submitted successfully, you receive a jobID. ' +
                                                        'Use this parameter to retrieve your results if the ' +
                                                        'connection is interrupted.')

    # parser.add_argument('-mode', type=str,
    #                     help='possible values: i) profile, ii) query, iii) dbstat')

    args = parser.parse_args()

    if (len(sys.argv) <= 1):
        parser.print_help()
        sys.exit(0)
    return args



def saveFile(r, outfile):
    if r.status_code == 200:
        print("Receiving result files")
        handle = open(outfile, "wb")
        for chunk in r.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                handle.write(chunk)
        handle.close()
        return True
    else:
        print("Error when trying to obtain results from server")
        return False


## get general statistics of databadse
def getdbStat():
    r = requests.post(dbstat_url, stream=True)
    #    print (r.headers)
    saveFile(r, r.headers['name'])
    print("\n ----  Database statistics dumped to " + r.headers['name'] + " in the current working directory. --- ")
    print("\n ****  Preview: ****\n")
    with open(r.headers['name']) as myfile:
        for x in range(10):
            print(myfile.readline().strip())
    sys.exit(0)


## get statistics for one species
def getTaxonStat(taxonID):
    data = {"taxonID": taxonID}
    r = requests.post(taxonstat_url, data=data, stream=True)
    saveFile(r, r.headers['name'])

    print("\n ----  Generated " + r.headers['name'] + " in the current working directory. --- ")

    sys.exit(0)


def getJson(file):
    # check if json is valid
    try:
        f = open(file, "r")
        data = json.load(f)
        return data
    except ValueError as e:
        print(e)
        print("Errors in json format!")
        sys.exit(0)


def checkScope(data):
    """
    Checks if either experiments= or studies= was given in the config file
    Checks for presence of allowed optional parameters
    """
    backdata = {}
    if not (data.get("experiments") or data.get("studies") or data.get("taxonID")):
        print(
            "You need to specify either experiments=SRX/DRX/ERX (comma separated), studies=SRP/DRP/ERP (comma separated) or taxon IDs")
        sys.exit(0)
    if data.get("experiments"):
        backdata["experiments"] = data["experiments"]
    if data.get("studies"):
        backdata["studies"] = data["studies"]
    if data.get("taxonID"):
        backdata["taxonID"] = data["taxonID"]
    if data.get("alignType"):
        backdata["alignType"] = data["alignType"]
    if data.get("mm"):
        backdata["mm"] = data["mm"]
    if data.get("max"):
        backdata["max"] = data["max"]
    if data.get("minRC"):
        backdata["minRC"] = data["minRC"]
    return backdata


# read config file '=' separated
def readConfigAlt(configFile):
    back = {}
    fh = open(configFile, "r")
    for line in fh:
        if not line.startswith("#"):
            f = line.split("=")
            if (len(f) >= 2):
                back[f[0]] = f[1].strip()

    return back


def parseConfig(file):
    """
    Parse and error check the config file in json/txt format
    Return: python dictionary with paramters
    """
    data = {}
    if file.endswith("txt"):
        print("Extention of config file is 'txt'. Will assume key/value format separated by '=' ")
        data = readConfigAlt(file)
    else:
        print("Config file was given in json format. (Any other extention than '.txt' will be interpreted as json.)")
        data = getJson(file)

    backdata = checkScope(data)
    type = ""

    ## check localOut
    if data.get("localOut"):

        backdata['localOut'] = data['localOut']
        print("Local outfile was specified")
        if os.path.exists(data['localOut']):
            print("The local output directory does exist already!")
        else:
            os.mkdir(data['localOut'])
            print("Created the directory: {}".format(data['localOut']))
    else:
        backdata['localOut'] = "pySRA_results"
        print("localOut= was not specified in config file. Will create default output pySRA_results")
        if os.path.exists(backdata['localOut']):
            print("The local output directory exists already.")
        else:
            try:
                os.mkdir(backdata['localOut'])
            except OSError:
                print("Make directory {} failed. Please check the permissions.".format( backdata['localOut']))
            else:
                print("Created the directory {}".format(backdata['localOut']))

    if data.get("mode"):
        backdata["type"] = "profiler"
        print("Detected analysis type: " + data["mode"])

        if data['mode'] == "download":
            backdata["mode"] = "download"
        ## add the separator 
            if "sep" in data:
                backdata['sep']=data["sep"]
            else:
                backdata['sep']="#"
            if "minRC" in data:
                backdata['minRC']=data["minRC"]
            if "minReadLength" in data:
                backdata['minReadLength']=data["minReadLength"]
            if "maxReadLength" in data:
                backdata['maxReadLength']=data["maxReadLength"]
                
            return (backdata, None)
        # check if mode is spike and the file is specified and does exist
        if (data["mode"] == "exact"):
            data["mode"] = "spike"
            if (data.get("spikeFile") and os.path.isfile(data["spikeFile"])):
                backdata["mode"] = "spike"
                backdata["fn1"] = os.path.basename(data["spikeFile"])
                return (backdata, {"spikeFile": data["spikeFile"]})
            else:
                print("The fasta file (spikeFile=) with localOut spike-in sequences could not be detected")
                sys.exit(0)
        if (data["mode"] == "spike"):
            if (data.get("spikeFile") and os.path.isfile(data["spikeFile"])):
                backdata["mode"] = "spike"
                backdata["fn1"] = os.path.basename(data["spikeFile"])
                return (backdata, {"spikeFile": data["spikeFile"]})
            else:
                print("The fasta file (spikeFile=) with localOut spike-in sequences could not be detected")
                sys.exit(0)
            # check if mode is libs and the file is specified and does exist
        elif (data["mode"] == "libs" or data["mode"] == "libsG"):
            if (data.get("libs") and os.path.isfile(data["libs"])):
                backdata["mode"] = data["mode"]
                backdata["fn1"] = os.path.basename(data["libs"])
                return (backdata, {"libs": data["libs"]})
            else:
                print("The fasta file (libs=) with the library sequences could not be detected")
                sys.exit(0)
                # check if mode is mirna and mature/hairpin was specified and files do exist
        elif data["mode"] == "mirna":
            if (data.get("mature") and os.path.isfile(data["mature"])):
                if (data.get("hairpin") and os.path.isfile(data["hairpin"])):
                    backdata["mode"] = "mirna"
                    backdata["fn1"] = os.path.basename(data["mature"])
                    backdata["fn2"] = os.path.basename(data["hairpin"])

                    return (backdata, {"mature": data["mature"], "hairpin": data["hairpin"]})
                else:
                    print("The fasta file (hairpin=) with the hairpin miRNA sequences could not be detected")
                    sys.exit(0)
            else:
                print("The fasta file (mature=) with the mature miRNA sequences could not be detected")
                sys.exit(0)

    else:
        type = "dbquery"
        print("start to query the DB")

def getExample():
    script_path = os.path.realpath(__file__)
    dir_name = os.path.dirname(script_path)
    # get local config

    local_config_path = os.path.join(dir_name, "example_configs", "miSRA_example_config.json")
    annotated_config_path = os.path.join(dir_name, "example_configs", "annotated_miSRA_example_config.json")
    # if os.path.exists(local_config_path):
    if os.path.exists(local_config_path):
        shutil.copyfile(local_config_path, "miSRA_example_config.json")
        # print content of annotated
        with open(annotated_config_path, 'r') as file:
            file_content = file.read()
            print(file_content)

    else:
        online_config = "https://raw.githubusercontent.com/bioinfoUGR/sRNAtoolbox/master/README.md"
        online_annotated = "https://raw.githubusercontent.com/bioinfoUGR/sRNAtoolbox/master/README.md"
        response = requests.get(online_config)
        if response.status_code == 200:
            # write to miSRA_example_config.json
            with open("miSRA_example_config.json", 'w') as file:
                file.write(response.text)
        else:
            print("Error: an example file could not be found locally or online.")
        response = requests.get(online_annotated)
        if response.status_code == 200:
            # annotated
            print(response.text)




    # if not found try to get it from github
    # if not found fail
    online_config = "https://raw.githubusercontent.com/bioinfoUGR/sRNAtoolbox/master/README.md"
    sys.exit(0)


def main():
    # parse user provided parameters
    args = parseArgs()

    ## no config file was given: either dbstat, taxonstat or get arguments over command line
    if args.config == None:
        if args.example_config:
            getExample()
        elif args.db_stat:
            getdbStat()
        elif args.taxonID:
            getTaxonStat(args.taxonID)
        elif args.jobID:
            getResult_fromJobID(args.jobID)
            sys.exit(0)
        else:
            print("\n####################################")
            print("No config file was provided (-config FILE)")
            print("####################################\n")
            sys.exit(0)
    #            (data,files) = getArguments()
    else:
        if not os.path.isfile(args.config):
            print("The specified config file is not accessable")
            sys.exit(0)

        (data, files) = parseConfig(args.config)

    if (data["type"] == "profiler"):
        # get back the response object from requests
        r = post_profiler(data, files)
        # monitor the process: wait until it finshes
        check = checkProcess(r, data)

        if check == True:
            print("Successfully received the output. Summary can be found in " + os.path.join(data['localOut'],
                                                                                              'results.html'))


if __name__ == '__main__':
    main()

