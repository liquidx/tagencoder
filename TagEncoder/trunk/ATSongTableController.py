from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import *
from AppKit import *

from TagConvert import *
from tagger import *

import re
import struct
import traceback
import tempfile

EDITABLE_COLUMNS = ["track", "title", "album", "artist", 'year']

DRAG_TYPES = [NSFileContentsPboardType,
    NSHTMLPboardType, 
    NSPDFPboardType, 
    NSPICTPboardType, 
    NSFilenamesPboardType,
    NSPostScriptPboardType,
    NSRTFPboardType,
    NSStringPboardType,
    NSTabularTextPboardType,
    NSTIFFPboardType,
    NSURLPboardType,
    NSFilesPromisePboardType]

def pastetype(fileType):
    return 'CorePasteboardFlavorType 0x'+hex(str2ostype(fileType))[2:].upper()

def str2ostype(z):
    return reduce(lambda x, y: (x << 8) + y, map(ord, z))
    
def ostype2str(x):
    s = ''
    for i in range(4):
        s += chr((x >> (24 - i*8)) & 0xff)
    return s
    
def CarbonPromiseHFSFlavor(fileType, fileCreator, fdFlags, promisedFlavor):
    return struct.pack('IIHI', 
        str2ostype(fileType), 
        str2ostype(fileCreator), 
        fdFlags, 
        str2ostype(promisedFlavor))
        
class ATSongTableController(NibClassBuilder.AutoBaseClass):
    
    tableData = []
    convertedImage = None
    draggedRows = None
    tempfiles = []
    
    # IBOutlets
    # ---------
    # window
    # tableView 
    # mainController
    
    def awakeFromNib(self):
        self.tableView.registerForDraggedTypes_(DRAG_TYPES)
        """
        self.convertedImage = NSImage.imageNamed_("Converted")
        self.convertedImage.setScalesWhenResized_(True)
        self.convertedImage.setSize_(NSMakeSize(12, 12))
        """
        self.tableView.setDataSource_(self)
        
        # get notification of application quitting so we can clean up
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, 'applicationWillTerminate:', NSApplicationWillTerminateNotification, None)   
                        
    def applicationWillTerminate_(self, aNotification):
        # clean up
        for t in self.tempfiles:
            os.unlink(t)
        
    """
    Called by ATSongTableView
    """
    def encodingUsedForRow_column_(self, row, col):
        colname = self.tableView.tableColumns()[col].identifier()
        if colname in EDITABLE_COLUMNS:
            return self.tableData[row].conv_encodings[colname]
        else:
            return None
            
    def changeEncoding_(self, sender):
        objectData = sender.representedObject()
        encoding = objectData[0]
        row = objectData[1]
        col = objectData[2]
        colname = self.tableView.tableColumns()[col].identifier()
        if colname in EDITABLE_COLUMNS:
            result, enc_used = self.tableData[row].convert_field(colname, \
                self.tableData[row].original[colname], \
                [encoding])
            if enc_used != None:
                self.tableData[row].converted[colname] = result
                self.tableData[row].conv_encodings[colname] = enc_used
                self.tableData[row].commit_to_file(self.tempfiles[row])
                self.tableView.reloadData()

    # - (int)numberOfRowsInTableView:(NSTableView *)aTableView
    def numberOfRowsInTableView_(self, aTableView):
        return len(self.tableData)


    # - (void)tableView:(NSTableView *)aTableView
    #    setObjectValue:anObject
    #    forTableColumn:(NSTableColumn *)aTableColumn
    #               row:(int)rowIndex
    def tableView_setObjectValue_forTableColumn_row_(self, aTableView, 
        anObject, aTableColumn, rowIndex):
        columnName = aTableColumn.identifier()
        if columnName in EDITABLE_COLUMNS:
            self.tableData[rowIndex].converted[columnName] = anObject
            os.unlink(self.tempfiles[rowIndex])
            self.tableData[rowIndex].commit_to_file(self.tempfiles[rowIndex])
        
        
    # - (id)tableView:(NSTableView *)aTableView
    # objectValueForTableColumn:(NSTableColumn *)aTableColumn
    #             row:(int)rowIndex
    def tableView_objectValueForTableColumn_row_(self, aTableView, 
        aTableColumn, row):
        
        columnName = aTableColumn.identifier()

        # got column header, now grab the right field:
        if columnName in EDITABLE_COLUMNS:
            return self.tableData[row].converted[columnName]
        elif columnName == 'fname':
            return os.path.basename(self.tableData[row].filename)
        else:
            return None

    def deleteRows(self, rowIndexes):
        maxCount = rowIndexes.count()
        inRange = NSMakeRange(0, len(self.tableData) + 1)
        
        print rowIndexes, inRange
            
        (r, indices, n) =  rowIndexes.getIndexes_maxCount_inIndexRange_( \
            maxCount, inRange)
            
        print "deleteRows - deleting"
        for i in indices:
            self.tableData[i] = None
            os.unlink(self.tempfiles[i])
            self.tempfiles[i] = None
        
        print "deleteRows - filter"
        self.tableData = filter(lambda x: x != None, self.tableData)
        self.tempfiles = filter(lambda x: x != None, self.tempfiles)
        self.tableView.reloadData()

    """
    # - (void)tableView:(NSTableView *)aTableView 
    #   willDisplayCell:(id)aCell 
    #    forTableColumn:(NSTableColumn *)aTableColumn 
    #               row:(int)rowIndex
    
    def tableView_willDisplayCell_forTableColumn_row_(self, aTableView, 
        aCell, aTableColumn, rowIndex):
        pass
            #aCell.setImage_(self.convertedImage)
    """     

            
    """
    - (NSDragOperation)tableView:(NSTableView*)tv
				validateDrop:(id <NSDraggingInfo>)info
				 proposedRow:(int)row
	   proposedDropOperation:(NSTableViewDropOperation)op
	"""
    def tableView_validateDrop_proposedRow_proposedDropOperation_(self, 
            tv, info, row, op):
        pasteboardTypes = info.draggingPasteboard().types()
        
        if tv == info.draggingSource(): # eg local
            return NSDragOperationNone
            
        if pasteboardTypes.containsObject_(NSFilenamesPboardType):
            return NSDragOperationCopy
        else:
            return NSDragOperationNone
        
        
    def printPasteboard(self, pboard):
        pasteboardTypes = pboard.types()
        
        for ptype in pasteboardTypes:
            if re.search('CorePasteboardFlavorType', ptype):
                match = re.search('CorePasteboardFlavorType ([0-9A-Fx]+)',
                        ptype)
                print 'ATSTCtrl: Pasteboard:', ostype2str(int(match.group(1)[2:], 16)),
                print '(', ptype, ')'
                try:
                    data = pboard.dataForType_(ptype)
                    dataBytes = data.bytes()
                    print len(dataBytes)
                    print [dataBytes[0:len(dataBytes)]]
                except:
                    traceback.print_exc()
            else:
                print 'Pasteboard:', ptype

        
    #- (BOOL)tableView:(NSTableView*)tv
	#       acceptDrop:(id <NSDraggingInfo>)info
    #		       row:(int)row
	#     ropOperation:(NSTableViewDropOperation)op
    def tableView_acceptDrop_row_dropOperation_(self, tv, info, row, op):
    
        pboard = info.draggingPasteboard()
        pasteboardTypes = pboard.types()
        if pasteboardTypes.containsObject_(NSFilenamesPboardType):
            # get all the files dragged
            filenames = pboard.propertyListForType_(NSFilenamesPboardType)
            
            # try loading their ID3 tags
            for f in filenames:
                prefs = self.mainController.prefsControl
                ftag = EncodedID3(f, prefs.enabledEncodings)
                self.tableData.append(ftag)
                tempfd, tempname = tempfile.mkstemp(suffix = ".mp3")
                os.close(tempfd)
                ftag.commit_to_file(tempname)
                self.tempfiles.append(tempname)
                print f.encode('utf_8')
                
            # if ok, force view to refresh
            self.tableView.reloadData()
    
        return False


    # - (BOOL)tableView:(NSTableView *)tableView 
    #         writeRows:(NSArray *)rows 
    #      toPasteboard:(NSPasteboard *)pboard
    def tableView_writeRows_toPasteboard_(self, tableView, rows, pboard):
        print "tableView_writeRows_toPasteboard:", rows
        pboard.declareTypes_owner_([NSFilenamesPboardType], self)
        
        # make new files for dragging
        filenames = map(lambda x: self.tempfiles[x], rows)
        pboard.setPropertyList_forType_(filenames, NSFilenamesPboardType)
        return True
    
    def pasteboard_provideDataForType_(self, sender, ptype):
        print "accept type:", ptype
        if ptype == NSFilenamesPboardType:
            filenames = []
            for row in self.draggedRows:
                filenames.append(self.tableData[row].filename)
            sender.setPropertyList_forType_(filenames, NSFilenamesPboardType)
        elif ptype == NSFilesPromisePboardType:
            pass
      
    """
    # - (NSArray *)namesOfPromisedFilesDroppedAtDestination:(NSURL *)dropDestination
    def namesOfPromisedFilesDroppedAtDestination_(self, destination):
        print "nameOfPromisedFilesDroppedAtDestination", destination
        filenames = []
        for row in self.draggedRows:
            filenames.append(self.tableData[row].filename)
        return filenames

    # - (BOOL)tableView:(NSTableView *)tableView 
    #         writeRows:(NSArray *)rows 
    #      toPasteboard:(NSPasteboard *)pboard
    def tableView_writeRows_toPasteboard_(self, tableView, rows, pboard):
        print "tableView_writeRows_toPasteboard:", rows
        self.draggedRows = rows
        rectRow = tableView.rectOfRow_(tableView.selectedRow())
        rectRow.size.height = 16
        rectRow.size.width = 16
        
              # set promised files to drag
        tableView.dragPromisedFilesOfTypes_fromRect_source_slideBack_event_(
            ["mp3"], # filetypes
            rectRow, # fromRect
            self, # source
            True, # slideback
            None)
            
        return False        

    """        


# notes: finder dragged file has these types
#CorePasteboardFlavorType 0x6E6F6465 (code)
#CorePasteboardFlavorType 0x68667320 (hfs )
#CorePasteboardFlavorType 0x6675726C (furl)
#NSFilenamesPboardType
#CorePasteboardFlavorType 0x626E6368 (bnch)
#CorePasteboardFlavorType 0xC4706431 (?pd1)

# notes: drag from itunes
#CorePasteboardFlavorType 0x70686673 (phfs)
#Apple files promise pasteboard type
#CorePasteboardFlavorType 0x72576D31 (rWm1)
#CorePasteboardFlavorType 0x4A524653 (JRFS)
#CorePasteboardFlavorType 0x4870666C (Hpfl)
#CorePasteboardFlavorType 0x44736964 (Dsid)
#CorePasteboardFlavorType 0x4F69646C (Oidl)
#CorePasteboardFlavorType 0x6974756E (itun)

# notes: url drag from safari
#Apple files promise pasteboard type
#BookmarkDictionaryListPboardType
#BookmarkStatisticsPBoardType
#NSStringPboardType
#WebURLsWithTitlesPboardType
#Apple URL pasteboard type
#CorePasteboardFlavorType 0x75726C20 (url )
#NeXT plain ascii pasteboard type
#CorePasteboardFlavorType 0x70686673 (phfs)
#CorePasteboardFlavorType 0x66737350 (fssp)
#NSPromiseContentsPboardType
#CorePasteboardFlavorType 0x75726C6E (urln)


