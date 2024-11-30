from app.llm_flows.json_response import get_json_response


def check_site_relevance_template(
        topic: str,
        url: str,
        html_content: str,
):
    return f"""Below you are given contents of a html site and a description of the whole documentation. Your job is to determine if the sites content is part of the specified documentation.
Some rules to help with the verdict:
1. Determine if the site is useful for the topic, and see if it has or leads to any useful information related to the topic. Start with reasoning why it is or isn't useful and than return a verdict.
2. Also the site must not be legacy and old code and old documentation site.
3. The site must be related to documentation.
    
Topic:
{topic}
END

URL of the site: {url}
    
Html content:
{html_content}

Return a json in the end with the following format: {{"verdict": "yes or no"}}
"""


def check_site_relevance(
        topic: str,
        url: str,
        html_content: str,
):
    template = check_site_relevance_template(topic,url, html_content)
    response = get_json_response(template)
    return response["verdict"] == "yes"
