# Upgrade Plan: Refactoring `main.py` into Modular Code

## **Objective**

The goal is to refactor the existing `main.py` script into smaller, modular Python files. This will make the code more maintainable, flexible, and user-friendly, especially for people who are not familiar with programming.

This upgrade will include:

* Separating the input/output handling, data processing, and configuration into distinct modules.
* Making file and column configuration editable through a settings file (`settings.ini`), instead of hard-coding paths and column names.
* Ensuring that debugging functions (such as the `check_task_id` function) are retained, while removing unnecessary debugging code.

## **Modules to be Created**

### **1. Configuration Module (`config.py`)**

* **Purpose:** Store all configurable parameters such as file paths, column names, and processing options.
* **Key Features:**

  * Allow users to modify the input/output file names, directory paths, and column names without modifying the core logic.
  * Use a configuration file (`settings.ini`) to manage parameters in a simple and non-technical way.
* **File Example:**

  ```ini
  [Paths]
  input_file = input.csv
  output_file = output.csv

  [Columns]
  column_task_id = TaskID
  column_planned_mhrs = Planned Mhrs
  column_check_id = CheckID

  [Processing]
  ignore_missing_columns = False
  ```
* **Details:**

  * This file will be read using Python's `configparser` module.
  * Users can change the file paths and column names directly in the `settings.ini` file.

### **2. Input/Output Module (`input_output.py`)**

* **Purpose:** Manage reading from input files and writing to output files.
* **Key Features:**

  * Load the input file based on the path set in `settings.ini`.
  * Save the results to the specified output file.
  * Ensure file handling is modular and separated from the core processing logic.
* **Functions:**

  * `load_input_file()`: Reads data from the input file and returns it.
  * `save_output_file()`: Saves processed data to the output file.
  * `validate_file_path()`: Ensures the file path is valid and accessible.
* **Example Code:**

  ```python
  import configparser

  config = configparser.ConfigParser()
  config.read('settings.ini')

  input_file = config['Paths']['input_file']
  output_file = config['Paths']['output_file']

  def load_input_file():
      # Logic to load the input file (CSV, Excel, etc.)
      pass

  def save_output_file(data):
      # Logic to save data to the output file
      pass
  ```

### **3. Data Processing Module (`data_processing.py`)**

* **Purpose:** Handle all the core data transformation and processing.
* **Key Features:**

  * Process the data (e.g., convert "Planned Mhrs", check `TaskID` validity).
  * Handle column-specific logic (e.g., checking if the expected columns are present in the input file).
  * Modularize each processing step into its own function.
* **Functions:**

  * `process_data()`: The main function that applies all the necessary data transformations.
  * `convert_planned_mhrs()`: Converts "Planned Mhrs" into hours or a standard format.
  * `check_task_id()`: Validates the task ID based on `B84` vs `C9` (retained as per the need for task comparison).
  * `validate_columns()`: Checks if required columns exist in the input data.
* **Example Code:**

  ```python
  def convert_planned_mhrs(row):
      # Convert the "Planned Mhrs" column into hours format
      pass

  def check_task_id(row):
      # Check the TaskID and compare B84 vs C9
      pass

  def validate_columns(columns):
      # Ensure that necessary columns are present in the data
      pass

  def process_data(input_data):
      # Process data using the above functions
      pass
  ```

### **4. Output Formatting Module (`output_formatting.py`)**

* **Purpose:** Format the results before saving to the output file.
* **Key Features:**

  * Apply any required formatting to the processed data before outputting (e.g., rounding values, adding headers).
  * Generate reports, summaries, or any other necessary output formats.
* **Functions:**

  * `format_output_data()`: Formats data in a suitable way for output.
  * `generate_report()`: Creates a summary report from the processed data.
* **Example Code:**

  ```python
  def format_output_data(data):
      # Logic to format the processed data
      pass

  def generate_report(data):
      # Generate a summary report or any other output type
      pass
  ```

### **5. Main Execution (`main.py`)**

* **Purpose:** The entry point of the program that ties everything together.
* **Key Features:**

  * Orchestrates the entire flow: loading data, processing it, and saving the result.
  * Calls functions from the input/output module, data processing module, and output formatting module.
  * Remains lightweight and focuses on managing the sequence of operations.
* **Example Code:**

  ```python
  from input_output import load_input_file, save_output_file
  from data_processing import process_data
  from output_formatting import generate_report

  def main():
      input_data = load_input_file()
      processed_data = process_data(input_data)
      generate_report(processed_data)
      save_output_file(processed_data)

  if __name__ == '__main__':
      main()
  ```

---

## **File Organization After Refactoring**

* `main.py`: Entry point for the program, responsible for calling functions from the other modules.
* `config.py`: Stores configuration details like file paths, column names, and other settings.
* `input_output.py`: Handles file reading and writing.
* `data_processing.py`: Handles all data transformations and checks.
* `output_formatting.py`: Formats the final output before saving or reporting.

---

## **Benefits of This Approach**

1. **Separation of Concerns:** By modularizing the code, each file handles one aspect of the program, making it easier to maintain, debug, and enhance.
2. **User-Friendly Configuration:** Non-programmers can easily modify input/output paths and column names by updating the `settings.ini` file, without needing to touch the core logic.
3. **Scalability:** As the program grows, new modules can be added without disrupting the existing functionality.
4. **Cleaner Code:** With separate modules for input/output, processing, and output formatting, the code becomes more readable and manageable.

---

## **Next Steps**

1. Create and populate the `settings.ini` file with the necessary configuration.
2. Begin refactoring the `main.py` into separate modules as outlined above.
3. Test each module to ensure that it functions independently before integrating everything together.

Let me know if you'd like any further details or assistance on how to implement any specific part!
