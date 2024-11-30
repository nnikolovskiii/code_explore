from app.llms.generic_chat import generic_chat


def check_contents_quality_template(
        html_content: str,
):
    return f"""Below you are given contents of a html site. Your job is to provide a verdict "yes" if the site is one of these pages: navigation page, index page, or gateway page. Return a verdict "no" if it is a content page or has at least some content.
First reason than provide verdict.

Html content:
{html_content}

For last return a json with this format: {{"verdict": "yes or no"}}
"""

def extract_contents_template(
        html_content: str,
):
    return f"""Below you are given contents of a html site. Your job is to reorganize the information from the text into segments. 

Html content:
{html_content}

You must not skip any information from the text. Include every line.

Return in format: 
###Detailed Title: (write detailed title here)
...
###Subtitle
...
###Subtitle
"""


def check_contents_quality(
        html_content: str,
):
    template = check_contents_quality_template(html_content)
    response = generic_chat(template)
    print(response)


def extract_contents(
        html_content: str,
):
    template = extract_contents_template(html_content)
    response = generic_chat(template, "You are an expert AI assistant for extracting information from html websites.")
    return response
