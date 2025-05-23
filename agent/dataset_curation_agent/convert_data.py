import json

# Set your input file name here
INPUT_FILE = "diff_benchmark.json"
OUTPUT_FILE = "simple_python_bugs.jsonl"

with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
    print(f"Processing: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        try:
            # Load the entire JSON file as a list
            data_list = json.load(f)

            # Process each item in the list
            for data in data_list:
                try:
                    correct_code = data.get("correct_code")
                    prompt_code = data.get("prompt_code", "")

                    formatted = {
                        "correct_code": correct_code,
                        "prompt_code": prompt_code
                    }

                    output.write(json.dumps(formatted) + "\n")
                except Exception as e:
                    print(f"Error processing item: {e}")
        except Exception as e:
            print(f"Error reading JSON file: {e}")