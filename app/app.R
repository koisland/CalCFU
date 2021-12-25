library(shiny)
library(shinythemes)
library(dplyr)
library(DT)
library(shinyWidgets)
library(shinycssloaders)
library(shinyjs)
library(shinylogs)

source("ui.R")

source("server.R")

shinyApp(ui, server)
