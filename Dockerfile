# get shiny and tidyverse packaages
FROM rocker/tidyverse:latest

RUN apt-get update -qq \
  # install python and dependencies
  && apt-get -y --no-install-recommends install \
    python3.6 \
    python3-pip \
    python3-setuptools \
    python3-dev
  
## update system libraries
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean

# copy folder and set workdir 
RUN mkdir /home/CalCFU

COPY ../. /home/CalCFU

WORKDIR /home/CalCFU/app

# install python packages
RUN pip3 install -r ../requirements.txt

# install renv & restore packages
RUN Rscript -e 'install.packages("renv")'
RUN Rscript -e 'renv::consent(provided = TRUE)'
RUN Rscript -e 'renv::restore()'

# Expose port 
EXPOSE 3838

# Run app on container start
CMD ["R", "-e", "shiny::runApp('app.R', host = '0.0.0.0', port = 3838)"]