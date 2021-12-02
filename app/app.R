setwd("~/CalCFU/app")

source("globals.R")

source("ui.R")

source("server.R")

shinyApp(ui, server)
