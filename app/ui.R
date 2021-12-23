

ui <- fluidPage(
  # allow shiny js
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
               checkboxInput("header", "File contains a header row?", TRUE)),
        
        column(4, 
               dateRangeInput("dates", "Date Range", 
                              min = "2000-01-01"),
               dropdown(label = "Options",size = "lg",
                        awesomeCheckboxGroup(
                          inputId = "options",
                          label = "", 
                          choices = c("Allow no ID? (Group by #)", 
                                      "Allow different dilutions? (Set dilutions)"), 
                          status = "warning"),
                        
                        textOutput("options_msg"),
                        
                        # disable by default and enable based on options selected.
                        shinyjs::disabled(numericInput("opt_grp", "Number per Group", min=2, value = 2)),
                        shinyjs::disabled(selectInput("opt_dils", "Dilutions", 
                                                      choices = c("1:1 / -1", "-1 / -2", 
                                                                  "-2 / -3", "-3 / -4")))
               ))
      ), 
      
      hr(),
    
      # adjust color of options msg
      tags$head(tags$style("#options_msg{color: red; font-size: 16px;}")),
      
      mainPanel(
        width = 900,
        tabsetPanel(
          tabPanel(title = "Input", 
                   br(),
                   DTOutput("auto_input") %>% withSpinner()),
          tabPanel(title = "Output",
                   br(),
                   DTOutput("auto_results") %>% withSpinner())
        )
      )
    ),
    tabPanel(
      title = "Manual",
      tags$head(
        tags$style(HTML('#man_submit{background-color:orange}'))
        ),
      div(style="display:inline-block", 
          actionButton("man_submit", label = "Save"), style="float:right"),
      hr(),
      tabsetPanel(
        tabPanel(title = "Input",
                 br(),
                 dataTableOutput("man_input") %>% withSpinner()
                ),
        tabPanel(title = "Output",
                 br(),
                 dataTableOutput("man_results") %>% withSpinner()
                )
 ),
       
     ),

    
    
    tabPanel(
      title = "Documentation",
      includeMarkdown("../README.md")
      
    )
  )
)

