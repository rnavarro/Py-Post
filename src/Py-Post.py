'''
Created on Apr 10, 2010

@author: Robert Navarro <rnavarro@phiivo.com>
'''

def _preProcess(file_list):
    # Calculate CRCs if needed; generate and sfv files
    # Generate any Par Files
    return None

def parseArgs():
    parser = optparse.OptionParser(usage=__doc__, version = Py-Post.version)
    parser.add_option('-h', '--host', type='string', dest='host',
                      help='hostname or IP of the news server')
    parser.add_option('-p', '--port', type='int', dest='port',
                      help='port number on the news server')
    parser.add_option('-u', '--username', type='string', dest='username',
                      help='username on the news server')
    parser.add_option('-p', '--password', type='string', dest='password',
                      help='password on the news server')
    parser.add_option('-f', '--email', type='string', dest='email',
                      help='posting email address')
    parser.add_option('-F', '--name', type='string', dest='name',
                      help='posting name')
    parser.add_option('-g', '--group', type='string', dest='group',
                      help='newsgroups to post to')
    parser.add_option('-s', '--subject', type='string', dest='subject',
                      help='subject')
    parser.add_option('-v', '--verbose', type='string', dest='verbose',
                      help='be verbose')
    parser.add_option('-V', '--version', type='string', dest='version',
                      help='print version info and exit')

def main():
    print("Hello World!")
    # Pre-Process
    parfiles = _preProcess()
    
    # Post!
    # encode_and_post(file_list, parfiles)

if __name__ == '__main__':
    main()