#!/usr/bin/python
import os, subprocess
from optparse import OptionParser
import hashlib
import time
import Poster
import sys

# Global locations variable, this should not change throughout execution!
locations = {}

# Global fingerprint variable, this should not change throughout execution!
fingerprint = ""

debug = False

def _rarFiles(compressionLevel, volumeSize):
	print('Raring...');
	args = ['rar', 'a', '-ep1', '-v'+str(volumeSize),
			'-m'+str(compressionLevel),
			locations['path']+locations['workingDirectory']+os.sep+locations['tld'], locations['path']+locations['tld']];
	if(debug):
		print(args)
		subprocess.check_call(args, stdout=open(os.devnull,'w'))
	else:
		subprocess.check_call(args)
	return None

def _parFiles(percentage=10):
	print('Paring...');	
	args = ['par2', 'create', '-r'+str(percentage), '-s307200',
			locations['path']+locations['workingDirectory']+os.sep+'*.rar']
	if(debug):
		print(args);
		subprocess.check_call(args, stdout=open(os.devnull,'w'))
	else:
		subprocess.check_call(args);
	return None
	
def generateNZB(config,data):
	xml = ''
	
	xml += '<?xml version="1.0" encoding="iso-8859-1" ?>\n'
	xml += '<!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">\n'
	xml += '<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">\n'
	#xml += '\t<head>\n'
	#xml += '\t\t<meta type="title">Your File!</meta>\n'
	#xml += '\t\t<meta type="tag">Example</meta>\n'
	#xml += '\t</head>\n'
	
	for i in data:
		subj = i['subject'].replace('"', '&quot;')
		xml += '\t<file poster="'+config['name']+' &lt;'+config['email']+'&gt;" date="'+str(int(time.time()))+'" subject="'+subj+'">\n'
		xml += '\t\t<groups>\n'
		
		for group in config['groups'].rsplit(','):
			xml += '\t\t\t<group>'+group+'</group>\n'
		
		xml += '\t\t</groups>\n'
		xml += '\t\t<segments>\n'
		for pnum, data in i['articles'].iteritems():
			for psize, loc in data.iteritems():		
				xml += '\t\t\t<segment bytes="'+str(psize)+'" number="'+str(pnum)+'">'+loc+'</segment>\n'
		xml += '\t\t</segments>\n'
		xml += '\t</file>\n'
		
	xml += '</nzb>'
	
	fullPath = locations['path']+locations['workingDirectory']+os.sep+locations['tld']+'.nzb'
	file = open(fullPath, 'w')
	file.write(xml)
	file.close()
	
	print 'NZB Saved to: '+fullPath
	
	return None

def _addParserOptions(parser):
	# Adds options to the parser object that was passed in. 
	parser.add_option('-H', '--hostname', type='string', dest='hostname',
						help='hostname or IP of the news server')
	parser.add_option('-p', '--port', type='int', dest='port',
						help='port number on the news server', default='119')
	parser.add_option('-c', '--connections', type='int', dest='connections',
						help='max number of connections to the news server', default='10')
	parser.add_option('-u', '--username', type='string', dest='username',
						help='username on the news server')
	parser.add_option('-w', '--password', type='string', dest='password',
						help='password on the news server')
	parser.add_option('-f', '--email', type='string', dest='email',
						help='posting email address', default='poster@py-post.net')
	parser.add_option('-F', '--name', type='string', dest='name',
						help='posting name', default='Py-Post')
	parser.add_option('-g', '--groups', type='string', dest='groups',
						help='newsgroups to post to', default='alt.binaries.test')
	parser.add_option('-s', '--subject', type='string', dest='subject',
						help='subject')
	parser.add_option('-U', '--unique', action='store_true', dest='uniqueFingerprint',
						help='Do NOT prepend a unique upload fingerprint', default=False)
	parser.add_option('-n', '--nzb', action='store_false', dest='genNZB',
						help='Do NOT generate an nzb file', default=True)
	
	parser.add_option('-z', '--volume-size', type='string', dest='volumeSize',
						help='Rar Volume Size', default='15m')
	parser.add_option('-m', '--compression-level', type='int', dest='compressionLevel',
						help='Rar Compression Level', default='0')
	
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
					  help='be verbose', default=False)
	return None

def main(args):
	version = "Version: 0.5.0 <Apr 10, 2011>"
	
	usage = "\nAuthor: Robert Navarro <rnavarro@phiivo.com>\n"
	usage += version+"\n"
	usage += "%prog [options] SourceDirectory"

	# Instantiate our CLI Option/Argument parser
	parser = OptionParser(usage=usage, version=version)
	_addParserOptions(parser)
	# Parse the CLI Options/Argumets
	(options, args) = parser.parse_args()
	
	if len(args) != 1:
		parser.error("Incorrect Number of Arguments")
		
	if not os.path.isdir(args[0]):
		parser.error("We an only work with directories")
	
	# Split the given path into individual segments
	splits = args[0].rsplit(os.sep)
	
	# Initialize Path String
	path = ''
	
	# Grab the top level directory that we're working with
	# If there is a trailing slash, then we have to go back two in the array
	if(splits[-1] == ''):
		tld = splits[-2]
		for i in range(0, len(splits)-2):
			path += splits[i]+'/'
	# There is no trailing slash, add one....and only go back one in the array
	else:
		tld = splits[-1]
		for i in range(0, len(splits)-1):
			path += splits[i]+'/'
	
	# Create a unique fingerprint (Makes searching easier too!)
	global fingerprint
	fingerprint = hashlib.sha1(tld).hexdigest()[0:10]
	workingDirectory = '['+fingerprint+'] '+tld
	
	global locations
	locations = {'path':path, 'tld':tld, 'workingDirectory':workingDirectory}
	
	if not os.path.isdir(path+workingDirectory):
		os.mkdir(path+workingDirectory)
		
	subj = "\nSubject: "
	if(options.subject):
		subj += options.subject
	else:
		subj += locations['tld']
	if(options.uniqueFingerprint): subj += '['+fingerprint+'] '
	subj += '[X/Y] - '
	subj += '"'+locations['tld']+'.EXT"'
	subj += ' yEnc (X/Y)'
	
	print('Running rar!')
	_rarFiles(options.compressionLevel, options.volumeSize);
	print('Finished rar\n')
	
	print('Running Par!')
	_parFiles();
	print('Finished Par!\n')
	
	config = {
		'hostname': options.hostname,
		'port': options.port,
		'connections': options.connections,
		'username': options.username,
		'password': options.password,
		'email': options.email,
		'name': options.name,
		'groups': options.groups,
		'subject': options.subject,
		'fingerprint': options.uniqueFingerprint
	}
	print('Posting!')
	articles = Poster.post(args, config,fingerprint,locations)
	print('Done Posting!\n')
	
	print subj+"\n"
	
	print "Posted To: "+options.groups
	
	if options.genNZB:
		print('Generating NZB!')
		generateNZB(config, articles)

if __name__ == '__main__':
	main(sys.argv)
