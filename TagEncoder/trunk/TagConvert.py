from tagger import *
import cjkcodecs.aliases
from cjkcodecs import *
from encodings import aliases

import os

def strip_mod(list):
    return map(lambda x: x.split(".")[-1], list)

DEBUG_ENC = ['gb2312', 'big5_hkscs2001', 'utf_8', 'iso8859-1']
FALLBACK_ENC = 'iso8859-1'

# class to deal with MP3 files' tag encodings

class EncodedID3:
    id3 = None
    
    conv_encodings = {}
    converted = {}
    original =  {} 
    filename = None
    encodings = []
    version = 0
    id3v1 = None
    id3v2 = None
    
    def __init__(self, filename, possibleEncodings = DEBUG_ENC):
    
        self.filename = filename
    
        self.converted = {'artist':'', 'album':'', 'title':'', 
            'track':'', 'year':''}
        self.original = {'artist':'', 'album':'', 'title':'', 
            'track':'', 'year':''}
    
        if self.extract_id3v2(filename):
            self.version = self.id3v2.version
        elif self.extract_id3v1(filename):
            self.version = 1
        else:
            self.original = {'artist': '', 
                'title':os.path.basename(str(filename)), 
                'album':'', 'track':'0', 'year':'2000'}
            self.version = 0
        
        # convert fields
        conv, conv_enc = self.convert_fields(self.original, possibleEncodings)
        self.converted = conv
        self.conv_encodings = conv_enc
        self.encodings = possibleEncodings
        
    def __del__(self):
        if self.id3v2:
            del self.id3v2
        if self.id3v1:
            del self.id3v1
        
    def commit_to_file(self, filename):
        if self.version > 2:
            self.id3v2.commit_to_file(filename)
        elif self.version in [0, 1]:
            # make a id3v2 version of the file and commit our fields
            self.id3v2 = ID3v2(self.filename)

        if self.version > 2.2 or self.version in [0, 1]:        
            artist = self.id3v2.new_frame(fid = 'TPE1')
            artist.set_text(self.converted['artist'])
            title = self.id3v2.new_frame(fid = 'TIT2')
            title.set_text(self.converted['title'])
            album = self.id3v2.new_frame(fid = 'TALB')
            album.set_text(self.converted['album'])
            track = self.id3v2.new_frame(fid = 'TRCK')
            track.set_text(self.converted['track'])
            year = self.id3v2.new_frame(fid = 'TYER')
            year.set_text(self.converted['year'])
        elif self.version == 2.2:
            artist = self.id3v2.new_frame(fid = 'TP1')
            artist.set_text(self.converted['artist'])
            title = self.id3v2.new_frame(fid = 'TT2')
            title.set_text(self.converted['title'])
            album = self.id3v2.new_frame(fid = 'TAL')
            album.set_text(self.converted['album'])
            track = self.id3v2.new_frame(fid = 'TRK')
            track.set_text(self.converted['track'])
            year = self.id3v2.new_frame(fid = 'TYE')
            year.set_text(self.converted['year'])
            
        self.id3v2.frames += [artist, title, album, track, year]
        self.id3v2.commit_to_file(filename)
        
        if self.version in [0, 1]:
            del self.id3v2
            self.id3v2 = None
        
    def extract_id3v1(self, filename):
        try:
            self.id3v1 = ID3v1(filename)
        except ID3Exception, e:
            print "No ID3v1 Tags Found"
            return False
            
        if not self.id3v1.tag_exists():
            print "No ID3v1 Tags Found"
            return False
        else:
            self.original = {'artist': self.id3v1.artist,
                             'title': self.id3v1.songname,
                             'album': self.id3v1.album,
                             'track': str(self.id3v1.track),
                             'year': self.id3v1.year}
            return True

        
    def extract_id3v2(self, filename):
        try:
            self.id3v2 = ID3v2(filename)
        except ID3Exception, e:
            print "No ID3v2 Tags Found"
            return False
            
        if not self.id3v2.tag_exists():
            print "No ID3v2 Tags Found"
            del self.id3v2
            self.id3v2 = None
            return False
        else:
            frames = self.id3v2.frames
            if self.id3v2.version < 2.3:
                self.extract_id3v2_2(self.id3v2)
            else:
                self.extract_id3v2_3(self.id3v2)
            return True
    
    def extract_id3v2_2(self, id3):
        frames = id3.frames
        for frame in frames:
            if frame.fid == 'TP1':
                self.original['artist'] = frame.strings[0]
            if frame.fid == 'TT2':
                self.original['title'] = frame.strings[0]            
            if frame.fid == 'TAL':
                self.original['album'] = frame.strings[0]
            if frame.fid == 'TRK':
                self.original['track'] = frame.strings[0]
            if frame.fid == 'TYE':
                self.original['year'] = frame.strings[0]                
            
    def extract_id3v2_3(self, id3):
        frames = id3.frames
        for frame in frames:
            if frame.fid == 'TPE1':
                self.original['artist'] = frame.strings[0]
            if frame.fid == 'TIT2':
                self.original['title'] = frame.strings[0] 
            if frame.fid == 'TALB':
                self.original['album'] = frame.strings[0]
            if frame.fid == 'TRCK':
                self.original['track'] = frame.strings[0]
            if frame.fid == 'TYER':
                self.original['year'] = frame.strings[0]            
                    
    def convert_field(self, fieldname, value, encodings):
        result = u''
        enc_used = ''

        for enc in encodings:
            try:
                try:
                    result = value.decode(enc)
                except AttributeError:
                    result = value.encode('iso8859').decode(enc)
                enc_used = enc
                break
            except UnicodeDecodeError, e:
                print "error decoding %s: %s" % (fieldname, str(e))
                pass

        if result:
            return result, enc_used
        else:
            return value, None
                    
    def convert_fields(self, toconvert, encodings):
        converted = {}
        conv_encodings = {}
        
        for k, v in toconvert.items():
            result, enc_used = self.convert_field(k, v, encodings)
            converted[k] = result
            conv_encodings[k] = enc_used

        return converted, conv_encodings
        