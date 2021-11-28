
process_data <- function(df) {
  if ("Date.Time.of.Image" %in% names(df)) {
    
  } else {
    safeError("Error: Missing or Renamed Date Column")
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
        
        df <- edited_df
        
        return(df)
      } 
      else {
        # return a safeError if a parsing error occurs
        stop(safeError(e))
      }
    },
    finally = {
      return(df)
    }
  )
  
}

server <- function(input, output, session) {
  
  output$contents <- renderDataTable(
    options = list(scrollX = TRUE),
    {
      req(input$file)
      
    }
  )
}
