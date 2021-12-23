library(purrr)
library(shiny)
library(shinythemes)
library(dplyr)
library(DT)
library(rvest)
library(shinyWidgets)
library(shinycssloaders)
library(shinyjs)

source("ui.R")

source("server.R")

shinyApp(ui, server)
