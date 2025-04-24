# Adding a New Case Study
Each case study must have its own folder inside the ```case_studies``` directory.
The folder name will be considered the case study name.
The folder must contain the following two files:

- ```Dockerfile``` - The Dockerfile to build the case study.
- ```docker-compose.yml``` - The docker-compose file to run the case study.

## Dockerfile
The Dockerfile includes the instructions to build the case study.
The Dockerfile should be named ```Dockerfile``` and should be located in the root of the case study folder.
An example Dockerfile is shown below, look at the other case studies for more examples.

### Example Dockerfile
```dockerfile
FROM FROM python:3.12-alpine

# Install dependencies
RUN apk add --update git

# Clone the repo and checkout the specific commit
RUN git clone /<case_study_repo>.git 
WORKDIR /<case_study_repo>
RUN git checkout <commit_hash>

# Install the project dependencies
RUN pip install -r requirements.txt
```

### Guidelines
- Use a lightweight base image (e.g. python3.12-alpine for Python projects or node:18-slim for Node.js projects).
- Use the ```git checkout``` command to check out a specific commit to ensure reproducibility.

## docker-compose.yml
The docker-compose file should define the services needed to run the case study.
A minimal template is shown below:
```
services:
    <case_study_name>:
        build:
        dockerfile: Dockerfile
        image: <case_study_name>
        ports:
        - ":8080"
```
### Guidelines
- Do not specify a host port. This will allow the case study to run on any port, allowing parallel experiment execution.
- Use the ```<case_study_name>``` as the image name.
- Use the ```<case_study_name>``` as the service name.