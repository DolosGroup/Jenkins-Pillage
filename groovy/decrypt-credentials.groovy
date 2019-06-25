import groovy.json.JsonOutput

def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardUsernameCredentials.class,
    Jenkins.instance,
    null,
    null
);

List list = []

for (c in creds) {
    if( c.properties.class.toString() == 'class com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey') {
        list << [username: c.properties.username, privatekey: c.properties.privateKey, description: c.properties.description]
    }
    if (c.properties.class.toString() == 'class com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl') {
        list << [username: c.properties.username, password: c.properties.password, description: c.properties.description]
    }
}

println(JsonOutput.toJson(list))
