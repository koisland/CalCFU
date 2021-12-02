
process_data <- function(df, input) {
  # find date column.
  date_col_ind <-startsWith(names(df), "Date")
  date_col_name <- names(df)[date_col_ind]
  
  if (length(date_col_name) != 0) {
    dt_df <- df %>%
      # rename column to remove unwanted chrs
      rename(c("DateTime" = date_col_name[1] )) %>%
      # convert string to datetime
      summarise(across(everything()), 
                DateTime = as.Date(DateTime, "%m/%d/%Y %H:%M:%S %p")) %>%
      # filter based on provided dates in input
      filter(between(DateTime, input$dates[1], input$dates[2]))
      # # add id col
      # mutate(ID = row_number(), .before=1)
      
    return(dt_df) 
    
  } else {
    stop(safeError("Missing or Renamed Date Column"))
  }
}

read_data <- function(input) {
  # when reading semicolon separated files,
  # having a comma separator causes `read.csv` to error
  tryCatch(
    {
      df <- read.csv(input$file$datapath,
                     header = input$header,
                     sep = input$sep)
      return(df)
    },
    error = function(e) {
      # if file header left in results.
      if (e$message == "more columns than column names") {
        og_df <- read.csv(input$file$datapath,
                          header = FALSE,
                          sep = input$sep)
        
        # slice out 1st row containing header
        edited_df <- slice(og_df, 3:n())
        
        # make first row of initial df the column names
        names(edited_df) <- og_df[2,]
        
        return(edited_df)
      } 
      else {
        # return a safeError if a parsing error occurs
        stop(safeError(e))
      }
    }
  )
  
}

server <- function(input, output, session) {
  
  rv <- reactiveValues(
    man_df = NULL
  )

  # File uploaded.
  initial_data <- reactive({
    req(input$file)
    # validates dates
    validate(need(!is.na(input$dates[1]) & !is.na(input$dates[2]), 
                  "Error: Please provide both a start and an end date."))
    validate(need(input$dates[1] <= input$dates[2], 
                  "Error: Start date should be earlier than end date."))
    
    df <- read_data(input)
    return(process_data(df, input))

  })

  observeEvent(input$man_submit, {
    # Try to get data. If NULL (refreshing) then return empty string so doesn't crash.
    lbls <- map_chr(plt_names_manual(), ~ input[[paste0(.x, "_lbl")]] %||% "")
    cnts <- map_chr(plt_names_manual(), ~ input[[paste0(.x, "_cnt")]] %||% "")
    dils <- map_chr(plt_names_manual(), ~ input[[paste0(.x, "_dil")]] %||% "")
    types <- map_chr(plt_names_manual(), ~ input[[paste0(.x, "_type")]] %||% "")
    n_plts <- map_chr(plt_names_manual(), ~ input[[paste0(.x, "_n_plts")]] %||% "")
    
    # if everything is filled out. probably will change later
    if (all(!is.na(c(lbls, cnts, dils, types, n_plts)))) {
      df <- tibble(Label = lbls, 
                   Count = cnts, 
                   Dilution = dils, 
                   Type = types, 
                   NumberPlts = n_plts)
      rv$man_df <- df
    } else {
      showNotification("An input is unfilled. Try again.")
    }
    
    
  })

  output$initial <- renderDataTable(
    options = list(scrollX = TRUE),
    {
    
    final_df <- initial_data()
    return(final_df)
    })
  
  output$results <- renderDataTable(
    options = list(scrollX = TRUE),
    {
      
    }
  )
  
  # store number of plates with id plt_#
  # must be multiple of 2.
  plt_names_manual <- reactive({
    validate(need(input$n %% 2 == 0, "Error: Choose multiple of 2."))
    paste0("plt_", seq_len(input$n))
  })
  

  # manual plate ui.
  # isolate stores value outside of even after ui is updated.
  output$man_lbls_ui <- renderUI({
    lbls <- map(plt_names_manual(), ~ textInput(paste0(.x, "_lbl"), label = NULL, 
                                        value = gsub("plt_", "Plate ", .x)))
  })
  
  output$man_cnts_ui <- renderUI({
    map(plt_names_manual(), ~ numericInput(paste0(.x, "_cnt"), label = NULL, 
                                           value = isolate(.x), min = 1))
    })
  
  output$man_dils_ui <- renderUI({
    map(plt_names_manual(), ~ selectInput(paste0(.x, "_dil"),
                                         label = NULL,
                                         choices = list("-3" = -3,
                                                        "-2" = -2,
                                                        "-1" = -1,
                                                        "1:1" = 0),
                                         selected = -2))
  })
  
  output$man_types_ui <- renderUI({
    map(plt_names_manual(), ~ selectInput(paste0(.x, "_type"),
                                         label = NULL,
                                         choices = list("SPC",
                                                        "PAC",
                                                        "RAC",
                                                        "CPC",
                                                        "HSCC",
                                                        "PCC")))
  })
  
  output$man_num_plts_ui <- renderUI({
    map(plt_names_manual(), ~ numericInput(paste0(.x, "_n_plts"), label = NULL, 
                                           value = isolate(.x), min = 1))
  })
  
  output$man_results <- renderDataTable({
    rv$man_df
    
  })
}
