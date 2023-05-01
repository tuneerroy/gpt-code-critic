import openai
import os
import json

# Use GPT-3 to analyze code and generate code problems
def analyze_file(filename, code_diff):
    # Preface with explanation
    prompt = "Analyze the following code changes to file " + filename + ".\n"
    prompt += "You should format your response like:\n"
    prompt += "Issue X (Line Y, Column Z)::: Comment about problem, quality, readability, or issue\n"
    prompt += "Issue X (Line Y, Column Z)::: Comment about problem, quality, readability, or issue\n"
    prompt += "...\n\n\n"
    prompt += "diff:\n" + code_diff + "\n"

    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    # Extract the generated analysis from the API response
    result = completion.choices[0].message.content

    return result

# Process results to SARIF format
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

def get_sarif_report(key, files):
    openai.api_key = key
    sarif_files = []
    for name, code in files.items():
        problems = analyze_file(name, code)
        sarif_file = get_sarif_results_for_file(name, problems)
        sarif_files.append(sarif_file)
    sarif_report = combine_sarif_results(sarif_files)
    return sarif_report

def get_sarif_report(files):
    return get_sarif_report(os.environ.get("OPENAI_API_KEY"), files)

if __name__ == '__main__':
    filename = 'main.py'
    code = 'def foo():\n    prnt("Hello, world!")'

    print(get_sarif_report({filename: code}))
