import openai
import os
import json

"""
Analyze a file using GPT-3

Args:
    filename: the name of the file to analyze
    code_diff: the diff of the file to analyze

Returns:
    result: the analysis of the file
"""
def analyze_file(filename, code_diff):
    # preface with explanation
    prompt = "Analyze the following code changes to file " + filename + ".\n"
    prompt += "You should format your response like:\n"
    prompt += "Issue X (Line Y, Column Z)::: Comment about problem, quality, readability, or issue\n"
    prompt += "Issue X (Line Y, Column Z)::: Comment about problem, quality, readability, or issue\n"
    prompt += "...\n\n\n"
    prompt += "diff:\n" + code_diff + "\n"

    # send prompt to GPT-3
    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    # extract the generated analysis from the API response
    result = completion.choices[0].message.content

    return result


"""
Get the SARIF results for a file

Args:
    filename: the name of the file to analyze
    analysis: the analysis of the file to analyze

Returns:  
    sarif_results: the SARIF results for the file
"""
def get_sarif_results_for_file(filename, analysis):
    # Parse the generated analysis from GPT-3
    results = analysis.split('Issue')
    issues = []
    for result in results:
        issue = {}
        tokens = result.strip().split(':::')
        if len(tokens) >= 2:
            try:
                issue['message'] = tokens[1].strip()
                location = {}
                location['file'] = filename
                location['line'] = int(tokens[0].split('Line')[1].split(',')[0].strip())
                location['column'] = int(tokens[0].split('Column')[1].strip()[:-1])
                issue['location'] = location
                issues.append(issue)
            except:
                pass

    # Create SARIF result objects
    sarif_results = []
    for issue in issues:
        # Extract issue details from the analysis
        message = issue.get("message", "")
        location = issue.get("location", {})
        file_path = location.get("file", "")
        line_number = location.get("line", 0)
        column_number = location.get("column", 0)

        # Create SARIF result object
        sarif_result = {
            "message": {
                "text": message
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path
                        },
                        "region": {
                            "startLine": line_number,
                            "startColumn": column_number
                        }
                    }
                }
            ]
        }

        # Add the SARIF result object to the list
        sarif_results.append(sarif_result)
    
    return sarif_results

"""
Combine SARIF results into one report

Args:
    results: the SARIF results to combine

Returns:
    sarif_report: the combined SARIF report
"""
def combine_sarif_results(results):

    sarif_results = sum(results, []) # concatenate results into one list

    # Create SARIF report
    sarif_report = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "GPT-3.5 Code Analysis",
                        "informationUri": "https://platform.openai.com/docs/models/overview",
                        "version": "1.0"
                    }
                },
                "results": sarif_results
            }
        ]
    }

    return json.dumps(sarif_report)

"""
Get the SARIF report for a list of files

Args:
    files: the files to analyze
    key: the API key to use (optional); defaults to OPENAI_API_KEY env variable

Returns:
    sarif_report: the SARIF report for the files
"""
def get_sarif_report(files, key=os.environ.get("OPENAI_API_KEY")):
    # set API key
    openai.api_key = key

    # get SARIF results for each file
    sarif_files = []
    for name, code in files.items():
        problems = analyze_file(name, code)
        sarif_file = get_sarif_results_for_file(name, problems)
        sarif_files.append(sarif_file)

    # combine SARIF results into one report
    sarif_report = combine_sarif_results(sarif_files)

    # reset API key so it doesn't get saved
    openai.api_key = None
    
    return sarif_report

"""
Check if an API key is valid

Args:
    api_key: the API key to check

Returns:
    True if the API key is valid, False otherwise
"""
def check_api_key(api_key):
    openai.api_key = api_key
    try:
        response = openai.Completion.create(
            engine="text-ada-001",
            prompt="Hello, world!",
            max_tokens=1
        )
        if response.choices[0].text:
            return True
    except Exception as e:
        print(e)
    return False

"""
Main function for testing
"""
if __name__ == '__main__':
    filename = 'main.py'
    code = 'def foo():\n    prnt("Hello, world!")'

    if (os.environ.get("OPENAI_API_KEY") is None):
        print("Please set OPENAI_API_KEY environment variable.")
    else:
        print(get_sarif_report({filename: code}))
