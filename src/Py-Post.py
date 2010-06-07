'''
Created on Apr 10, 2010
Author: Robert Navarro <rnavarro@phiivo.com>
Version: 0.0.1

Py-Post.py [options] SourceDirectory
'''
import os
from optparse import OptionParser
import subprocess
import hashlib
import nntplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import StringIO

import yenc
from binascii import crc32
from stat import *

def _rarFiles(locations, compressionLevel, volumeSize):
    print('Raring...');
    args = ['rar', 'a', '-v'+str(volumeSize),
            '-m'+str(compressionLevel),
            locations['path']+locations['workingDirectory']+os.sep+locations['tld'], locations['path']+locations['tld']];
    print(args);
    #retcode = subprocess.check_call(args, stdout=open(os.devnull,'w'));
    retcode = subprocess.check_call(args);
    return None

def _parFiles(locations, percentage=10):
    print('Paring...');    
    args = ['par2', 'create', '-r'+str(percentage),
            '-s307200', locations['path']+locations['workingDirectory']+os.sep+'*.rar'];
    print(args);
    #retcode = subprocess.check_call(args, stdout=open(os.devnull,'w'));
    retcode = subprocess.check_call(args);
    return None

def _yEnc(locations,filename):
    print('yEncoding...')
    filePath=locations['path']+locations['workingDirectory']+os.sep+filename
    file_out = open('/tmp/usenet2', 'w')
    file_in = open(filePath,"r")
    
    crc = hex( crc32( open(filePath,"r").read() ) )[2:]
    name = os.path.split(filePath)[1]
    size = os.stat(filePath)[ST_SIZE]
    file_out.write("=ybegin line=128 size=%d crc32=%s name=%s\r\n" % (size, crc, name) )
    try:
        encoded, crc = yenc.encode(file_in, file_out, size)
    except Exception, e:
        print e
        sys.exit(3)
    file_out.write("=yend size=%d crc32=%s\r\n" % (encoded, crc) )
    file_out.close
    
    return None

def _post(locations, fingerprint):
    print(locations)
    
    for filename in os.listdir(locations['path']+locations['workingDirectory']):
        print(filename)
        filePath=locations['path']+locations['workingDirectory']+os.sep+filename
        
        size = os.stat(filePath)[ST_SIZE]
        parts = size/(5242880) # 5MB
        print(parts)
        
        if parts > 0:
            for x in range(0, parts):
                print('Part: '+str(x))
        else:
            msg = MIMEMultipart()
            msg['Subject'] = '['+fingerprint+'] "'+filename+'" yEnc ('
            msg['From'] = '<Bill Hill> jerry@eagle.ATT.COM'
            msg.add_header('Newsgroups', 'alt.test');
            msg.add_header('Content-Disposition', 'attachment', filename = filename)
            
            #_yEnc(locations,filename)
            '''
            #f = open('/tmp/post_attachment', 'rb')
            f = open(filePath, 'rb')
            file = MIMEApplication(f.read())
            f.close()
            msg.attach(file)
            
            mesStr = StringIO.StringIO();
            mesStr.write(msg.as_string())
            mesStr.seek(0)
            
            server = nntplib.NNTP('usnews.blocknews.net', '119', 'cr0ntab', 'passw0rd')
            server.set_debuglevel(1)
            print(server.getwelcome())
            server.post(mesStr)
            server.quit()
            '''
    '''
    msg = MIMEMultipart()
    msg['Subject'] = '['+fingerprint+'] Test Again'
    msg['From'] = '<Bill Hill> jerry@eagle.ATT.COM'
    msg.add_header('Newsgroups', 'alt.test');
    msg.add_header('Content-Disposition', 'attachment', filename = 'files.part01.rar.par2')
    
    _yEnc(locations,filename)
    
    #f = open('/media/Data/Downloads/Testing/[a1f13b3bc2] files/files.part01.rar.par2', 'rb')
    f = open('/tmp/usenet2', 'rb')
    file = MIMEApplication(f.read())
    f.close()
    msg.attach(file)
    
    f = open('/tmp/usenet', 'w')
    f.write(msg.as_string())
    f.close
    
    server = nntplib.NNTP('usnews.blocknews.net', '119', 'cr0ntab', 'passw0rd')
    server.set_debuglevel(2)
    print(server.getwelcome())
    f = open('/tmp/usenet', 'rb')
    server.post(f)
    server.quit()    
    f.close()
    os.remove('/tmp/usenet');
    os.remove('/tmp/usenet2');
    '''
    return None

def _addParserOptions(parser):
    # Adds options to the parser object that was passed in. 
    parser.add_option('-c', '--server-host', type='string', dest='serverHost',
                      help='hostname or IP of the news server')
    parser.add_option('-p', '--port', type='int', dest='port',
                      help='port number on the news server')
    parser.add_option('-u', '--username', type='string', dest='username',
                      help='username on the news server')
    parser.add_option('-w', '--password', type='string', dest='password',
                      help='password on the news server')
    parser.add_option('-f', '--email', type='string', dest='email',
                      help='posting email address')
    parser.add_option('-F', '--name', type='string', dest='name',
                      help='posting name')
    parser.add_option('-g', '--group', type='string', dest='group',
                      help='newsgroups to post to')
    parser.add_option('-s', '--subject', type='string', dest='subject',
                      help='subject')
    
    parser.add_option('-r', '--compress', action='store_true', dest='compress',
                      help='Enable Rar Compression', default=False)
    parser.add_option('-z', '--volume-size', type='string', dest='volumeSize',
                      help='Rar Volume Size', default='15m')
    parser.add_option('-m', '--compression-level', type='int', dest='compressionLevel',
                      help='Rar Compression Level', default='3')
    
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      help='be verbose', default=False)
    return None

def main():
    # Instantiate our CLI Option/Argument parser
    parser = OptionParser(usage=__doc__)
    _addParserOptions(parser)
    # Parse the CLI Options/Argumets
    (options, args) = parser.parse_args()
    print(options)
    print(args)
    
    if len(args) != 1:
        parser.error("incorrect number of arguments")
        
    if not os.path.isdir(args[0]):
        parser.error("We an only work with directories")
    
    # Split the given path into individual segments
    splits = args[0].rsplit(os.sep)
    print(splits)
    # Create a path string
    path = args[0][0:-len(splits[-2])-1]
    # Grab the top level directory that we're working with
    tld = splits[-2]
    
    # Create a unique fingerprint (Makes searching easier too!)
    fingerprint = hashlib.sha1(tld).hexdigest()[0:10]
    workingDirectory = '['+fingerprint+'] '+tld
    
    locations = {'path':path, 'tld':tld, 'workingDirectory':workingDirectory}
    
    if not os.path.isdir(path+workingDirectory):
        os.mkdir(path+workingDirectory)
    
    if options.compress:
        print('Running rar!')
        #_rarFiles(locations, options.compressionLevel, options.volumeSize);
        print('Finished rar')
    
    print('Running Par!')
    #_parFiles(locations);
    print('Finished Par!')
    
    print('Posting!')
    _post(locations, fingerprint)
    print('Done Posting!')
    # Pre-Process
    # Rar whatever
    # Yenc and Sfv whatever
    # Par whatever
    #parfiles = _preProcess()
    # Restrict block size to multiples of UseNet article size
    
    
    # Post!
    # encode_and_post(file_list, parfiles)

if __name__ == '__main__':
    main()