
import sys
import os
import re
import captions
from pprint import pprint
from optparse import OptionParser
   

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()

    directory = args[0]
    p = captions.Parser()
    p.parse(directory)
    
    print ('Bedford')
    for ref in p.findWords(['bedford']):
        print(ref.link,ref.text)
    print()
    
    print ('Final Experiment')
    for ref in p.findWords(['final','experiment']):
        print(ref.link,ref.text)
    print()
    
    print ('Will Duffy')
    for ref in p.findWords(['will','duffy']):
        print(ref.link,ref.text)
    print()
    
    print ('Anarctic')
    for ref in p.findWord('anarctic'):
        print(ref.link,ref.text)
    print()

    print ('Antarctic')
    for ref in p.findWord('antarctic'):
        print(ref.link,ref.text)
    print()
    
    print ('Antarctica')
    for ref in p.findWord('antarctica'):
        print(ref.link,ref.text)
    print()
        
    print ('South Pole')
    for ref in p.findWords(['south','pole']):
        print(ref.link,ref.text)
    print()
    
    print ('Midnight Sun')
    for ref in p.findWords(['midnight','sun']):
        print(ref.link,ref.text)
    print()
        
    print ('24 hour')
    for ref in p.findWords(['24','hour']):
        print(ref.link,ref.text)
    print()

