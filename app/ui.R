times <- strftime(seq(ISOdate(2000, 1, 1, hour = 8), by = "min", length.out = 541), format = "%I:%M:%S %p")

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
               fileInput("file", "File"),
               dropdown(label = "Options", size = "lg",
                        br(),
                        awesomeCheckboxGroup(
                          inputId = "options",
                          label = NULL, 
                          choices = c("Weighed?", 
                                      "Allow no ID? (Group by #)", 
                                      "Allow different dilutions? (Set dilutions)",
                                      "Allow different plate types? (Set plate type)"), 
                          status = "warning"),
                        
                        # disable by default and enable based on options selected.
                        shinyjs::disabled(numericInput("opt_grp_n", "Number per Group", 
                                                       min=2, value = 2)),
                        shinyjs::disabled(selectInput("opt_dils", "Dilutions", 
                                                      choices = c("1:1/-1", "-1/-2", 
                                                                  "-2/-3", "-3/-4"),
                                                      selected = "-2/-3")),
                        shinyjs::disabled(selectInput("opt_plt", "Plate Types", 
                                                      choices = c("PAC", "RAC", "PCC"),
                                                      selected = "PAC"))
               )),
        
        column(4, 
               # Input: Select separator ----
               selectInput("sep", "Separator",
                           choices = c(Comma = ",", Semicolon = ";", Tab = "\t"),
                           selected = ","),
                
               # Input: Checkbox if file has header ----
               checkboxInput("header", "File contains a header row?", TRUE)),
        
        # adjust color of options msg
        tags$head(tags$style("#options_msg{color: red; font-size: 16px;}")),
        
        column(4, 
               dateRangeInput("dates", "Date Range", 
                              min = "2000-01-01"),
               sliderTextInput(
                 inputId = "times",
                 label = "Time Range", 
                 choices = times,
                 selected = c("08:00:00 AM", "05:00:00 PM")),
               )
      ), 
      
      hr(),
      
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

