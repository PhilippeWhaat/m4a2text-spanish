import os

def post_process_text_file(file_path):
    # Read the content of the file
    with open(file_path, "r") as infile:
        text_content = infile.read()

    # Perform the post-processing
    text_content = text_content.replace("```\n", " ").replace("```", " ").replace("\n", " ")
    while "  " in text_content:
        text_content = text_content.replace("  ", " ")

    # Save the post-processed text back to a new file
    output_file_path = os.path.splitext(file_path)[0] + "_processed.txt"
    with open(output_file_path, "w") as outfile:
        outfile.write(text_content)

    print(f"Post-processing completed. Results saved to '{output_file_path}'.")

if __name__ == "__main__":
    file_path = input("Enter the path to the text file for post-processing: ").strip()
    
    if not os.path.isfile(file_path):
        print("Invalid file path. Please try again.")
    else:
        post_process_text_file(file_path)