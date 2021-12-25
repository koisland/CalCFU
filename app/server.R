# track_usage(storage_mode = store_json(path = "/root/logs/"))

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
      
      if (!isTRUE(input$header)) {
        # if no header, add colnames. can't do if header, cause might erase data.
        column_names <- readLines("../data/3M_colnames.txt")
        
        # check if column names same length as df.
        if (length(column_names) == length(names(df))) {
          names(df) <- column_names
        } else {
          stop(safeError("One or multiple columns are missing."))
        }
      }
      
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
    res_man_df = NULL,
    res_auto_df = NULL,
    opt_msg = "",
    opt_dils = "-2 / -3",
    opt_grp = "id",
    opt_grp_n = "2"
  )
  
  # Initialize df w/inputs for manual entry.
  init_man_df <- function (num) {
    man_df = data.frame(Label = as.character(paste("Plate", seq(num))), 
                        Count = as.character(rep(0, num)), 
                        Dilution = as.character(rep(-1, num)),
                        Type = as.character(rep("PAC", num)),
                        NumberPlates = as.character(rep(1, num)),
                        stringsAsFactors=FALSE)
    
    # Add inputs. Can't access them through input[[?_#]]?
    # Pretty slow. Also will reset values on setting new n. Find way to use isolate() correctly.
    for (n in 1:num){
      man_df$Label[n] <- as.character(textInput(paste0("lbl_", n), 
                                                label = NULL, 
                                                width = "100px"))
      
      man_df$Count[n] <- as.character(numericInput(paste0("cnt_", n),
                                                   label = NULL,
                                                   width = "100px",
                                                   value = 1,
                                                   min = 1))
      man_df$Dilution[n] <- as.character(selectInput(paste0("dil_", n), 
                                                     label = NULL, 
                                                     choices = list("-3" = -3, "-2" = -2, "-1" = -1, "1:1" = 0), 
                                                     selected = -2, 
                                                     width = "100px"))
      man_df$Type[n] <- as.character(selectInput(paste0("type_", n),
                                                 label = NULL, 
                                                 choices = list("SPC", "PAC", "RAC", "CPC", "HSCC", "PCC"),
                                                 selected = "PAC",
                                                 width = "100px"))
      
      man_df$NumberPlates[n] <- as.character(numericInput(paste0("num_plts", n),
                                                          label = NULL,
                                                          width = "100px",
                                                          value = 1,
                                                          min = 1))
    }
    return(man_df)
  }
  
  # File uploaded.
  upl_data <- reactive({
    # validates dates
    validate(need(!is.na(input$dates[1]) & !is.na(input$dates[2]), 
                  "Error: Please provide both a start and an end date."))
    validate(need(input$dates[1] <= input$dates[2], 
                  "Error: Start date should be earlier than end date."))
    
    df <- read_data(input) %>% process_data(input)
    return(df)

  })
  
  # When manual submit, get ids of each widget and extract values into df
  observeEvent(input$man_submit, {
    
    col_names <- c("Label", "Count", "Dilution", "Type", "NumberPlates")
    ids <- c("lbl_", "cnt_", "dil_", "type_", "num_plts")
    
    # create matrix of ids using outer product and number of plate groups.
    lbl_mat <- t(outer(ids, seq(10), paste0))
    res_mat <- apply(lbl_mat, c(1,2), function(x) input[[x]])
    colnames(res_mat) <- col_names

    res_man_df <- data.frame(res_mat)
    
    # store res df as reactive value to access
    rv$res_man_df <- res_man_df
  })
  
  # dt proxy to edit a cell
  proxy_auto_input <- dataTableProxy("auto_input")
  
  # on cell edit, replace value, and replace datatable.
  observeEvent(input$auto_input_cell_edit, {
    info <- input$auto_input_cell_edit
    
    # replace value in reactive values and coerce to whatever dtype in that pos
    rv$res_auto_df[info$row, info$col] <- coerceValue(info$value, rv$res_auto_df[info$row, info$col])
    
    # replace DT and keep state of table 
    replaceData(proxy_auto_input, rv$res_auto_df, resetPaging = FALSE)
  })
  
  # set options msgs and enable or disable inputs.
  observeEvent(input$options, {
    if (length(input$options) == 2) {
      rv$opt_msg <- "Set both grouping and dilutions below."
      rv$opt_grp <- "num"
      enable("opt_grp_n")
      enable("opt_dils")
    } else if ("Allow no ID? (Group by #)" %in% input$options) {
      rv$opt_msg <- "Set number per grouping below."
      rv$opt_grp <- "num"
      enable("opt_grp_n")
      disable("opt_dils")
    } else if ("Allow different dilutions? (Set dilutions)" %in% input$options) {
      rv$opt_msg <- "Set dilution below."
      enable("opt_dils")
      disable("opt_grp_n")
    } else {
      rv$opt_msg <- ""
      rv$opt_grp <- "id"
      disable("opt_dils")
      disable("opt_grp_n")
    }
    # Will not trigger event for checkbox if NULL ignored.
  }, ignoreNULL = FALSE)
  
  
  # Store options.
  observeEvent(input$opt_dils, {
    rv$opt_dils <- input$opt_dils
  })
  
  observeEvent(input$opt_grp_n, {
    rv$opt_grp_n <- input$opt_grp_n
  })
  
  # Display options msg.
  output$options_msg <- renderText({
    return(rv$opt_msg)
  })
  
  output$auto_input <- renderDT(
    options = list(scrollX = TRUE),
    selection = "single",
    editable = TRUE, 
    {
      req(input$file)
      df = upl_data()
      # save df to reactive values
      rv$res_auto_df <- df
      return(df)
    }
  )
  
  output$auto_results <- renderDataTable(
    options = list(scrollX = TRUE),
    {
      req(input$file, rv$res_auto_df)
      t_i_path <- paste0(tempfile(), ".csv")
      t_o_path <- paste0(tempfile(), ".csv")
      
      # write manual df to disk as csv
      write.csv(rv$res_auto_df, t_i_path, row.names = FALSE)
      
      # Run args to calcfu scripts
      # TODO: Add weighed and other widgets
      cmd <- c("-i", t_i_path, "-o", t_o_path, 
               "-g", rv$opt_grp, "-gn", rv$opt_grp_n, 
               "-d", rv$opt_dils)
      res <- system2("python3", args = cmd, stdout = TRUE)
  
      # cmd <- c("calc_auto.sh", t_i_path, t_o_path, "False", rv$opt_grp, rv$opt_grp_n, rv$opt_dils)
      # res <- system2("bash", args = cmd, stdout = TRUE)
      
      if (file.exists(t_o_path)){
        return(read.csv(t_o_path))
      } else {
        # if file doesn't exist, py script failed. output error.
        stop(safeError(res))
      }
      
    }
  )
  
  output$man_input <- renderDataTable(
    # https://stackoverflow.com/questions/57215607/render-dropdown-for-single-column-in-dt-shiny
    {
      init_man_df(10)
    }, 
    selection = 'none', escape = FALSE, server = FALSE,
    options = list(dom = 't', paging = FALSE, ordering = FALSE),
    callback = JS("table.rows().every(function(i, tab, row) {
        var $this = $(this.node());
        $this.attr('id', this.data()[0]);
        $this.addClass('shiny-input-container');
      });
      Shiny.unbindAll(table.table().node());
      Shiny.bindAll(table.table().node());")
  )
  
  output$man_results <- renderDataTable({
    req(input$man_submit, rv$res_man_df)
    t_i_path <- paste0(tempfile(), ".csv")
    t_o_path <- paste0(tempfile(), ".csv")
    
    # write manual df to disk as csv
    write.csv(rv$res_man_df, t_i_path, row.names = FALSE)
    
    # Run sh script to py calcfu scripts
    cmd <- c("-i", t_i_path, "-o", t_o_path)
    res <- system2("python3", args = cmd, stdout = TRUE)
    
    # cmd <- c("calc_man.sh", t_i_path, t_o_path)
    # res <- system2("bash", args = cmd, stdout = TRUE)

    return(read.csv(t_o_path))
    
    
  })
}
