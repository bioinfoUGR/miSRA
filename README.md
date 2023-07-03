# miSRA
a command line tool to remotely query over 90,000 miRNA-seq samples from the Sequence Read Archive

## Dependencies
miSRA requires Python >= 3.7 and the python package *requests* (automatically installed by *pip*)

## How to install
### (*optional but recommended*) Create a virtual environment and activate it

    python3 -m venv env
    source env/bin/activate

### Option 1: Install with *pip* (recommended)

    pip3 install miSRA
    # to test your installation
    miSRA --help

### Option 2: Install manually 
Alternatively, you could clone the project, install the requirements and make an alias to the script.

    git clone https://github.com/bioinfoUGR/miSRA.git
    cd miSRA
    pip3 install -r requirements.txt
    alias miSRA='python3 /absolute/path/to/miSRA.py'
    # to test your installation
    miSRA --help

If you do not want to add an alias, miSRA is a stand-alone script so it should work all the same by simply:

    python3 /absolute/path/to/miSRA.py


## Run miSRA:

    Below is an example of a typical miSRA job. Using the “-h” option will report a list of all commands available.

    miSRA --config your_config.json
An example [*config.json*](https://raw.githubusercontent.com/bioinfoUGR/miSRA/main/src/example_configs/miSRA_example_config.json) could include the following parameters (for a detailed explanation of the different query modes, [see **miSRA modes** ](#miSRA-modes)):
    
    {
        "mode":"mirna",  # There are different modes to query miSRA (mirna, libs and spike). The mode mirna performs alignments to miRNA annotations using sRNAbench
        
        # mirna mode requires 2 miRNA annotation files, one for mature miRNAs and one for hairpins
        "mature":"mature_hsa.fa", # path to mature miRNA annotations in fasta format
        "hairpin":"hairpin_hsa.fa", # path to hairpin miRNA annotations in fasta format
        
        # you can specify which samples you want to profile either by specifying comma-separated SRA study or experiment accessions
        "studies":"SRP225193", # profile all samples from this study
        # "experiments":"SRX2349199,SRX2349197,SRX546025,SRX546026", # this would include these experiments
        
        "localOut":"RNAatlas", # local folder where the results will be downloaded to
        "mm": "1", # number of mismatches (optional)
        "alignType":"v" # bowtie alignment type (optional)
    }

One could also download information about the database content. The following command will generate a file in the 
current working directory including the number of available samples and studies per species.

    miSRA --db-stat

To obtain all samples and studies available for a specific species, you can do:

    miSRA --taxonID TAXON_ID
    ## Where TAXON_ID is NCBI's taxonID. For instance, for human:
    miSRA --taxonID 9606

## miSRA modes:
There are 3 main modes to query samples in miSRA:
* **miRNA**: mature and hairpin miRNA sequences are used for profiling
* **library**: long reference sequences are used for profiling and mappings of reads to these sequences will be reported
* **spike**: short reference sequences are provided and only exact matches will be reported

### miRNA mode example run
In this example we mapped samples from the RNA Atlas project ([SRP225193](https://trace.ncbi.nlm.nih.gov/Traces/?view=study&acc=SRP225193)) to some miRNAs from MirGeneDB.\
Download files from [the miRNA mode example](https://github.com/bioinfoUGR/miSRA/tree/master/examples/mirna) into a local directory (let's call it example_mirna). Check the config file:



    cd example_mirna
    more config.json
        
        {
            "mode":"mirna",
            "studies":"SRP225193",
            "mature":"mature.fa",
            "hairpin":"hairpin.fa",
            "localOut":"RNAatlas",
            "mm": "1",
            "alignType":"v"
        }

Input references in fasta format should look like:
        
        ## mature.fa
            ...
        >Hsa-Mir-126-P2-v1_3p
        TCGTACCGTGAGTAATAATGCG
        >Hsa-Mir-21_5p
        TAGCTTATCAGACTGATGTTGACT
            ...
        
        ## hairpin.fa
            ...
        >Hsa-Mir-126-P2_pre
        CATTATTACTTTTGGTACGCGCTGTGACACTTCAAACTCGTACCGTGAGTAATAATGCG
        >Hsa-Mir-21_pre
        TAGCTTATCAGACTGATGTTGACTGTTGAATCTCATGGCAACACCAGTCGATGGGCTGTC
            ...

You can simply launch it by doing:

    miSRA --config config.json

A local directory called RNAatlas will be generated, containing the same results files as the [example](https://github.com/bioinfoUGR/miSRA/tree/master/examples/mirna/output).

### library mode example run

In this example we tried to find fragments of the [HIV genome](https://www.ncbi.nlm.nih.gov/search/all/?term=NC_001802) by mapping several samples to it. We used library mode. \
Download files from [the library mode example](https://github.com/bioinfoUGR/miSRA/tree/master/examples/libs) into a local directory (let's call it example_libs). Check the config file:

    cd example_libs
    more config.json
        
        {
        "mode":"libs",
        "experiments":"SRX2349199,SRX2349197,SRX546025,SRX546026,SRX546024,SRX1130492,[..]"
        "libs":"NC_001802.fa",
        "localOut":"vih1_lib"
        }

The libs file is simply a [fasta file containing the HIV genome assembly](https://github.com/bioinfoUGR/miSRA/tree/master/examples/libs/NC_001802.fa). 

You can simply launch it by doing:

    miSRA --config config.json

A local directory called vih1_lib will be generated, containing the same results files as the [example](https://github.com/bioinfoUGR/miSRA/tree/master/examples/libs/output).


### spike mode example run


## Manual
For further questions, please refer to the [manual]() or [post an issue](https://github.com/bioinfoUGR/miSRA/issues).





