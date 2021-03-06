'''
Created on Apr 5, 2012

@author: Dan
'''
from Shapes import * #@UnusedWildImport

class Symbol(object):
    __slots__=("name","isPower","polygons","wires","texts","pins","circles","rectangles")
    #TODO multigate Parts each shape has a unit associated with it... 
    #this coresponds to the swap level in the deviceset. 
    def __init__(self,node,converter):
        self.polygons=[]
        self.wires=[]
        self.texts=[]
        self.pins=[]
        self.circles=[]
        self.rectangles=[]
        self.name=node.get("name")
        for polygon in node.findall("polygon"):
            self.polygons.append(Polyline(polygon,converter,True))
        for wire in node.findall("wire"):
            self.wires.append(Line(wire,converter,True))
        for text in node.findall("text"):
            self.texts.append(Text(text,converter,True))
        for pin in node.findall("pin"):
            self.pins.append(Pin(pin,converter,True))
        for circle in node.findall("circle"):
            self.circles.append(Circle(circle,converter,True))
        
        self.isPower="P"
        for pin in self.pins:
            if pin.direction!="w":
                self.isPower="N"
                break
         



    
    def write(self,symFile):
        """
        DEF name reference unused text_offset draw_pinnumber draw_pinname unit_count units_locked option_flag
        ALIAS name1 name2...
        fields list
        DRAW
            list graphic elements and pins
        ENDDRAW
        ENDDEF
        """
        if self.isPower=="Y":
            token="#"
        else:
            token=""
        symFile.write("DEF "+self.name+" U 0 100 Y Y 1 0 "+self.isPower+"\n")
        #TODO give actual names to fields in syms
        symFile.write("F0 \""+token+"U\" 0 0 0 H I C CNN\n")
        symFile.write("F1 \""+self.name+"\" 0 0 0 H I C CNN \n")
        symFile.write("DRAW\n")
        for polygon in self.polygons:
            symFile.write(polygon.symRep())
        for wire in self.wires:
            symFile.write(wire.symRep())
        for text in self.texts:
            symFile.write(text.symRep())
        for pin in self.pins:
            symFile.write(pin.symRep())
        for circle in self.circles:
            symFile.write(circle.symRep())
        symFile.write("ENDDRAW\n")
        symFile.write("ENDDEF\n")

class Pin(object):
#          name          %String;       #REQUIRED
#          x             %Coord;        #REQUIRED
#          y             %Coord;        #REQUIRED
#          visible       %PinVisible;   "both"
#          length        %PinLength;    "long"
#          direction     %PinDirection; "io"
#          function      %PinFunction;  "none"
#          swaplevel     %Int;          "0"
#          rot           %Rotation;     "R0"
    __slots__=("name",
               "direction",
               "rotation",
               "shape","length",
               "numSize","nameSize",
               "x","y")
    
    def __init__(self,node,converter,noTranspose=True):
        self.name=node.get("name")
        x,y=converter.convertCoordinate(node.get("x"),node.get("y"),True,True)
        self.x=str(x)
        self.y=str(y)
        
        self.getShape(node,converter);
        self.getDirection(node)
        self.getVisibility(node)
        
    def getShape(self,node,converter):
        #<!ENTITY % PinLength         "(point | short | middle | long)">
        length=node.get("length")
        if length=="middle":
            self.length="200"
        elif length=="short":
            self.length="100"
        elif length=="point":
            self.length="0"
        else:
            self.length="300" #defaults to long
            
        #<!ENTITY % PinFunction       "(none | dot | clk | dotclk)">
        func=node.get("function")
        if func=="dot":
            self.shape="I"
        elif func=="clk":
            self.shape="C"
        elif func=="dotclk":
            self.shape="CI"
        else:
            self.shape=""#defualts to line
            
        #on = U (up) D (down) R (right) L (left).
        
        rot=converter.convertRotation(node.get("rot"))['rot']
        if rot==0:
            self.rotation="R"
        elif rot==900:
            self.rotation="U"
        elif rot==1800:
            self.rotation="L"
        elif rot==2700:
            self.rotation="D"
        else:
            print("Warning: symbol pin not at 90 degrees\n"+self.name+": "+str(rot))
            
    def getDirection(self,node):
        #<!ENTITY % PinDirection "(nc | in | out | io | oc | pwr | pas | hiz | sup)">
        myDict={"nc":"N",   #not connected
                "in":"I",   #input
                "out":"O",  #output
                "io":"B",   #bidirectional
                "oc":"C",   #open Collector
                "pwr":"W",  #power input
                "pas":"P",  #Passive
                "hiz":"U",  #unspecified TODO this might be open emitter (E)
                "sup":"w"   #power output
                }
        direction=myDict.get(node.get("direction"))
        if direction==None:
            direction="B" #default to bidi
        self.direction=direction
        
    def getVisibility(self,node):
        #<!ENTITY % PinVisible        "(off | pad | pin | both)">
        vis=node.get("visible")
        
        self.numSize="0"
        self.nameSize="0"
        
        if vis!="off" and vis!="pad":
            self.nameSize="60"

    def symRep(self):
        num=self.name
        if len(self.name)>4:
            num=self.name[:4]
        myString="X "+self.name+" "+num+" "+self.x+" "+self.y+" "+self.length
        myString+=" "+self.rotation+" "+self.numSize+" "+self.nameSize+" 0 0 "
        myString+=self.direction+" "+self.shape+"\n"
        return myString

        