ui <- fluidPage(
  navbarPage(
    theme = shinytheme("lumen"),
    
    title = "CalCFU",
    
    tabPanel(
      title = "3M File",
      fluidRow(
        column(4, 
               fileInput("file", "File")),
        
        column(4, 
               # Input: Select separator ----
               selectInput("sep", "Separator",
                           choices = c(Comma = ",", Semicolon = ";", Tab = "\t"),
                           selected = ","),
                
               # Input: Checkbox if file has header ----
               checkboxInput("header", "Header", TRUE)),
        
        column(4, 
               dateRangeInput("dates", "Date Range", 
                              min = "2000-01-01"))
      ), 
      
      hr(),
      
      mainPanel(
        dataTableOutput("contents"),
        width = 900
      )
    ),
    tabPanel(
      title = "Manual"
      
    )
  )
)

