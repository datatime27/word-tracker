
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
    
    '''
    print ('Bedford')
    for ref in p.findWords(['bedford']):
        print(ref.link,ref.text)
    print()
    '''
    print ('Final Experiment')
    for ref in p.findWords(['final','experiment']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
    
    print ('Will Duffy')
    for ref in p.findWords(['will','duffy']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
    
    print ('Anarctic')
    for ref in p.findWord('anarctic'):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()

    print ('Antarctic')
    for ref in p.findWord('antarctic'):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
    
    print ('Antarctica')
    for ref in p.findWord('antarctica'):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
        
    print ('South Pole')
    for ref in p.findWords(['south','pole']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
    
    print ('Midnight')
    for ref in p.findWords(['midnight']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
        
    print ('24 hour')
    for ref in p.findWords(['24','hour']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
    
    print ('Southern hemisphere')
    for ref in p.findWords(['southern','hemisphere']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()

    print ('Flight')
    for ref in p.findWords(['flight']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()

    print ('Airplane')
    for ref in p.findWords(['airplane']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()

    print ('Plane')
    for ref in p.findWords(['plane']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()

    print ('Sunset')
    for ref in p.findWords(['sunset']):
        print(ref.publishedAt.split('T')[0], ref.link,ref.text)
    print()
