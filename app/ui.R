
ui <- fluidPage(
  # allow shiny js
  useShinyjs(),
  # Use css
  includeCSS("css/widgets.css"),
  navbarPage(
    theme = shinythemes::shinytheme("lumen"),
    
    title = "CalCFU",
    
    tabPanel(
      title = "3M File",
      fluidRow(
        column(4, 
               fileInput("file", "File", accept = c(".csv", ".txt")),
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
      tabsetPanel(
        tabPanel(title = "Input",
                 br(),
                 dataTableOutput("man_input") %>% withSpinner(),
                 br(),
                 actionButton("man_submit", label = "Save"),
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

