from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import *
from AppKit import *

import math

class ATImageAndTextCell(NibClassBuilder.AutoBaseClass):

    _image = None
    
    def copyWithZone_(self, zone):
        cell = super(ATImageAndTextCell, self).copyWithZone_(zone)
        cell.image = self._image
        return cell
        
    def setImage_(self, anImage):
        if (anImage != self._image):
            print "setting new image"
            self._image = anImage
            
    def image(self):
        return self._image
        
    def imageFrameForCellFrame_(self, cellFrame):
        
        imageFrame = NSZeroRect
        if self._image:
            imageFrame.size = self._image.size()
            imageFrame.origin = cellFrame.origin
            imageFrame.origin.x += 3
            verticalSpacing = cellFrame.size.height - imageFrame.size.height
            imageFrame.origin.y += math.ceil(vericalSpacing/2.0)

        return imageFrame
        
    def editWithFrame_inView_editor_delegate_event_(self, aRect, controlView, textObj, anObject, theEvent):
    
        print "editWithFrame"
        imageFrame, textFrame = NSDivideRect(aRect, 3 + self._image.size().width, NSMinXEdge)
        super(ATImageAndTextCell, self).editWithFrame_inView_editor_delegate_event_(textFrame, controlView, textObj, anObject, theEvent)
        
    def selectWithFrame_inView_editor_delegate_start_length_(self, aRect, controlView, textObj, anObject, selStart, selLength):
        print "selectWithFrame"
        
        imageFrame, textFrame = NSDivideRect(aRect, 3 + self._image.size().width, NSMinXEdge)
        super(ATImageAndTextCell, self).selectWithFrame_inView_editor_delegate_start_length_(textFrame, controlView, textObj, anObject, selStart, selLength)


    def drawWithFrame_inView_(self, cellFrame, controlView):
    
        textFrame = cellFrame
    
        if self._image:
            imageSize = self._image.size()
            
            imageFrame, textFrame = NSDivideRect(cellFrame, 3 + imageSize.width, NSMinXEdge)
            if self.drawsBackground():
                self.backgroundColor().set()
                NSRectFill(imageFrame)
                
            imageFrame.origin.x += 3
            imageFrame.size = imageSize
            
            imageFrame.origin.y += math.ceil((cellFrame.size.height + imageFrame.size.height) * 0.5)
                
            self._image.compositeToPoint_operation_(imageFrame.origin, NSCompositeSourceOver)        
        
        super(ATImageAndTextCell, self).drawWithFrame_inView_(textFrame, controlView)
        
    def cellSize(self):
        cellSize = super(ATImageAndTextCell, self).cellSize()
        if self._image:
            cellSize.width += self._image.size().width + 3
        else:
            cellSize.width += 3
        return cellSize
    
        
    
    
        
        
        