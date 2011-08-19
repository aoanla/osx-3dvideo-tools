import objc
import Foundation
import QTKit
import math
import sys
from AppKit import *
from Quartz.CoreGraphics import *

filename = sys.argv[1] #first argument!
e = None

m_in = QTKit.QTMovie.movieWithFile_error_(filename,None)[0]

#some constants for repeated use later - frame cropping + rotating, really should pick up these from m_in dimensions.
rectL = CGRectMake(0,0,1920/2,1080)
rectR = CGRectMake(1920/2,0,1920,1080)
rot90 = CGAffineTransformMakeRotation(math.pi/2)
rot270 = CGAffineTransformMakeRotation(-1*math.pi/2)

#and our video out compression stuff
d = Foundation.NSMutableDictionary.dictionary()
d[u'QTAddImageCodecType'] = u'avc1'  
# u'avc1' is the right codec for H.264 AVC encoding, u'mp4v' for the bog standard MPEG-4.
d[u'QTAddImageCodecQuality'] = QTKit.codecHighQuality #or something? check where this is defined.

#and open our output movies and make them writable - should replace this with proper use of QTKit.QTMovie.withWritableFile_ stuff
# that is QTKit.QTMovie.alloc().initToWritablefile_error_(u'Left' + filename, e) kindathing (also means update is easy)
# can call updateMovieFile type call each iteration of frame adds..

#This is supposed to base the output files on writable files, but this fails horribly, apparently, to judge from the growing virtual memory use (which eventually
#  kills the program). The output movie also appears to have the wrong time base and doesn't play properly (blank frames)...
#  -- so: with the "addImage" etc bits uncommented so we actually write the movie files, we die from an allocation error around 50% through the movie encoding.
#         with it commented out (so we're just editing images and disposing of them), we die from an allocation error around 90% through the movie encoding.
#   Conclusion: something is leaking memory significantly (probably in image operations).
#   Solution: explicitly adding an NSAutoreleasePool for the loop removes the leak with movie writing commented out. This
# 		is because PyObjC only allocates an explicit NSAutoreleasePool for thread 1 - QTKit is multithreaded.
#  This solves the memory leak when writing to the movies, but the movies are still completely black video for the entire movie (which is also
#  twice as long as it should be). The duration issue is because we're getting the time base wrong? The blackness issue... need to test the output images separately.

m_left = QTKit.QTMovie.alloc().initToWritableFile_error_(u'Left' + filename, e)[0]
m_right = QTKit.QTMovie.alloc().initToWritableFile_error_(u'Right' + filename, e)[0]
#print m_left
#sys.exit(0)
m_left.setAttribute_forKey_(True, QTKit.QTMovieEditableAttribute)
m_right.setAttribute_forKey_(True, QTKit.QTMovieEditableAttribute)
#We might want to set the output movies to the same format as the input movie
#we *do* want to control the video stream compression (but this is done in addImage?)

#get the input movie duration for copy operations
dura = m_in.duration()
start = m_in.currentTime()
t_range = QTKit.QTMakeTimeRange(start,dura)

print QTKit.QTTimeIncrement(start, dura)

#and add the soundtrack to both of them
m_in_strack = m_in.tracksOfMediaType_(QTKit.QTMediaTypeSound)[0]
m_left.insertSegmentOfTrack_timeRange_atTime_(m_in_strack, t_range, start)
m_right.insertSegmentOfTrack_timeRange_atTime_(m_in_strack, t_range, start)

#
# And now to add the video frames.
m_in_vtrack = m_in.tracksOfMediaType_(QTKit.QTMediaTypeVideo)[0]
# can get sample durations from GetMovieNextInterestingTime to pull frames + their durations (as video samples)

#frame handling stuff 
#for some reason, we can't get CIImages from the movie properly in pyobjc
#so, we just get NSImages and manipulate

#while we can stepForward:

curtime = QTKit.QTMakeTime(99999,99) #fake number so doesn't match first while
newtime = m_in.currentTime()

#iterate through the video frames, splitting and rotating each, saving to the new movie files... until we reach the end
#QTKit's stepForward function doesn't tell you when you've hit the end, so you have to check for the time not advancing afterwards...
while (QTKit.QTTimeCompare(curtime,newtime) != Foundation.NSOrderedSame ):
	pool = NSAutoreleasePool.alloc().init()
	#update our curtime to the old newtime, as we're handling the new frame
	curtime_old = curtime
	curtime = newtime
	try: #try, as we might have malloc issues here, depending on if the frame exists or memory pressure
		cFrame = m_in.currentFrameImage()
		cRep = cFrame.representations()[0]
	except:
		print curtime_old, curtime
		print cFrame
		sys.exit(1)

	cImage = CIImage.alloc().initWithBitmapImageRep_(cRep)
	
	#now get our sub images - the two halves from the two mirrors (divide in two horizontally)
	cImageLeft = cImage.imageByCroppingToRect_(rectL)
	cImageRight = cImage.imageByCroppingToRect_(rectR)
	
	#and rotate them so they are oriented "horizontally"
	
	cImageLeftTrans = cImageLeft.imageByApplyingTransform_(rot90)
	cImageRightTrans = cImageRight.imageByApplyingTransform_(rot270)
	
	#finally, compress them back to NSImages - I don't think this method actually exists... need to
	# draw into an NSImageContext, I think (urgh)
	#	bImageLeftTrans = NSImage.alloc().imageFromCIImage_(cImageLeftTrans)
	#	bImageRightTrans = NSImage.alloc().imageFromCIImage_(cImageRightTrans)
	#sommat like: (fix names, and convert from Objective-C)
	repImageLeftTrans = NSCIImageRep.imageRepWithCIImage_(cImageLeftTrans)
	bImageLeftTrans = NSImage.alloc().initWithSize_(repImageLeftTrans.size())
	bImageLeftTrans.addRepresentation_(repImageLeftTrans)
	repImageRightTrans = NSCIImageRep.imageRepWithCIImage_(cImageRightTrans)
	bImageRightTrans = NSImage.alloc().initWithSize_(repImageRightTrans.size())
	bImageRightTrans.addRepresentation_(repImageRightTrans)
	
	print bImageRightTrans
	sys.exit(1)
	
	
	m_in.stepForward() #or whatever
	newtime = m_in.currentTime()
	
	#duration is now difference between the two - if it is 0 then we're at the end of the movie!
	frameDur = QTKit.QTTimeDecrement(newtime,curtime)
#	frameDuration = QTKit.QTTimeMakeDuration(curtime,frameDur)
	
	#so, write out our new frames:
	m_left.addImage_forDuration_withAttributes_(bImageLeftTrans,frameDur,d)
	m_right.addImage_forDuration_withAttributes_(bImageRightTrans,frameDur,d)
	m_left.setCurrentTime_(m_left.duration() )
	m_right.setCurrentTime_(m_right.duration() )
	
	m_left.updateMovieFile()
	m_right.updateMovieFile()
	
	del pool
#	cFrame.release()
	
#then write out to files - this actually generates smaller files than the original movie files used in the loop, presumably because we get interframe compression here.
d_out = Foundation.NSMutableDictionary.dictionary()
d_out['QTMovieFlatten'] = True

m_left.writeToFile_withAttributes_(u'Left_' + filename, d_out)
m_right.writeToFile_withAttributes_(u'Right_' + filename, d_out)

