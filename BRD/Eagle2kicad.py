'''
Created on Dec 23, 2011

@author: Dan Chianucci
'''
from BRD.brdParser import brdParser
import codecs
import math

myDict={}
contactRefs={}
signalIds={}
layerIds={}

def getLayerIds():
    global layerIds
    layerIds={'1':'15',
               '2':'14',
               '3':'13',
               '4':'12',
               '5':'11',
               '6':'10',
               '7':'9',
               '8':'8',
               '9':'7',
               '10':'6',
               '11':'5',
               '12':'4',
               '13':'3',
               '14':'2',
               '15':'1',
               '16':'0',
               '20':'28',
               '21':'21',
               '22':'20',
               '25':'25',
               '26':'25',
               '27':'26',
               '28':'26',
               '29':'23',
               '30':'22',
               '31':'19',
               '32':'18',
               '35':'17',
               '36':'16',
               '51':'26',
               '52':'27',
               '95':'26',
               '96':'27'}

def getContactRefs():
    global contactRefs
    signals=myDict['eagle']['drawing']['board']['signals']
    
    for signal in signals:
        sigRefs=signals[signal].get('contactref')
        if not sigRefs==None:
            for ref in sigRefs:
                element = sigRefs[ref]['element']
                pad=sigRefs[ref]['pad']           
                
                if contactRefs.get(element)==None:
                    contactRefs[element]={}
                contactRefs[element][pad]=signal


def main(inFileName=None,outFileName=None):
    global myDict
    if inFileName == None:
        inFile=open(input("Enter Name of Eagle File: "))
    else:
        inFile=open(inFileName)
    
    b=brdParser()
    myDict=b.parse(inFile)
    getContactRefs()
    getLayerIds()
    printKicadFile(outFileName)

def printKicadFile(outFileName=None):
    if outFileName==None:
        outFileName=input("Output File: ")
    out=codecs.open(outFileName,'w','utf-8')
    out.write('PCBNEW-BOARD Version 0 date 0/0/0000 00:00:00\n\n')
    out.close()
    out=codecs.open(outFileName,'a','utf-8')

    writeEQUIPOT(out)
    writeMODULES(out)
    writeGRAPHICS(out)
    writeTRACKS(out)
    writeZONES(out)
       
    out.write('$EndBOARD')
    out.close()



def getWireInfo(wire,noTranspose=False):
        x1,y1=convertCoordinate(wire.get('x1'),wire.get('y1'),noTranspose)
        x2,y2=convertCoordinate(wire.get('x2'),wire.get('y2'),noTranspose)
        width=convertUnit(wire.get('width'))
        layer=layerIds.get(wire.get('layer'))
        curve=wire.get('curve')
        if not curve==None:
            x1,y1,x2,y2,curve=getWireArcInfo(wire,noTranspose)
            
        listCheck=[x1,y1,x2,y2,width,layer]
        for element in listCheck:
            if element==None:
                return None
                
        return {'x1':x1,'y1':y1,'x2':x2,'y2':y2,'width':width,'layer':layer,'curve':curve}
    
def getWireArcInfo(arc,noTranspose=False,noInvert=False):
    ##x1y1 is endpoint1
    ##x2y2 is endpoint 2
    ##curve is sweep angle from pt1 to pt2 ccw
    
    ##ways to do this
    
    curve=float(arc['curve'])
#    print('Curve: ',curve)
    x1,y1=arc.get('x1'),arc.get('y1')
    x2,y2=arc.get('x2'),arc.get('y2')
#    print('Point 1: ',(x1,y1))
#    print('Point 2: ',(x2,y2))
    
    #radius of arc
    x1=float(x1)
    x2=float(x2)
    y1=float(y1)
    y2=float(y2)
    l=math.sqrt((x1-x2)**2+(y1-y2)**2)
    r=l/(2*math.sin(math.radians(curve/2.0)))
#    print('Radius: '+str(r)+ '   Chord: '+str(l))
    

    
    ##go to midpoint of chord move perpendicular by arc height
    h=math.sqrt(r**2-(l/2)**2)
#    print('Height: ',h)
    #slope of chord
    dY=(y2-y1)
    dX=(x2-x1)
#    print('Slope: '+str(dY)+' / '+str(dX))
    mX=(x2+x1)/2
    mY=(y2+y1)/2
#    print('Midpoint ',(mX,mY)) 
    

    chordangle=math.atan2(dY,dX)
    if chordangle<0:
        chordangle+=math.radians(360)
    
    angleSign=curve/math.fabs(curve)
    
    angle=chordangle-math.radians(90)*angleSign
   
    xChange=h*math.cos(angle)#*outX
    yChange=h*math.sin(angle)#*outY
    if math.fabs(curve)<180:
        xChange=-xChange
        yChange=-yChange

#    print('xChange: ',xChange)
#    print('yChange: ',yChange)
    
    cX=mX+xChange
    cY=mY+yChange

#    x1=str(int(x1))
#    y1=str(int(y1))
#    cX=str(int(cX))
#    cY=str(int(cY))
    x1,y1=convertCoordinate(x1,y1,noTranspose,noInvert)
    cX,cY=convertCoordinate(cX,cY,noTranspose,noInvert)
    curve=str(-int(curve*10))

    return cX,cY,x1,y1,curve

def polygonToLines(polygon):
    vertexs=polygon['vertex']
    width=polygon['width']
    layer=polygon['layer']
    wires=[]
    for _i in range(len(vertexs)):
        nexti=(_i+1)%len(vertexs)
        x1=vertexs[_i]['x']
        y1=vertexs[_i]['y']
        x2=vertexs[nexti]['x']
        y2=vertexs[nexti]['y']
        curve=vertexs[_i].get('curve')
        wire={'x1':x1,'y1':y1,'x2':x2,'y2':y2,'curve':curve,'width':width,'layer':layer}
        wires.append(wire)
    return wires

def getTextInfo(text,noTranspose=False):
    global layerIds
    
    txtData=text['txtData']
    x,y=convertCoordinate(text['x'],text['y'],noTranspose)
    xSize=convertUnit(text['size'])#*5/7
    ySize=convertUnit(text['size'])
    
    wMod=text.get('ratio')
    if wMod==None:
        wMod='8'
    width=str(int(ySize)*int(wMod)//100)

    
    rot=text.get('rot')
    if rot==None:
        rot='0'
        mirror='1'
        spin=False
    else:
        rot=getRotationInfo(rot)
        mirror='0' if rot['mirror'] else '1'
        spin=rot['spin']
        rot=rot['rot']

    if not (rot=='0' or rot=='900' or rot=='1800' or rot=='2700' or rot=='3600'):
        return None
     
    layer=layerIds[text['layer']]
    style='Normal'
    
    if spin:
        justification='L'
    
    elif int(rot)<=900 or int(rot)>2700:
        justification='L'
        
    else:
        justification='R'
        rot=str(int(rot)-1800)
    
    rot=int(rot)
    offset=int(ySize)//2
    sign=1
    if justification=='R':
        sign=-1
    if (rot+3600)%3600==0:
        y=str(int(y)-offset*sign)
    elif(rot+3600)%3600==900:
        x=str(int(x)-offset*sign)
    elif(rot+3600)%3600==1800:
        y=str(int(y)+offset*sign)
    elif(rot+3600)%3600==2700:
        x=str(int(x)+offset*sign)
        
    rot=str(rot)
    return {'text':txtData,'x':x,'y':y,'xSize':xSize,'ySize':ySize,'width':width,'rot':rot,'mirror':mirror,'just':justification,'layer':layer,'style':style}
  
def getRectInfo(rect):
    ##have to convert to lines
    pass

def getCircInfo(circ,noTranspose=False):
    radius=convertUnit(circ['radius'])
    cX,cY=convertCoordinate(circ['x'],circ['y'],noTranspose)
    width=convertUnit(circ['width'])
    layer=layerIds.get(circ['layer'])
    checklist=[radius,cX,cY,width,layer]
    for element in checklist:
        if element==None:
            return None
    pX=str(int(cX)+int(radius))
    pY=cY
    return {'cX':cX,'cY':cY,'pX':pX,'pY':pY,'layer':layer,'width':width}
    
def getViaInfo(via):
    x,y=convertCoordinate(via.get('x'),via.get('y'))
    drill=convertUnit(via.get('drill'))
    checkList=[x,y,drill]
    for element in checkList:
        if element==None:
            return None
    return {'x':x,'y':y,'drill':drill}

def getRotationInfo(rot):
    mirror=False
    spin=False
    if rot==None:
        rot='0'
    else:
        if rot[0]=='M':
            mirror=True
            rot=str(int(float(rot[2:])*10))
        elif rot[0]=='S':
            spin=True
            rot=str(int(float(rot[2:])*10))
        else:
            rot=str(int(float(rot[1:])*10))
    
    return {'rot':rot,'mirror':mirror,'spin':spin}

def getModInfo(mod):
    x,y=convertCoordinate(mod['x'],mod['y'])
    rotation = getRotationInfo(mod.get('rot'))
    layer='0' if rotation['mirror'] else '15'
    package=mod.get('package')
    lib=mod.get('library')
    name=str(mod.get('name'))
    value=str(mod.get('value'))
    return {'x':x,'y':y,'rot':rotation['rot'],'mirror':rotation['mirror'],'layer':layer,'package':package,'lib':lib,'name':name,'value':value}

def getPadInfo(pad,modName,modRot,mirror):
    rot=modRot
    name=pad.get('name')
    shapeType='smd' if pad.get('drill')==None else 'pad'
    pX,pY=convertCoordinate(pad['x'],pad['y'],True)   
    net=None
    if not contactRefs.get(modName)==None:
        if not contactRefs[modName].get(name)==None:
            netName=contactRefs[modName][name]
            netNumber=signalIds[netName]
            net={'name':netName,'num':netNumber}
    
    if shapeType=='pad':
        drill=convertUnit(pad['drill'])
        if pad.get('diameter')==None:
            diameter=str(int(int(drill)*1.5))
        else:
            diameter=convertUnit(pad['diameter'])
        xSize=diameter
        ySize=diameter
        kind='STD'
        layerMask='00A88001'#00A88001 should tell it to go through all layers
        shape='C'
    
    elif shapeType=='smd':
        drill='0'
        xSize=convertUnit(pad['dx'])
        ySize=convertUnit(pad['dy'])
        if not pad.get('rot')==None:
            pRot=getRotationInfo(pad['rot'])['rot']
            rot=str(int(pRot)+int(modRot))
        kind='SMD'
        layerMask ='00440001' if mirror else '00888000'
        shape='R'
            
    return {'name':name,'drill':drill,'xSize':xSize, 'ySize':ySize,'x':pX,'y':pY,'net':net,'kind':kind,'shape':shape,'layerMask':layerMask,'rot':rot}                     
 
def writeEQUIPOT(outFile):
    global myDict
    global signalIds
    subDict=myDict['eagle']['drawing']['board']['signals'] 
    i=0
    for signal in subDict:
        i+=1
        name=subDict[signal].get('name')
        signalIds[name]=str(i)
        outFile.write('$EQUIPOT\n')
        outFile.write('Na '+str(i)+' '+name+'\n')
        outFile.write('St~\n')
        outFile.write('$EndEQUIPOT\n\n')

#No Text
#No Rects
def writeMODULES(outFile):
    global myDict
    global signalIds
    global contactRefs
    
    subDict=myDict['eagle']['drawing']['board']['elements']
    for name in subDict:
        info=subDict[name]
        mod=getModInfo(info)
        libInfo=myDict['eagle']['drawing']['board']['libraries'][mod['lib']]['packages'][mod['package']]
        
        outFile.write('$MODULE '+mod['package']+'\n')
        outFile.write('Po '+mod['x']+' '+mod['y']+' '+mod['rot']+' '+mod['layer']+' 00000000 00000000 ~~\n')
        outFile.write('Li '+mod['package']+'\n')
        outFile.write('Sc 00000000\n')
        outFile.write('Op 0 0 0\n')
        
        #Field Desc "Name/Value"
        #              T# x y xsize ysize rot penWidth N Visible layer "txt"
        outFile.write('T0 0 0 0 0 0 0 N I 25 "'+mod['name']+'"\n')
        outFile.write('T1 0 0 0 0 0 0 N I 26 "'+mod['value']+'"\n')
        
        #Drawing
        
        #Lines
        if not libInfo.get('wire')==None:
            for wire in libInfo['wire']:
                w=getWireInfo(wire,True)

                if not w==None:
                    wtype='DS ' if w['curve']==None else 'DA '
                    curve=' ' if w['curve']==None else (' '+w['curve']+' ')
                    outFile.write(wtype+w['x1']+' '+w['y1']+' '+w['x2']+' '+w['y2']+curve+w['width']+' '+w['layer']+'\n')
        
        #PolyGons
        if not libInfo.get('polygon')==None:
            for poly in libInfo['polygon']:
                wires=polygonToLines(poly)
                for wire in wires:
                    w=getWireInfo(wire,True)
                    if not w==None:
                        wtype='DS ' if w['curve']==None else 'DA '
                        curve=' ' if w['curve']==None else (' '+w['curve']+' ')
                        outFile.write(wtype+w['x1']+' '+w['y1']+' '+w['x2']+' '+w['y2']+curve+w['width']+' '+w['layer']+'\n')
        
        #circles               
        if not libInfo.get('circle')==None:
            for circ in libInfo['circle']:
                circ=getCircInfo(circ,True)
                if circ==None:
                    pass
                else:
                    outFile.write('DC '+circ['cX']+' '+circ['cY']+' '+circ['pX']+' '+circ['pY']+' '+circ['width']+' '+circ['layer']+'\n')
                    
        #PAD Descriptions:
        mirror=mod['mirror']
        allConnects=[]
        if not libInfo.get('pad')==None:
            for pad in libInfo['pad']:
                allConnects.append(libInfo['pad'][pad])            
        
        if not libInfo.get('smd')==None:
            for smd in libInfo['smd']:
                allConnects.append(libInfo['smd'][smd])
        
        for pad in allConnects:
            #pad=allConnects[pad]
            p=getPadInfo(pad,name,mod['rot'],mirror)
            outFile.write('$PAD\n')
            outFile.write('Sh "'+p['name']+'" '+p['shape']+' '+p['xSize']+' '+p['ySize']+' 0 0 '+p['rot']+'\n')
            outFile.write('Dr '+p['drill']+' 0 0\n')
            outFile.write('At '+p['kind']+' N '+p['layerMask']+'\n') 
            if not p.get('net')==None:
                outFile.write('Ne '+p['net']['num']+' "'+p['net']['name']+'"\n')
            outFile.write('Po '+p['x']+' '+p['y']+'\n')                      
            outFile.write('$EndPAD\n')
                
        outFile.write('$EndMODULE '+mod['package']+'\n\n')


#No Rectangle
def writeGRAPHICS(outFile):
    plainWires=myDict['eagle']['drawing']['board']['plain']['wire']
    plainText=myDict['eagle']['drawing']['board']['plain'].get('text')
    plainCircles=myDict['eagle']['drawing']['board']['plain']['circle']
#    plainRects=myDict['eagle']['drawing']['board']['plain']['rectangle']
    plainPolys=myDict['eagle']['drawing']['board']['plain'].get('polygon')
    
    for line in plainWires:        
        info=getWireInfo(line)
        if not info == None:
            curve='900'
            shape='0'
            if not info.get('curve')==None:
                curve=info['curve']
                shape='2'
            outFile.write('$DRAWSEGMENT\n')         
            outFile.write('Po '+shape+' '+info['x1']+' '+info['y1']+' '+info['x2']+' '+info['y2']+' '+info['width']+'\n')
            outFile.write('De '+info['layer']+' 0 '+curve+' 0 0\n')
            outFile.write('$EndDRAWSEGMENT\n\n')
            
    if not plainText==None:
        for text in plainText:
            info=getTextInfo(text)
            if not info==None:
                outFile.write('$TEXTPCB\n')         
                outFile.write('Te "'+info['text']+'"\n')
                outFile.write('Po '+info['x']+' '+info['y']+' '+info['xSize']+' '+info['ySize']+' '+info['width']+' '+info['rot']+'\n')
                outFile.write('De '+info['layer']+' '+info['mirror']+' 0000 '+info['style']+' '+info['just']+'\n')
                outFile.write('$EndTEXTPCB\n\n')
    
    if not plainPolys==None:
        for polygon in plainPolys:
            wires=polygonToLines(polygon)
            for wire in wires:
                info=getWireInfo(wire)
                if not info == None:
                    curve='900'
                    shape='0'
                    if not info.get('curve')==None:
                        curve=info['curve']
                        shape='2'
                    outFile.write('$DRAWSEGMENT\n')         
                    outFile.write('Po '+shape+' '+info['cX']+' '+info['cY']+' '+info['x2']+' '+info['y2']+' '+info['width']+'\n')
                    outFile.write('De '+info['layer']+' 0 '+curve+' 0 0\n')
                    outFile.write('$EndDRAWSEGMENT\n\n')
                    
    if not plainCircles==None:
        for circle in plainCircles:
            info=getCircInfo(circle)
            if not info==None:
                    outFile.write('$DRAWSEGMENT\n')         
                    outFile.write('Po 3 '+info['cX']+' '+info['cY']+' '+info['pX']+' '+info['pY']+' '+info['width']+'\n')
                    outFile.write('De '+info['layer']+' 0 900 0 0\n')
                    outFile.write('$EndDRAWSEGMENT\n\n')

def writeTRACKS(outFile):
    signals=myDict['eagle']['drawing']['board']['signals']
    outFile.write('$TRACK\n')
    
    for sigName in signals:
        signal=signals[sigName]
        if not signal.get('wire')==None:            
            for wire in signal['wire']:
                w = getWireInfo(wire)
                netCode=signalIds[sigName]
                if not w == None:
                    outFile.write('Po 0 '+w['x1']+' '+w['y1']+' '+w['x2']+' '+w['y2']+' '+w['width']+'\n')                
                    outFile.write('De '+w['layer']+' 0 '+netCode+' 0 0\n')
                
        if not signal.get('via')==None:
            for via in signal['via']:
                v=getViaInfo(via)
                netCode=signalIds[sigName]
                if not v==None:
                    outFile.write('Po 3 '+v['x']+' '+v['y']+' '+v['x']+' '+v['y']+' '+v['drill']+'\n')                    
                    outFile.write('De 15 1 '+netCode+' 0 0\n')
            
    outFile.write('$EndTRACK\n\n')


def writeZONES(outFile):
    signals=myDict['eagle']['drawing']['board']['signals']
    outFile.write('$ZONE\n')
    for sigName in signals:
        signal=signals[sigName]
        if not signal.get('polygon')==None:            
            for polygon in signal['polygon']:
                vertexs=polygon['vertex']
                for _i in range(len(vertexs)):
                    nexti=(_i+1)%len(vertexs)
                    x1,y1=convertCoordinate(vertexs[_i]['x'],vertexs[_i]['y'])
                    x2,y2=convertCoordinate(vertexs[nexti]['x'],vertexs[nexti]['y'])
                    width=convertUnit(polygon['width'])                    
                    netCode=signalIds[sigName]   
                    layer=layerIds.get(polygon['layer'])
                    if not layer == None:
                        outFile.write('Po 0 '+x1+' '+y1+' '+x2+' '+y2+' '+width+'\n')                 
                        outFile.write('De '+layer+' 0 '+netCode+' 0 0\n')
                        
    outFile.write('$EndZONE\n\n')
    

def convertUnit(unit):
    if unit==None:
        return None
    return str(int(float(unit)/25.4*10000))

def convertCoordinate(x,y,noTranspose=False,noInvert=False):
    global myDict
    
    if noTranspose:
            xTranspose=0
            yTranspose=0    
    else:
        border=myDict['border']
        cX,cY=convertCoordinate(border['cX'],border['cY'],True)
        xTranspose=0 if noTranspose else 58500-int(cX)
        yTranspose=0 if noTranspose else 41355-int(cY)
        
    invertFactor= 1 if noInvert else -1
    
    if not x==None: 
        x=str(xTranspose+int(float(x)/25.4*10000))
    if not y==None:
        y=str((yTranspose+int(invertFactor*float(y)/25.4*10000)))
    return x,y  

if __name__ == '__main__':
    main()
