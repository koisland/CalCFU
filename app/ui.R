

ui <- fluidPage(
  useShinyjs(),
  navbarPage(
    theme = shinythemes::shinytheme("lumen"),
    
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
                           selected = "\t"),
                
               # Input: Checkbox if file has header ----
               checkboxInput("header", "Header", TRUE)),
        
        column(4, 
               dateRangeInput("dates", "Date Range", 
                              min = "2000-01-01"))
      ), 
      
      hr(),
      
      mainPanel(
        width = 900,
        tabsetPanel(
          tabPanel(title = "Input", 
                   br(),
                   dataTableOutput("initial")),
          tabPanel(title = "Output",
                   br(),
                   dataTableOutput("results"))
        )
      )
    ),
    tabPanel(
      title = "Manual",
      numericInput("n", "Number of Plates", value = 2, min = 2, step = 2),
      tags$head(
        tags$style(HTML('#man_submit{background-color:orange}'))
        ),
      div(style="display:inline-block", 
          actionButton("man_submit", label = "Submit"), style="float:right"),
      hr(),
      tabsetPanel(
        tabPanel(title = "Input",
                 br(),
                 column(2, uiOutput("man_lbls_ui")),
                 column(2, uiOutput("man_cnts_ui")),
                 column(2, uiOutput("man_dils_ui")),
                 column(2, uiOutput("man_types_ui")),
                 column(2, uiOutput("man_num_plts_ui"))
                ),
        tabPanel(title = "Output",
                 br(),
                 dataTableOutput("man_results")
                )
 ),
       
     ),

    
    
    tabPanel(
      title = "Documentation",
      includeMarkdown("../README.md")
      
    )
  )
)

