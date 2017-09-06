### Installation
Download the repo:

    git clone git://github.com/brekkjern/DNBIngest.git

Create a virtual environment for development use:

    python3 -m venv venv

Install dependencies:

    ./venv/bin/pip install -U pip
    ./venv/bin/pip install -r ./requirements.txt

Install the script:

    ./venv/bin/pip install -e .

### Usage
To run DNBIngest:

    DNBIngest <transaction file> <destination folder>