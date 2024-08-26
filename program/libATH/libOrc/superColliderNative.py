#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          superColliderNative.py
# Purpose:       native csound instrument definitions instruments.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import time
import unittest, doctest

from athenaCL.libATH import drawer
from athenaCL.libATH import language
from athenaCL.libATH import pitchTools
lang = language.LangObj()
from athenaCL.libATH.libOrc import baseOrc

_MOD = 'superColliderNative.py'
from athenaCL.libATH import prefTools
environment = prefTools.Environment(_MOD)




class SuperColliderNative(baseOrc.Orchestra):
    """built-in csound instruments"""
    def __init__(self):
        baseOrc.Orchestra.__init__(self)

        self.name = 'superColliderNative'
        self.srcStr = None # string representation for writing

        self._instrNumbers = [0,
                              10,
                             ]
        
        # on initialization, load a dictionary of objects for use
        self._instrObjDict = {}
        globalDict = globals()
        for iNo in self._instrNumbers:
            objAttr = globalDict['Inst%i' % iNo]
            self._instrObjDict[iNo] = objAttr() # instantiate obj
        

    #-----------------------------------------------------------------------||--
    def instNoValid(self, iNo):
        """test if an instrument number is valid"""
        if drawer.isInt(iNo) and iNo in self._instrNumbers:
            return 1
        else:
            return 0

    def instNoList(self, format=None):
        """return a list of instrument numbers; if
        a list is not availabe, return None"""
        if format == 'user':
            return drawer.listToStr(self._instrNumbers)
        return self._instrNumbers


    def getInstObj(self, iNo):
        if iNo in list(self._instrObjDict.keys()): # already loaded
            return self._instrObjDict[iNo] # call attribute of module to get object
        else:
            raise ValueError('bad instrument number given: %s' % iNo)
            

    def constructOrc(self, noChannels=2, instList=None):
        """buildes a string of an entire orchestra
        provides proper header and output sections based on 
        number of channels
        """
        self.noChannels = noChannels
        msg = []
        #self.instrObjDict = {}
        if instList == None: # if not given, add all instruments
            instList = self.instNoList()
        for number in instList:
            if not self.instNoValid(number):
                environment.printWarn([lang.WARN, 'instrument %i not available.' % number])
                continue
            instrObj = self.getInstObj(number)
            msg.append(instrObj.buildInstrDef(noChannels))
        self.srcStr = ''.join(msg)

    def getInstInfo(self, iNo=None):
        """returns a dictionary of instrNo : (Name, pNo, pInfo)
        has data for all instruments
        pmtrFields includes 6 default values
        """
        if iNo == None:
            instrList = self.instNoList() # use method
        else:
            instrList = [iNo,]
        #self.instrObjDict = {} # this used to store inst obj data
        instInfoDict = {}
        for number in instrList:
            instrObj = self.getInstObj(number)
            instInfoDict[number] = (instrObj.name, 
                              instrObj.pmtrFields, instrObj.pmtrInfo)
        return instInfoDict, instrList

    def getInstPreset(self, iNo, auxNo=None):
        """returns a dictionary of default values for one instrument"""
        instrObj = self.getInstObj(iNo)
        presetDict = instrObj.getPresetDict() # converts to aux0 fist pos
        return presetDict

    def getInstName(self, iNo):
        'returns a string of name'
        instrObj = self.getInstObj(iNo)
        return instrObj.name

    def getInstAuxNo(self, iNo):
        instrObj = self.getInstObj(iNo)
        return instrObj.auxNo

    def getInstPmtrInfo(self, iNo, pmtrNo):
        """for specified inst, pmtrNo, return pmtr info
        parameter numbers start at 0"""
        instrObj = self.getInstObj(iNo)
        # numbers are shifted by pmtrCountDefault
        # this orchestra uses 'pmtr' instead of 'auxQ'
        key = 'pmtr%s' % (pmtrNo + 1 + instrObj.pmtrCountDefault)
        if instrObj.pmtrInfo != {}:
            return instrObj.pmtrInfo[key]
        else:
            return 'no information available'
        
    #-----------------------------------------------------------------------||--
    def _postMapPs(self, iNo, val):
        return pitchTools.psToPch(val)
        
    def _postMapAmp(self, iNo, val, orcMapMode=1):
        # get max/min amp value form inst, as well as scale factor
        instrObj = self.getInstObj(iNo)
        ampMax = float(instrObj.postMapAmp[1])
        if orcMapMode: # optional map; allow values greater then 1
            val = val * ampMax # temp: assume max amp of 90
        # always limit
        if val < 0: val = 0 # we can assume tt amps are never negative
        return val
        
    def _postMapPan(self, iNo, val, orcMapMode=1):
        if orcMapMode: # optional map
            pass # values are expected b/n 0 and 1
        # always limit: modulo 1    
        if val < 0 or val > 1: val = val % 1.0
        return val


        
        
#-----------------------------------------------------------------||||||||||||--
class InstrumentSuperCollider(baseOrc.Instrument):
    # outputs expect and instrument to have a single final signal, calld "aMixSig
    # this bit of codes gets appended to end of inst def
    def __init__(self):
        """
        >>> a = InstrumentSuperCollider()
        """
        baseOrc.Instrument.__init__(self)
        self.author = 'athenaCL native' # attribution

        self.pmtrCountDefault = 6 # 6 built in values
        self.pmtrFields = self.pmtrCountDefault
        # postMap values for scaling
        self.postMapAmp = (0,1, 'linear') # most amps are in db
        self.postMapPan = (0,1, 'linear')  # all pan values assume 0-1 maping
        
        self.instNo = None
        self.name = None

        # TODO!
        # leave four spaces
        self.monoOutput = """    Out.ar(0, Pan2.ar(sigPrePan, panPos));
"""
        self.stereoOutput = """    Out.ar(0, Pan2.ar(sigPrePan, panPos));
"""
        self.quadOutput = """    Out.ar(0, Pan2.ar(sigPrePan, panPos));
"""

    def getInstHeader(self):
        msg = """SynthDef("%s", {""" % self.name
        return msg

    def getInstFooter(self):
        msg = """ }).writeDefFile;
s.sendSynthDef("%s");

""" % self.name
        return msg

    def buildInstrDef(self, noChannels):
        """returns a string of all the code needed for this instrument

        >>> a = Inst0()
        >>> post = a.buildInstrDef(2)
        >>> "SynthDef" in post
        True
        >>> a.stereoOutput in post
        True
        """
        self.noChannels = noChannels

        msg = []
        msg.append(self.getInstHeader())
        msg.append(self.orcCode)
        if self.noChannels == 1:
            msg.append(self.monoOutput)
        elif self.noChannels == 2:
            msg.append(self.stereoOutput)
        elif self.noChannels == 4:
            msg.append(self.quadOutput)
        msg.append(self.getInstFooter())
        return ''.join(msg)



#-----------------------------------------------------------------||||||||||||--
# instruments 0 through 9 are unpitched percussion
class Inst0(InstrumentSuperCollider):
    def __init__(self):
        """
        >>> a = Inst0()
        """
        InstrumentSuperCollider.__init__(self)

        self.instNo = 0
        self.name = 'noiseBasic'
        self.info = 'A simple noise instrument.'
        self.postMapAmp = (0, 1, 'linear') # assume amps not greater tn 1

        self.pmtrInfo = {
          'pmtr7'   : 'attack percent within unit interval',
          'pmtr8'   : 'release percent within unit interval',
          'pmtr9'   : 'cutoff frequency in midi pitch values',
          }
          
        self.pmtrDefault = {
          'panQ'   : ('rb', .2, .2, 0, 1),
          'pmtr7'   : ('bg', 'rc', [.1, .2, .3, .4]),
          'pmtr8'   : ('bg', 'rc', [.1, .2, .3, .4]),
          'pmtr9'   : ('ru', 60, 120),
          }
        self.auxNo = len(list(self.pmtrInfo.keys()))
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrFieldNames = ['sus', 'amp', 'pan'] + list(self.pmtrInfo.keys())

        self.author = 'athenaCL native' # attribution

        self.orcCode = """
   arg sus, amp, pan, attackPercent, releasePercent, cfMidi;
   var env, ampEnvl, gate, panPos, sigPrePan;
   panPos = (pan*2)-1; 
   gate = Line.ar(1, 0, sus, doneAction: 2);
   env = Env.perc(sus*attackPercent, sus*releasePercent, amp, -4);
   ampEnvl = EnvGen.kr(env, gate);
   sigPrePan = LPF.ar(WhiteNoise.ar(ampEnvl), cfMidi.midicps);
"""

    def pmtrToOrcName(self, pmtr):
        """Translate from native pmtr names to score pmtr names
        """
        if pmtr in ['sus', 'pan', 'amp']:
            return pmtr
        elif pmtr == 'inst':
            return self.name
        elif pmtr == 'pmtr7':
            return 'attackPercent'
        elif pmtr == 'pmtr8':
            return 'releasePercent'
        elif pmtr == 'pmtr9':
            return 'cfMidi'
        else:
            raise Exception('canot translate parameter %s' % pmtr)


#-----------------------------------------------------------------||||||||||||--
# instruments 10 through 19 are pitched percussion
class Inst10(InstrumentSuperCollider):
    def __init__(self):
        """
        >>> a = Inst10()
        """
        InstrumentSuperCollider.__init__(self)

        self.instNo = 10
        self.name = 'electroKick'
        self.info = 'A basic elctronic kick.'
        self.postMapAmp = (0, 1, 'linear') # assume amps not greater tn 1

        self.pmtrInfo = {
          'pmtr7'   : 'envelope ratio',
          'pmtr8'   : 'frequency decay',
          }
          
        self.pmtrDefault = {
          'panQ'   : ('rb', .2, .2, 0, 1),
          'pmtr7'   : ('bg', 'rc', [3, 2, 1]),
          'pmtr8'   : ('bg', 'rc', [.02, .05]),
          }
        self.auxNo = len(list(self.pmtrInfo.keys()))
        self.pmtrFields = self.pmtrCountDefault + self.auxNo
        self.pmtrFieldNames = ['sus', 'amp', 'pan', 'ps'] + list(self.pmtrInfo.keys())

        self.author = 'athenaCL native' # attribution

        self.orcCode = """
    arg ps= -10, sus=0.5, amp=1, pan=0.5, envlRatio=3, fqDecay=0.02;
    var fqEnvl, ampEnvl, sigPrePan, panPos, pitchMidi;
    pitchMidi = ps + 60;
    panPos = (pan*2)-1; // convert from 0 to 1 to -1 to 1
    fqEnvl = EnvGen.kr(Env([envlRatio, 1], [fqDecay], \exp), 1) * pitchMidi.midicps;
    ampEnvl = EnvGen.kr(Env.perc(0.05, sus, amp), 1, doneAction: 2);
    sigPrePan = SinOsc.ar(fqEnvl, 0.5pi, ampEnvl);
"""

    def pmtrToOrcName(self, pmtr):
        """Translate from native pmtr names to score pmtr names
        """
        if pmtr in ['sus', 'pan', 'amp', 'ps']:
            return pmtr
        elif pmtr == 'inst':
            return self.name
        elif pmtr == 'pmtr7':
            return 'envlRatio'
        elif pmtr == 'pmtr8':
            return 'fqDecay'
        else:
            raise Exception('canot translate parameter %s' % pmtr)



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


#-----------------------------------------------------------------||||||||||||--
if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)
