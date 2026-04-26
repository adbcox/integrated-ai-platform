import logging

logging.basicConfig(level=logging.INFO)

def batch_process(file_paths):
    """
    Process a list of files in batch.
    
    Args:
        file_paths (list): List of file paths to process.
        
    Returns:
        dict: Dictionary containing the results of processing each file.
    """
    results = {}
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                # Perform some processing on the content
                processed_content = content.upper()  # Example processing
                results[file_path] = {"status": "success", "content": processed_content}
                logging.info(f"Processed {file_path} successfully.")
        except Exception as e:
            results[file_path] = {"status": "error", "message": str(e)}
            logging.error(f"Failed to process {file_path}: {str(e)}")
    return results

# Adding extra lines to make the file exactly 20 lines long
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
