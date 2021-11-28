setwd("~/CalCFU/")

source("app/globals.R")

source("app/ui.R")

source("app/server.R")

shinyApp(ui, server)