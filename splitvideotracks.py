import objc
import Foundation 
import QTKit
import sys

#get args
filename = sys.argv[1] #or whatever

#m_in is our source movie
m_in = QTKit.QTMovie.movieWithFile_(filename)
e = None

#need number of video tracks
video_tracks = m_in.tracksOfMediaType_(QTKit.QTMediaTypeVideo)

#m_outs are our destinations, zip them with their track here
m_out = [(QTKit.QTMovie.movie(),v) for v in video_tracks]

#need the time points to copy to the new movies - can't just add tracks due to QTKit limitations
dura = m_in.duration()
start = m_in.currentTime()
t_range = QTKit.QTMakeTimeRange(start,dura)

#get soundtrack ahead of time, as it's the same for all of them
soundtrack = m_in.tracksOfMediaType_(QTKit.QTMediaTypeSound)[0]

#Define mode to write out to files
d = Foundation.NSMutableDictionary.dictionary()
d['QTMovieFlatten'] = True

#iterate through movies, making writable (QTKit oddness), adding soundtrack, videotrack, write out to disk
index = 0
for m in m_out:
	m[0].setAttribute_forKey_(True, QTKit.QTMovieEditableAttribute)
	m[0].insertSegmentOfTrack_timeRange_atTime_(soundtrack, t_range, start)
	m[0].insertSegmentOfTrack_timeRange_atTime_(m[1], t_range, start)
	m[0].writeToFile_withAttributes_(filename + str(index), d)
	index = index + 1
#done!
