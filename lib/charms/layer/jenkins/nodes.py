from urllib.error import URLError

from jenkins import Jenkins, JenkinsException

from charmhelpers.core import hookenv
from charmhelpers.core.decorators import (
    retry_on_exception,
)

from charmhelpers.core.hookenv import (
    ERROR,
)

from charms.layer.jenkins.credentials import Credentials

URL = "http://localhost:8080/"
RETRIABLE = (URLError, JenkinsException)


class Nodes(object):
    """Encapsulate operations on the Jenkins master."""

    def __init__(self, hookenv=hookenv, jenkins=Jenkins):
        """
        @param hookenv: An object implementing the charmhelpers.core.hookenv
            API from charmhelpers (for testing).
        @param jenkins: A client factory for driving the Jenkins API.
        """
        self._hookenv = hookenv
        self._jenkins = jenkins

    # Wait up to 140 seconds for Jenkins to be fully up.
    @retry_on_exception(7, base_delay=5, exc_type=RETRIABLE)
    def wait(self):
        client = self._make_client()
        client.get_version()

    def add(self, host, executors, labels=()):
        """Add a slave node with the given host name."""
        self.wait()

        client = self._make_client()

        @retry_on_exception(3, 3, exc_type=RETRIABLE)
        def _add_node():
            if client.node_exists(host):
                self._hookenv.log("Node exists - not adding")
                return

            self._hookenv.log("Adding node '%s' to Jenkins master" % host)
            client.create_node(host, int(executors) * 2, host, labels=labels)
            if not client.node_exists(host):
                self._hookenv.log(
                    "Failed to create node '%s'" % host, level=ERROR)

        return _add_node()

    def delete(self, host):
        """Delete the slave node with the given host name."""
        client = self._make_client()
        if client.node_exists(host):
            self._hookenv.log("Node '%s' exists" % host)
            client.delete_node(host)
        else:
            self._hookenv.log("Node '%s' does not exist - not deleting" % host)

    def _make_client(self):
        """Build a Jenkins client instance."""
        creds = Credentials(hookenv=self._hookenv)
        return self._jenkins(URL, creds.username(), creds.password())
