import objc
import Foundation 
import QTKit
import sys

#get args
filename = sys.argv[1] #or whatever

m_in = QTKit.QTMovie.movieWithFile_(filename)
e = None
m_out1 = QTKit.QTMovie.movie()
m_out2 = QTKit.QTMovie.movie()

dura = m_in.duration()
start = m_in.currentTime()
t_range = QTKit.QTMakeTimeRange(start,dura)

m_out1.setAttribute_forKey_(True, QTKit.QTMovieEditableAttribute)
m_out2.setAttribute_forKey_(True, QTKit.QTMovieEditableAttribute)

#first add sound
soundtrack = m_in.tracksOfMediaType_(QTKit.QTMediaTypeSound)[0]

m_out1.insertSegmentOfTrack_timeRange_atTime_(soundtrack, t_range, start)
m_out2.insertSegmentOfTrack_timeRange_atTime_(soundtrack, t_range, start)

#then add split video
video_tracks = m_in.tracksOfMediaType_(QTKit.QTMediaTypeVideo)

m_out1.insertSegmentOfTrack_timeRange_atTime_(video_tracks[0], t_range, start)
m_out2.insertSegmentOfTrack_timeRange_atTime_(video_tracks[1], t_range, start)

#then write out to files
d = Foundation.NSMutableDictionary.dictionary()
d['QTMovieFlatten'] = True

m_out1.writeToFile_withAttributes_(filename + '0.mov', d)
m_out2.writeToFile_withAttributes_(filename + '1.mov', d)

#done!