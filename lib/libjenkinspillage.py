#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import json
import bs4
import urllib
from json import JSONDecodeError

# proxies = {
#     'http': 'socks4a://localhost:9080',
#     'https': 'socks4a://localhost:9080'

class JenkinsJobBuild():
    """Class to interact with builds once you find them"""
    def __init__(self, url, proxies={}, auth={}):
        # validate the URL before using it
        url_validation = urllib.parse.urlparse(url)
        if not all([url_validation.scheme , url_validation.netloc , url_validation.path]):
            raise ValueError
        self.url = url
        self.base_url = url_validation.scheme + '://' + url_validation.netloc
        self.auth = auth
        # if "hudson.model.FreeStyleBuild" not in self._api_request(url):
        #     print("You did not specify a correct build URL: {}".format(url))
        #     raise ValueError
    
    def _api_request(self, url):
        return requests.get(url, verify=False, auth=self.auth).text

    def get_console_text(self):
        """
        Gets console output text from a specific job build
        """
        console_text_api = '/consoleText'
        return self._api_request(self.url + console_text_api)
    
    def get_env_vars(self):
        """
        Gets the prepopulated environment variables for the job build
        """
        env_vars_api = '/injectedEnvVars/api/json'
        env_vars_json = self._api_request(self.url + env_vars_api)
        try:
            env_vars_json = json.loads(env_vars_json)
            return env_vars_json['envMap']
        except JSONDecodeError:
            return None

    def _grab_tags(self, url):
        """
        Return a bs4 object containing all the tags in doc of the URL
        """
        a = self._api_request(url)
        return bs4.BeautifulSoup(a,features="html.parser")

    def get_workspace_zip(self):
        """
        Gets the workspace zip for the specific build URL by parsing HTML
        The API has no way of retrieving the workspace zip AFAIK
        """
        workspace_api = '/ws/'
        # print("Checking Workspaces For: {}".format(self.url))
        workspace_elements = self._grab_tags(self.url + workspace_api)
        workspace_links = []
        root_domain = urllib.parse.urlparse(self.url).scheme + '://' + urllib.parse.urlparse(self.url).netloc
        for link in workspace_elements.find_all(name='a', href=True):
            if '/execution/node/' in link['href']:
                workspace_links.append(link['href'])
        if len(workspace_links) > 0:
            for workspace_link in workspace_links:
                single_workspace_elements = self._grab_tags(root_domain + workspace_link)
                for link in single_workspace_elements.find_all(name='a', href=True):
                        if '/*zip*/' in link['href']:
                            # URL returned as relative link, must reconstruct
                            print("FOUND ZIP: {}".format(root_domain + workspace_link + link['href']))
                            return root_domain + workspace_link + link['href']

def get_all_build_links(url, auth=None, netloc_force=False):
    """
    Recursively search through all jobs and projects to pull out build URLs
    """
    all_build_links = []
    if 'api/json' not in url:
        # if the api endpoint isnt appended, then append it:
        url += '/api/json/'
    def recurse_to_build(url):
        orig_url = urllib.parse.urlparse(url)
        try:
            json_reply = json.loads(requests.get(url, verify=False, auth=auth).text)
        except JSONDecodeError:
            return
        if 'builds' in json_reply:
            if len(json_reply['builds']) > 0:
                url_link = json_reply['builds'][0]['url']
                if netloc_force:
                    url_link = urllib.parse.urlparse(url_link)
                    url_link = url_link._replace(netloc=orig_url.netloc)
                    url_link = url_link.geturl()
                print("{}".format(url_link))
                all_build_links.append(url_link)
        if 'jobs' in json_reply:
            for job in json_reply['jobs']:
                url_link = job['url'] + 'api/json/'
                if netloc_force:
                    url_link = urllib.parse.urlparse(url_link)
                    url_link = url_link._replace(netloc=orig_url.netloc)
                    url_link = url_link.geturl()
                recurse_to_build(url_link)
        if 'endpoint' in json_reply:
                url_link = json_reply['endpoint'] + 'api/json/'
                if netloc_force:
                    url_link = urllib.parse.urlparse(url_link)
                    url_link = url_link._replace(netloc=orig_url.netloc)
                    url_link = url_link.geturl()
                recurse_to_build(url_link)
    recurse_to_build(url)
    return all_build_links

