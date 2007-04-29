from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import *
from AppKit import *

from tagger import *
from tagger.constants import *
from tagger.exceptions import *

import os, glob, types
import encodings

try:
    import cjkcodecs.aliases
    from cjkcodecs import *
except:
    pass
    
from encodings import aliases


NibClassBuilder.extractClasses("MusicTagger")

"""
TODO: have to deal properly with mixed encodings, like TRACK being one
      encoding and title's being another.

How to build:

python buildapp.py --standalone --package encodings build
"""

def uniq(list):
	last = None
	list.sort()
	result = []
	for i in list:
		if i != last:
			result.append(i)
			last = i

	return result

def strip_mod(list):
	return map(lambda x: x.split(".")[-1], list)

class PrefModel:

	encodingTable = []
	availableEncodings = strip_mod(uniq(aliases.aliases.values()))
	defaultEncodings = ['latin_1', 'utf_16', 'utf_16_be', 'utf_8',
						'big5', 'gb2312']
	enabledEncodings = []
	locationHistory = []

	def __init__(self):
		open('/tmp/debug','w').write(str(aliases.aliases.values()))
		
		for e in self.availableEncodings:
			if e in self.defaultEncodings:
				self.encodingTable.append({'PrefEncEnable':1,
										   'PrefEncName':e})
				self.enabledEncodings.append(e)
			else:
				self.encodingTable.append({'PrefEncEnable':0,
										   'PrefEncName':e})

	def addLocation(self, name):
		self.locationHistory.insert(0, name)

	def updateEnabledEncodings(self):
		self.enabledEncodings = []
		for e in self.encodingTable:
			if e['PrefEncEnable']:
				self.enabledEncodings.append(e['PrefEncName'])

	# implementations for combo box (location history)

	def comboBox_objectValueForItemAtIndex_(self, aBox, rowIndex):
		if rowIndex < len(self.locationHistory):
			return self.locationHistory[rowIndex]
		else:
			return ""

	def numberOfItemsInComboBox_(self, aBox):
		return len(self.locationHistory)

	

class MTPrefController(NibClassBuilder.AutoBaseClass):
	# prefEncTable
	# prefPanel
	# tagTable

	def awakeFromNib(self):
		self.prefEncTable.setTarget_(self)
		self.prefEncTable.window().setDelegate_(self)
		self.updateEncodingMenu()
		
	def closePref_(self, caller):
		self.prefPanel.close()

	def tableView_objectValueForTableColumn_row_(self,
												 aTableView,
												 aTableColumn,
												 rowIndex):
		col = aTableColumn.identifier()
		return prefs.encodingTable[rowIndex][col]
	
	def numberOfRowsInTableView_(self, tableview):
		return len(prefs.encodingTable)

	def tableView_shouldSelectRow_(self, aTableView, rowIndex):
		return True
		
	def tableView_shouldEditTableColumn_row_(self, aTableView,
											 aTableColumn, rowIndex):
		if aTableColumn.identifier() == "PrefEncEnable":
			if prefs.encodingTable[rowIndex]['PrefEncName'] not in \
				   prefs.defaultEncodings:
				return True
			
		return False

	def tableView_setObjectValue_forTableColumn_row_(self, aTableView,
													 anObject,
													 aTableColumn,
													 rowIndex):

		if aTableColumn.identifier() == "PrefEncEnable":
			prefs.encodingTable[rowIndex]["PrefEncEnable"] = anObject
			
		prefs.updateEnabledEncodings()
		self.updateEncodingMenu()

	def updateEncodingMenu(self):
		for col in self.tagTable.tableColumns():
			if col.identifier() == "MTColEnc":
				cell = col.dataCell()
				cell.removeAllItems()
				for e in prefs.enabledEncodings:
					cell.addItemWithTitle_(e)


class MTModel(NibClassBuilder.AutoBaseClass):

	records = []
	ID3V2_FIELDS = {'TIT2':'MTColTitle', 'TPE1':'MTColArtist',
					'TALB':'MTColAlbum', 'TRCK':'MTColTrack'}
	ID3V2_2_FIELDS = {'TT2':'MTColTitle', 'TP1':'MTColArtist',
					  'TAL':'MTColAlbum', 'TRK':'MRColTrack'}
	ID3V1_ID3V2 = {'songname': 'TIT2', 'album':'TALB', 'artist':'TPE1',
				   'year':'TYER', 'track':'TRCK'}
	
	def init(self):
		return self

	def len(self):
		return len(self.records)

	def get(self, row, col):
		if row >= len(self.records):
			return None
		else:
			return self.records[row][col]
		
	def set(self, row, col, value):
		if row < len(self.records):
			self.records[row][col] = value
		
	def clear(self):
		self.records = []
		
	def initRow(self):
		return {'MTColTrack':'', 
				'MTColTitle':'', 
				'MTColArtist':'', 
				'MTColAlbum':'', 
				'MTColEnc':'', 
				'MTColConvert':'',
				'id3v2':None, 
				'id3v1':None}
		
	def addFile(self, filename, tagv2, tagv1):
		d = self.initRow()
		enc = 'latin_1'
		
		# if there aren't any id3v2, we create one and populate with
		# ID3v1 tags
		if not tagv2 and tagv1:
			tagv2 = ID3v2(filename, ID3_FILE_NEW, version=2.4)
			for v1, v2 in self.ID3V1_ID3V2.items():
				if tagv1._tag.has_key(v1):
					"""
					if type(tagv1._tag[v1]) == types.StringType:
						print "added %s -> %s: %s" % \
							  (v1, v2, \
						 tagv1._tag[v1].decode('latin_1').encode('utf_8'))
					else:
						print "added %s -> %s: %d" % (v1, v2, tagv1._tag[v1])
					"""
						
					newframe = tagv2.new_frame(fid=v2)
					newframe.encoding = 'latin_1'
					newframe.strings = [str(tagv1._tag[v1])]
					tagv2.frames.append(newframe)

		if not tagv2:
			# we don't have any information to populate the tags
			self.records.append(d)
			return
		
		# for all the fields we need to convert, we check if it is in
		# latin encoding. if it is, then we need to decode it,
		# otherwise, pyid3v2 should have turned
		# it into unicode objects

		for f in tagv2.frames:
			if tagv2.version == 2.2:
				fields = self.ID3V2_2_FIELDS
			else:
				fields = self.ID3V2_FIELDS
				
			if fields.has_key(f.fid):
				col =fields[f.fid]
				# need to convert things that are not UTF*
				if f.encoding == 'latin_1':
					d[col] = f.strings[0].decode('latin_1')
				else:
					if f.encoding not in ['utf_16be', 'utf_16', 'utf_8']:
						print "WARNING: unknown encoding: %d" % f.encoding	
					d[col] = f.strings[0]
					enc = f.encoding
		
		# keep references for these so we can commit changes
		d['id3v2'] = tagv2
		d['id3v1'] = tagv1
		try:
			d['MTColEnc'] = enc
		except ValueError:
			print [enc]
			raise
		self.records.append(d)

	def convert(self, row, enc):
		tagv2 = self.records[row]['id3v2']
		if tagv2 == None:
			return
				
		try:
			# here we try to convert everything to the desired encoding
			for f in tagv2.frames:
				if tagv2.version == 2.2:
					fields = self.ID3V2_2_FIELDS
				else:
					fields = self.ID3V2_FIELDS
				if fields.has_key(f.fid):
					col = fields[f.fid]
					try:
						self.records[row][col] = f.strings[0].decode(enc)
					except AttributeError:
						self.records[row][col] = f.strings[0]
		except UnicodeDecodeError, e:
			print "TODO: print an error dialog box and restore values"
			print "UnicodeDecodeError:", [f.strings[0]], enc, f.fid
			print f.strings[0].decode(enc).encode('utf-8')
			print e
			for f in tagv2.frames:
				if tagv2.version == 2.2:
					fields = self.ID3V2_2_FIELDS
				else:
					fields = self.ID3V2_FIELDS
				
				if fields.has_key(f.fid):
					col = fields[f.fid]
					if f.encoding == 'latin_1':
						self.records[row][col] = f.strings[0].decode('latin_1')	
					else:
						self.records[row][col] = f.strings[0]
					
			
			return


	def load_(self, dirname):
		self.clear()
		for filename in glob.glob(os.path.join(dirname, "*.mp3")):
			try:
				tagv2 = id3v2.ID3v2(filename, ID3_FILE_MODIFY)
			except ID3HeaderInvalidException:
				print filename.encode("utf_8"), "has no ID3v2 tag"
				tagv2 = None

			try:
				tagv1 = ID3v1(filename)
			except ID3HeaderInvalidException:
				tagv1 = None
			
			self.addFile(filename, tagv2, tagv1)
			
	def save_(self, row):
		tagv2 = self.records[row]['id3v2']
		if tagv2.version == 2.2:
			fields = self.ID3V2_2_FIELDS
		else:
			fields = self.ID3V2_FIELDS
			
		for fid, col in fields.items():
			i = 0
			found = 0
			while i < len(tagv2.frames):
				if tagv2.frames[i].fid == fid:
					#print col, fid, self.records[row][col].encode('utf_8')
					try:
						unicode(self.records[row][col]).encode('latin_1')
						tagv2.frames[i].encoding = 'latin_1'
					except UnicodeEncodeError:
						tagv2.frames[i].encoding = 'utf_16'
						
					tagv2.frames[i].strings = [unicode(self.records[row][col])]
					found = 1
					break
				i+=1
				
			if not found:
				newframe = tagv2.new_frame(fid=fid)
				try:
					unicode(self.records[row][col]).encode('latin_1')
					newframe.encoding = 'latin_1'
				except UnicodeEncodeError:
					newframe.encoding = 'utf_16'
					
				newframe.strings = [unicode(self.records[row][col])]
				tagv2.frames.append(newframe)

		tagv2.commit()

class MTController(NibClassBuilder.AutoBaseClass):
	# connected outlets
	#   tableView
	#   window
	#   model
	#   prefController
	
	def awakeFromNib(self):
		self.tableView.setTarget_(self)
		self.tableView.window().setDelegate_(self)
	
	def tableView_objectValueForTableColumn_row_(self, 
		aTableView, aTableColumn, rowIndex):
		col = aTableColumn.identifier()
		if col == "MTColEnc":
			enc = self.model.get(rowIndex, col)
			try:
				return prefs.enabledEncodings.index(enc)
			except ValueError:
				# if the encoding isn't in the list anymore, we reset
				# to a first encoding :(
				self.model.set(rowIndex, col, prefs.enabledEncodings[0])
				return 0
		else:
			return self.model.get(rowIndex, col)
		
	def numberOfRowsInTableView_(self, tableview):
		if self.model:
			return self.model.len()
		else:
			return 0

	def convertSelected_(self, sender):
		selectedRows = self.tableView.selectedRowIndexes()
		idx = selectedRows.firstIndex()
		while idx != NSNotFound:
			idx = selectedRows.indexGreaterThanIndex_(idx)
			self.model.save_(i)

	def convertAll_(self, sender):
		rows = self.tableView.numberOfRows()
		for i in range(0, rows):
			self.model.save_(i)

	def load_(self, sender):
		opendialog = NSOpenPanel.openPanel()
		opendialog.setCanChooseDirectories_(True)
		opendialog.setCanChooseFiles_(False)
		result = opendialog.runModalForDirectory_file_types_(None, None, None)
		if result == 1:
			# pressed ok
			# update location combo box
			self.locationBox.insertItemWithObjectValue_atIndex_(opendialog.filenames()[0], 0)
			self.locationBox.selectItemAtIndex_(0)
			# load files in directory
			self.model.load_(opendialog.filenames()[0])
			# redraw table
			self.tableView.reloadData()
		elif result == 0:
			pass
		else:
			# load pressed?
			pass
		
	# delegate methods for mp3 table listing
	def tableView_setObjectValue_forTableColumn_row_(self, aTableView, anObject, aTableColumn, rowIndex):
		col = aTableColumn.identifier()
		if col == "MTColEnc":
			self.model.convert(rowIndex, prefs.enabledEncodings[anObject])
			self.model.set(rowIndex, col, prefs.enabledEncodings[anObject])
			self.tableView.reloadData()
		elif col == "MTColConvert":
			self.model.save_(rowIndex)
		else:
			self.model.set(rowIndex, col, anObject)
	
	def tableView_shouldSelectRow_(self, aTableView, rowIndex):
		return True		
		
	def tableView_shouldEditTableColumn_row_(self, aTableView,
											 aTableColumn, rowIndex):
		return True

	# delegate methods for location combo box
	def comboBoxSelectionDidChange_(self, notif):
		dirname = self.locationBox.objectValueOfSelectedItem()
		self.model.load_(dirname)
		self.tableView.reloadData()		
		

prefs = PrefModel()

if __name__ == "__main__":
	AppHelper.runEventLoop()
	
