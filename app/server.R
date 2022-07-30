# setup sweet alerts
useSweetAlert()

server <- function(input, output, session) {

  rv <- reactiveValues(
    res_man_df = NULL,
    res_auto_df = NULL,
    missing_cols = NULL
  )

  stop_alert <- function(msg, title, msg_type = "error") {
    sendSweetAlert(
      session = session,
      title = paste0(stringr::str_to_title(msg_type), ": ", title),
      text = msg,
      type = msg_type)
    shiny:::reactiveStop(msg)
  }

  process_data <- function(df, input) {
    # find date column.
    date_col_ind <-startsWith(names(df), "Date")
    date_col_name <- names(df)[date_col_ind]

    dt_df <- df %>%
      # rename column to remove unwanted chrs
      rename(c("DateTime" = date_col_name[1])) %>%

      # filter based on provided dates and timesin input
      filter(strptime(DateTime, "%m/%d/%Y %I:%M:%S %p") >= strptime(paste(input$dates[1], input$times[1]), "%Y-%m-%d %I:%M:%S %p")) %>%
      filter(strptime(DateTime, "%m/%d/%Y %I:%M:%S %p") <= strptime(paste(input$dates[2], input$times[2]), "%Y-%m-%d %I:%M:%S %p")) %>%
      # Replace dilutions with easier to read formats.
      mutate(Dilution = case_when(Dilution == "1 : 1" ~ "1:1",
                                  Dilution == "1 : 10" ~ "-1",
                                  Dilution == "1 : 100" ~ "-2",
                                  Dilution == "1 : 1000" ~ "-3",
                                  Dilution == "1 : 10000" ~ "-4")) %>%

      # Remove calculated column.
      select(!contains("Calculated"))

    edit_cnts_df <- dt_df %>%
      select(contains("Edited")) %>%
      # Set values of "-" to NA
      mutate(across(everything(), function(x) ifelse(x == "-", NA, x)))

    raw_cnts_df <- dt_df %>%
      select(contains("Raw"))

    # Set raw_cnts values that share loc with edit_cnts to edit_cnts values that aren't NA
    raw_cnts_df[!is.na(edit_cnts_df)] <- edit_cnts_df[!is.na(edit_cnts_df)]

    adj_df <- dt_df %>%
      # Select everything but the count columns
      select(!contains("Count")) %>%
      # Add index to join by.
      mutate(idx = row_number(), .before = 1) %>%
      # Perform left join on raw_cnts_df with index added.
      left_join(raw_cnts_df %>% mutate(idx = row_number(), .before = 1), by = "idx") %>%
      # Remove "." in colnames.
      rename_with(.cols = everything(), ~gsub("\\.", " ", .x)) %>%
      # Deselect index.
      select(-idx) %>%
      relocate(Comment, .after = last_col())

    return(adj_df)

  }

  check_cols <- function(data, input) {
    # if no header, add colnames. can't do if header, cause might erase data.
    data_column_names <- gsub("\\.|\\/", " ", names(data))
    column_names <- c(
      "Technician",
      "Sample ID",
      "Date/Time of Image",
      "Plate Type",
      "Dilution",
      "Barcode Text",
      "Red Raw Count",
      "Red Edited Count",
      "Red Calculated Count",
      "Red with Gas Raw Count",
      "Red with Gas Edited Count",
      "Red with Gas Calculated Count",
      "Blue Raw Count",
      "Blue Edited Count",
      "Blue Calculated Count",
      "Blue with Gas Raw Count",
      "Blue with Gas Edited Count",
      "Blue with Gas Calculated Count",
      "Comment"
    )

    col_check <- data_column_names == column_names
    missing_cols <- column_names[!col_check]
    rv$missing_cols <- missing_cols

    if (all(col_check)) {
      return(data)
    } else if (length(data_column_names) == length(column_names) && isFALSE(input$header)){
      # to avoid read errors, set column names of df if *equal num of columns and *header is false
      names(data) <- column_names
      return(data)
    } else {
      stop_alert(paste("One or multiple columns are missing.", "[", paste(rv$missing_cols, collapse = ", "), "]"), "Invalid Columns")
    }
  }

  read_data <- function(input) {
    # when reading semicolon separated files,
    # having a comma separator causes `read.csv` to error
    tryCatch(
      {
        df <- read.csv(input$file$datapath, header = input$header, sep = input$sep) %>%
          check_cols(input)

        return(df)
      },
      error = function(e) {
        # if file header left in results and num cols doesn't match df.
        if (e$message == "more columns than column names") {
          # Equal num of columns and header is false.
          og_df <- read.csv(input$file$datapath,
                            header = FALSE,
                            sep = input$sep)

          # slice out 1st row containing header
          edited_df <- slice(og_df, 3:n())

          # make first row of initial df the column names
          names(edited_df) <- og_df[2,]

          # recheck cols
          final_df <- check_cols(edited_df, input)
          return(final_df)
        }
        else {
          # return a safeError if a parsing error occurs
          stop_alert(e$message, "Read Failure")
        }
      }
    )

  }

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
    err = FALSE
    msg = "None"

    if (is.na(input$dates[1]) | is.na(input$dates[2])) {
      err = TRUE
      msg = "Please provide both a start and an end date."
    } else if (input$dates[1] > input$dates[2]) {
      err = TRUE
      msg = "Start date should be earlier than end date."
    }

    if (isTRUE(err)) {
      stop_alert(msg, "Invalid Date", msg_type = "warning")
    }

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
    og_value <- rv$res_auto_df[info$row, info$col]

    # replace value in reactive values and coerce to whatever dtype in that pos
    tryCatch(
      expr = {
        rv$res_auto_df[info$row, info$col] <- coerceValue(info$value, rv$res_auto_df[info$row, info$col])

        # replace DT and keep state of table
        replaceData(proxy_auto_input, rv$res_auto_df, resetPaging = FALSE)
      },
      error = function(e){
        msg = sprintf("Invalid value entered (%s [%s, %s])",
                      info$value, info$row, info$col)
        stop_alert(msg, "Invalid Value")
      }
    )
  })

  # set options msgs and enable or disable inputs.
  observeEvent(input$options, {
    option_key <-
      list("Allow no ID? (Group by #)" = "opt_grp_n",
           "Allow different dilutions? (Set dilutions)" = "opt_dils",
           "Allow different plate types? (Set plate type)" = "opt_plt")

    # disable all inputs
    lapply(option_key,
           function(x) disable(x))

    # enable selected inputs
    lapply(input$options,
           function(x) enable(option_key[x][[1]]))

  }, ignoreNULL = FALSE)

  output$auto_input <- renderDT(
    options = list(scrollX = TRUE),
    selection = "single",
    editable = TRUE,
    {
      req(input$file)
      df <- upl_data()
      # save df to reactive values
      rv$res_auto_df <- df
      return(df)
    }
  )

  exec_cmd <- function(i_path, o_path, shiny_input, method = "auto") {
    cmd <- c(sprintf("reader/read_%s.py", method), "-i", i_path, "-o", o_path)

    if ("Weighed?" %in% input$options) {
      cmd <- append(cmd, "-w")
    }
    if ("Allow no ID? (Group by #)" %in% input$options) {
      cmd <- append(cmd, paste("-g", input$opt_grp_n))
    }
    # These default to "None" in argparse py script if condition not met.
    if ("Allow different plate types? (Set plate type)" %in% input$options) {
      cmd <- append(cmd, paste("-p", input$opt_plt))
    }

    if ("Allow different dilutions? (Set dilutions)" %in% input$options) {
      dilutions <- paste(unlist(strsplit(input$opt_dils, "/")), collapse = " ")
      cmd <- append(cmd, paste('-d', dilutions))
    }

    return(cmd)
  }

  output$auto_results <- renderDataTable(
    options = list(scrollX = TRUE),
    {
      req(input$file, rv$res_auto_df)
      t_i_path <- paste0(tempfile(), ".csv")
      t_o_path <- paste0(tempfile(), ".csv")

      # write manual df to disk as csv
      write.csv(rv$res_auto_df, t_i_path, row.names = FALSE)

      # Run args to calcfu scripts
      cmd <- exec_cmd(t_i_path, t_o_path, input, method = "auto")
      res <- system2("python3", args = cmd, stdout = TRUE)

      if (file.exists(t_o_path)){
        return(read.csv(t_o_path))
      } else {
        # if file doesn't exist, py script failed. output error.
        stop_alert(res, "3M Script Failure")
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
    cmd <- exec_cmd(t_i_path, t_o_path, input, method = "man")
    res <- system2("python3", args = cmd, stdout = TRUE)

    # res <- system2("bash", args = cmd, stdout = TRUE)

    if (file.exists(t_o_path)){
      return(read.csv(t_o_path))
    } else {
      # if file doesn't exist, py script failed. output error.
      stop_alert(res, title = "Manual Script Failure")
    }

  })
}
