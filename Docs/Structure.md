project/
  main.py                # very small, entry point only
  config_io.py           # all I/O-related settings, loaded from a user editable file
  header_resolver.py     # logic to map logical fields -> actual Excel headers
  reference_data.py      # reading reference workbook (J0BCARD list, B84)
  task_ids.py            # extracting and checking task IDs
  comparisons.py         # B84 vs C9 comparison
  processing.py          # process_excel_file and report orchestration
  time_utils.py          # time_to_hours, hours_to_hhmm
