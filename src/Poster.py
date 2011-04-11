import threading, Queue
import sys
import os
import nntplib
from binascii import crc32
import yenc
import StringIO
from email.mime.text import MIMEText

locations = {}
totalFiles = 0
fingerprint = ""
jobs = Queue.Queue()
articles = []
stop_threads = False
debug = False

#
# This is called from the main function
# It spawns the threads, fills up the queue with work items that the threads will use
# And then waits for the threads to finish
# This could use some more try:except code...
#
def post(args, config, fprint, loc):	
	global locations, totalFiles, fingerprint
	locations = loc
	fingerprint = fprint
	totalFiles = len(os.listdir(locations['path']+locations['workingDirectory']))

	print('Posting...')
	if(debug): print(locations)
	
	print('Connecting...')
	
	threads = []
	print "Starting {0} threads".format(config['connections'])
	# Creating threads
	for i in xrange(config['connections']):
		t = postThread(config, totalFiles)
		t.daemon = True
		threads.append(t)
		t.start()
	
	# Queueing Files
	for filename in os.listdir(locations['path']+locations['workingDirectory']):
		temp = config.copy()
		temp['filename'] = filename
		jobs.put(temp)
		
	while len(threads) > 0:
		try:
			# Join all threads using a timeout so it doesn't block
			# Filter out threads which have been joined or are None
			threads = [t.join(1) for t in threads if t is not None and t.isAlive()]
		except KeyboardInterrupt:
			print "Ctrl-c received! Sending kill to threads..."
			
			# Ugliest hack in the book!
			global stop_threads
			stop_threads = True
			
			raise
	
	jobs.join()
	
	return articles
	
#
# Main thread class - based on threading.Thread
# This class is cloned/used as a thread template to spawn those threads.
# The class has a run function that gets a job out of the jobs queue
# And lets the queue object know when it has finished.
#
class postThread(threading.Thread):
	def __init__(self, config, totalFiles):
		threading.Thread.__init__(self)
		
	def run(self):
		while not stop_threads:
			try:
				config = jobs.get(True,1)
				
				if not stop_threads:
					conn = nntplib.NNTP(config['hostname'], config['port'], config['username'], config['password'])
					fileArticles = {}
			
					curFile = os.listdir(locations['path']+locations['workingDirectory']).index(config['filename'])+1
					filePath = locations['path']+locations['workingDirectory']+os.sep+config['filename']
			
					size = os.stat(filePath).st_size
			
					#print('Total Size: '+str(size))
					blockSize = 128 * 11000 # Bytes per line * Number of Lines
			
					parts = (size/blockSize) + (size % blockSize != 0)
	
					file_in = open(filePath,'r')
					crc = self.calc_crc(filePath)
			
					for part in range(1,parts+1):
						print('{'+self.name+'} File ['+str(curFile)+'/'+str(totalFiles)+'] - "'+config['filename']+'" - Posting Part '+str(part)+'/'+str(parts))
						pstart = blockSize*(part - 1) + 1
						pend = pstart+blockSize - 1
						if(pend > size):
							pend = size
						psize = pend - pstart + 1
		
						if(debug): print('Start: '+str(pstart))
						if(debug): print('End: '+str(pend))
						if(debug): print('Part Size: '+str(psize))
		
						if(part != 1):
							if(debug): print('Seeking to: '+str(pstart-1))
							file_in.seek(pstart-1, os.SEEK_SET)
			
						temp_out = StringIO.StringIO()
		
						if(parts == 1):
							if(debug): print('Single Start')
							temp_out.write("=ybegin line=%d size=%d name=%s\r\n" % (128, size, config['filename']) )
						else:
							if(debug): print('Multi Start')
							temp_out.write("=ybegin part=%d total=%d line=%d size=%d name=%s\r\n" % (part, parts, 128, size, config['filename']) )
							temp_out.write("=ypart begin=%d end=%d\r\n" % (pstart, pend) )
		
						encoder = yenc.Encoder(temp_out) # When this object is recreated it will close out the last 'temp_out'
						encoder.feed(file_in.read(psize))
						encoder.terminate()
						encoder.flush()
		
						if(parts == 1):
							if(debug): print('Single End')
							temp_out.write("=yend size=%d crc32=%s\r\n" % (psize, crc.upper()))
						else:
							pcrc = encoder.getCrc32()
							temp_out.write("=yend size=%d part=%d pcrc32=%s" % (psize, part, pcrc))
						
							if(part == parts):
								temp_out.write(" crc32=%s\r\n" % (crc.upper()))
							else:
								temp_out.write("\r\n")
				
							if(debug): print('Multi End - CRC: '+crc.upper()+' - PCRC: '+pcrc)
				
						subject = ""
						if(config['subject']):
							subject += config['subject']
						else:
							subject += locations['tld']
						if(config['fingerprint']): subject += '['+fingerprint+'] '
						subject += '['+str(curFile)+'/'+str(totalFiles)+'] - "'+config['filename']+'" yEnc ('+str(part)+'/'+str(parts)+')'	

						msg = MIMEText(temp_out.getvalue())
						msg['Subject'] = subject
						if(debug): print('Subject: '+msg['Subject'])
						msg['From'] = '<'+config['name']+'> '+config['email']
						msg.add_header('Newsgroups', config['groups'])
						msg.add_header('X-Newspost', 'Py-Post')
		
						if(parts == 1):
							fh = open(filePath, 'w');
							fh.write(msg.as_string());
							fh.close();

						post = StringIO.StringIO()
						post.write(msg.as_string())
						post.seek(0)
		
						resp = conn.post(post)
						post.close()
		
						fileArticles[part] = {psize:resp.split(' ')[1][1:-1]}
		
					file_in.close()
					conn.quit()
			
					global articles
					articles.append({
						'subject': subject,
						'articles': fileArticles
					})

				jobs.task_done()
			except Queue.Empty:
				break	# No more items in the queue
			except:
				self.kill_received = True				
				print "Something broke in the Thread!", sys.exc_info()[0]
				raise
				break
			
	def calc_crc(self,fileName):
		prev = 0
		for eachLine in open(fileName, 'rb'):
			prev = crc32(eachLine, prev)
		return "%X"%(prev & 0xFFFFFFFF)
