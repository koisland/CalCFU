FROM rocker/r-base:latest



RUN mkdir 


EXPOSE 3838

CMD ["R", "-e", "shiny:runApp("app.R")"]