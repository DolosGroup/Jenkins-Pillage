#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from typing import NoReturn

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import json
import bs4
import urllib
from json import JSONDecodeError

# proxies = {
#     'http': 'socks4a://localhost:9080',
#     'https': 'socks4a://localhost:9080'


class JenkinsConnection:
    """Class to interact with builds once you find them"""

    def __init__(self, url, proxies={}, auth={}):
        # validate the URL before using it
        url_validation = urllib.parse.urlparse(url)
        if not all([url_validation.scheme, url_validation.netloc, url_validation.path]):
            raise ValueError
        self.url = url
        self.base_url = url_validation.scheme + "://" + url_validation.netloc
        self.auth = auth
        # if "hudson.model.FreeStyleBuild" not in self._api_get(url):
        #     print("You did not specify a correct build URL: {}".format(url))
        #     raise ValueError

    def _add_crumb_header(self, url: str) -> dict:
        """
        Add crumb header to request.  Largely adopted from openstack/python-jenkins
        """

        response = requests.get(
            f"{url}/crumbIssuer/api/json", auth=self.auth, verify=False
        )

        if response.ok:
            crumb = response.json()
            return {f"{crumb['crumbRequestField']}": f"{crumb['crumb']}"}

        return {}

    def _api_get(self, url: str) -> str:
        return requests.get(url, verify=False, auth=self.auth)

    def _api_post(self, url: str, data: dict = None) -> str:
        return requests.post(
            url,
            verify=False,
            auth=self.auth,
            data=data,
            headers=self._add_crumb_header(url=self.url),
        )

    def execute_script(self, script):
        """
        Open Groovy script and send to script console, executed
        if we have rights to do so
        """

        with open(script) as filename:
            code = filename.read()
            response = self._api_post(
                url=f"{self.url}/scriptText", data={"script": f"{code}".encode("utf-8")}
            )

            try:
                return json.dumps(response.json(), sort_keys=True, indent=4)
            except JSONDecodeError:
                # Either a huge stack trace is in response.text (Groovy error) or we've got some
                # lack of permissions preventing the execution of scripts
                return None

    def get_console_text(self):
        """
        Gets console output text from a specific job build
        """
        console_text_api = "/consoleText"
        response = self._api_get(self.url + console_text_api)

        if response.ok:
            return response.text

        return None

    def get_env_vars(self):
        """
        Gets the prepopulated environment variables for the job build
        """
        env_vars_api = "/injectedEnvVars/api/json"
        env_vars_json = self._api_get(self.url + env_vars_api).text
        try:
            env_vars_json = json.loads(env_vars_json)
            return env_vars_json["envMap"]
        except JSONDecodeError:
            return None

    def _grab_tags(self, url):
        """
        Return a bs4 object containing all the tags in doc of the URL
        """
        obj = self._api_get(url).text
        return bs4.BeautifulSoup(obj, features="html.parser")

    def get_workspace_zip(self):
        """
        Gets the workspace zip for the specific build URL by parsing HTML
        The API has no way of retrieving the workspace zip AFAIK
        """
        workspace_api = "/ws/"
        # print("Checking Workspaces For: {}".format(self.url))
        workspace_elements = self._grab_tags(self.url + workspace_api)
        workspace_links = []
        root_domain = (
            urllib.parse.urlparse(self.url).scheme
            + "://"
            + urllib.parse.urlparse(self.url).netloc
        )
        for link in workspace_elements.find_all(name="a", href=True):
            if "/execution/node/" in link["href"]:
                workspace_links.append(link["href"])
        if len(workspace_links) > 0:
            for workspace_link in workspace_links:
                single_workspace_elements = self._grab_tags(
                    root_domain + workspace_link
                )
                for link in single_workspace_elements.find_all(name="a", href=True):
                    if "/*zip*/" in link["href"]:
                        # URL returned as relative link, must reconstruct
                        print(
                            "FOUND ZIP: {}".format(
                                root_domain + workspace_link + link["href"]
                            )
                        )
                        return root_domain + workspace_link + link["href"]


def get_all_build_links(url, auth=None, netloc_force=False):
    """
    Recursively search through all jobs and projects to pull out build URLs
    """
    all_build_links = []
    if "api/json" not in url:
        # if the api endpoint isnt appended, then append it:
        url += "/api/json/"

    def recurse_to_build(url):
        orig_url = urllib.parse.urlparse(url)
        try:
            json_reply = json.loads(requests.get(url, verify=False, auth=auth).text)
        except JSONDecodeError:
            return
        if "builds" in json_reply:
            if len(json_reply["builds"]) > 0:
                url_link = json_reply["builds"][0]["url"]
                if netloc_force:
                    url_link = urllib.parse.urlparse(url_link)
                    url_link = url_link._replace(netloc=orig_url.netloc)
                    url_link = url_link.geturl()
                print("{}".format(url_link))
                all_build_links.append(url_link)
        if "jobs" in json_reply:
            for job in json_reply["jobs"]:
                url_link = job["url"] + "api/json/"
                if netloc_force:
                    url_link = urllib.parse.urlparse(url_link)
                    url_link = url_link._replace(netloc=orig_url.netloc)
                    url_link = url_link.geturl()
                recurse_to_build(url_link)
        if "endpoint" in json_reply:
            url_link = json_reply["endpoint"] + "api/json/"
            if netloc_force:
                url_link = urllib.parse.urlparse(url_link)
                url_link = url_link._replace(netloc=orig_url.netloc)
                url_link = url_link.geturl()
            recurse_to_build(url_link)

    recurse_to_build(url)
    return all_build_links
