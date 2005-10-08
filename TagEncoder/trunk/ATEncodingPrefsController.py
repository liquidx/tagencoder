from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import *
from AppKit import *

import cjkcodecs.aliases
from cjkcodecs import *
from encodings import aliases

DEFAULT_ENCODINGS = ['big5_hkscs2001', 'gb2312', 'utf8', 'us_ascii']
ATEncodingPboardType = 'ATEncodingPboardType'

class ATEncodingPrefsController(NibClassBuilder.AutoBaseClass):

    # IBOutlets
    # ---------
    # prefPanel
    # availableTableView
    # enabledTableView

    enabledEncodings = None
    availableEncodings = None

    def awakeFromNib(self):
        # load preferences
        defaults = NSUserDefaults.standardUserDefaults()
        self.enabledEncodings = defaults.stringArrayForKey_('enabledEncodings')
        if not self.enabledEncodings:
            defaults.setObject_forKey_(DEFAULT_ENCODINGS, 'enabledEncodings')
            self.enabledEncodings = DEFAULT_ENCODINGS
            
        self.enabledEncodings = [x for x in self.enabledEncodings];
        defaults.synchronize()
            
        # load all encoding choices
        all_aliases = aliases.aliases.keys()
        all_aliases.sort()
        for enc in self.enabledEncodings:
            try:
                all_aliases.remove(enc)
            except ValueError:
                print "%s not in all_aliases" % enc
        self.availableEncodings = all_aliases
        
        self.availableTableView.setDataSource_(self)
        self.enabledTableView.setDataSource_(self)
        
        # enable drag and drop
        self.availableTableView.registerForDraggedTypes_([ATEncodingPboardType])
        self.enabledTableView.registerForDraggedTypes_([ATEncodingPboardType])
        
    """
     - (void)tableView:(NSTableView *)aTableView
        setObjectValue:anObject
        forTableColumn:(NSTableColumn *)aTableColumn
                   row:(int)rowIndex
    """
    def tableView_setObjectValue_forTableColumn_row_(self, aTableView, 
        anObject, aTableColumn, rowIndex):
        pass
        
    """    
     - (id)tableView:(NSTableView *)aTableView
     objectValueForTableColumn:(NSTableColumn *)aTableColumn
                 row:(int)rowIndex
    """                 
    def tableView_objectValueForTableColumn_row_(self, aTableView, 
        aTableColumn, row):
        if aTableView == self.availableTableView:
            return self.availableEncodings[row]
        elif aTableView == self.enabledTableView:
            return self.enabledEncodings[row]
    
    """
    - (int)numberOfRowsInTableView:(NSTableView *)aTableView
    """
    def numberOfRowsInTableView_(self, aTableView):
        if aTableView == self.availableTableView:
            return len(self.availableEncodings)
        elif aTableView == self.enabledTableView:
            return len(self.enabledEncodings)

    """
    - (NSDragOperation)tableView:(NSTableView*)tv
				validateDrop:(id <NSDraggingInfo>)info
				 proposedRow:(int)row
	   proposedDropOperation:(NSTableViewDropOperation)op
	"""
    def tableView_validateDrop_proposedRow_proposedDropOperation_(self, 
            tv, info, row, op):
            
        pasteboardTypes = info.draggingPasteboard().types()
        if pasteboardTypes.containsObject_(ATEncodingPboardType):
            return NSDragOperationMove
        else:
            return NSDragOperationNone

    """    
    - (BOOL)tableView:(NSTableView*)tv
	       acceptDrop:(id <NSDraggingInfo>)info
    		       row:(int)row
	     dropOperation:(NSTableViewDropOperation)op
    """	     
    def tableView_acceptDrop_row_dropOperation_(self, tv, info, row, op):
    
        pboard = info.draggingPasteboard()
        pasteboardTypes = pboard.types()
        
        if pasteboardTypes.containsObject_(ATEncodingPboardType):
            # work out which direction
            if (info.draggingSource() == self.availableTableView) and \
                (tv == self.enabledTableView):
                
                # adding to enabledEncodings
                encodings = pboard.propertyListForType_(ATEncodingPboardType)
                num_encodings = len(encodings)
                for i in range(num_encodings):
                    enc = encodings[num_encodings-i-1]
                    self.enabledEncodings.insert(row, enc)
                    
            elif (info.draggingSource() == self.enabledTableView) and \
                (tv == self.availableTableView):
                encodings = pboard.propertyListForType_(ATEncodingPboardType)
                for enc in encodings:
                    i = self.enabledEncodings.index(enc)
                    del self.enabledEncodings[i]
                    
            elif (self.enabledTableView == info.draggingSource()) and \
                (tv == self.enabledTableView):
                
                encodings = pboard.propertyListForType_(ATEncodingPboardType)
                moved = 0
                for enc in encodings:
                    oldIndex = self.enabledEncodings.index(enc)
                    del self.enabledEncodings[oldIndex]
                    if oldIndex < row + moved:
                        newIndex = row + moved - 1
                    else:
                        newIndex = row + moved
                    print newIndex
                    self.enabledEncodings.insert(newIndex, enc)
                    moved += 1
            else:
                print "dragging source unknown"
    
            self.enabledTableView.reloadData()
            defaults = NSUserDefaults.standardUserDefaults()
            defaults.setObject_forKey_(self.enabledEncodings, \
                 'enabledEncodings')
            defaults.synchronize()
            return True
        else:
            return False
            
    """
    - (BOOL)tableView:(NSTableView *)tableView 
            writeRows:(NSArray *)rows 
         toPasteboard:(NSPasteboard *)pboard
    """
    def tableView_writeRows_toPasteboard_(self, tableView, rows, pboard):
        pboard.declareTypes_owner_([ATEncodingPboardType], self)
        
        # make new files for dragging
        if tableView == self.enabledTableView:
            encodings = map(lambda x: self.enabledEncodings[x], rows)
        else:
            encodings = map(lambda x: self.availableEncodings[x], rows)
        pboard.setPropertyList_forType_(encodings, ATEncodingPboardType)
        return True    
              
    def open_(self, sender):
        self.prefPanel.makeKeyAndOrderFront_(self)
        
    def close_(self, sender):
        self.prefPanel.close()


    
    