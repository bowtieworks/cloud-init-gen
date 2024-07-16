# cloud-init-generator



## Getting started

This tool aims at making the process of constructing a well-formed cloud-init file simple and error free. This is achieved by starting with a template that includes the common options that new deployments will typically need, and then asking for the remaining inputs from the user in the console.    

## Requirements

- Python 3.6 or higher
- `pip` python package manager
- `argon2`

## Setup and Usage

- Clone repository
- Ensure included shell script is executable: `chmod +x generate-hash.sh`
- Run the script: `python3 create-cloud-init.py --input cloud-init-template.yaml`

This will generate a new cloud-init file in the same directory, as well as pass the new file contents to stdout.

## Misc
Slack Taylor if you have questions

