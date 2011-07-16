from yum.plugins import TYPE_CORE
import time
import urllib2
import urlparse
from ConfigParser import ConfigParser
import sys

requires_api_version = '2.5'
plugin_type = (TYPE_CORE,)
FASTESTMIRROR_CONF='/etc/yum/pluginconf.d/fastestmirror.conf'

class ScanMirrorCommand(object):

    checked = []

    def getNames(self):
        return ['time-mirrors']

    def getUsage(self):
        return "usage????"

    def getSummary(self):
        return "Scan mirrors"

    def doCheck(self, base, basecmd, extcmds):
        pass

    def doCommand(self, base, basecmd, extcmds):
        fastest = []
        for repo in base.repos.listEnabled():
            # try to check any one of these, smallest first
            for md in [ 'group', 'other', 'primary', 'filelists']:
                try:
                    mdpath = repo.repoXML.getData(md).location[1]
                    break
                except:
                    continue
            scores = self._score_hosts(repo, mdpath, md)

            # sort, fastest first
            scores.sort(key=lambda x: x[0], reverse=True)

            # only take the top 3 fastest of each repo
            fastest = fastest + [x[1] for x in scores[:3]]

        # remove duplicates
        fastest = set(fastest)

        self._write_mirrors(fastest)
        sys.exit()


    def _write_mirrors(self, mirrors):
        fastestmirrorconf = open(FASTESTMIRROR_CONF)
        cp = ConfigParser()
        cp.readfp(fastestmirrorconf)
        cp.set('main', 'include_only', ','.join(mirrors))
        conf = open(FASTESTMIRROR_CONF, 'w')
        cp.write(conf)
        conf.close()

    def _score_hosts(self, repo, mdpath, md=''):
        scored_hosts = []
        if len(repo.urls) == 1:
            url = repo.urls[0]
            hostname = urlparse.urlparse(url).netloc
            return [(9999, hostname)]

        for url in repo.urls:
            fileurl = '%s/%s' % (url, mdpath)
            hostname = urlparse.urlparse(url).netloc
            if hostname in self.checked:
                continue

            print "timing %s" % hostname, md, 
            try:
                speed = self._get_download_speed(url)
            except urllib2.URLError:
                speed = 0
            print "%s" % speed
            self.checked.append(hostname)

            scored_hosts.append((speed, hostname))
        return scored_hosts

    def _get_download_speed(self, url):
        headers = {'Pragma': 'no-cache',
                   'Cache-Control': 'no-cache'}
        request = urllib2.Request(url, None, headers)
        start_time = time.time()
        usock = urllib2.urlopen(request)
        fsize = len(usock.read())
        elapsed = time.time() - start_time
        speed = (fsize/1024) / elapsed
        return speed

def config_hook(conduit):
    '''
    '''

    parser = conduit.getOptParser()
    if not parser:
        return

    if hasattr(parser, 'plugin_option_group'):
        parser = parser.plugin_option_group

    conduit.registerCommand(ScanMirrorCommand())
