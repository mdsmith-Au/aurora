# Open V Switch Flavor Plugin for slice_plugin
# 2014
# SAVI McGill: Heming Wen, Prabhat Tiwary, Kevin Han, Michael Smith,
#              Mike Kobierski and Hoai Phuoc Truong
#

import copy
import glob
import importlib
import json
import os
import sys
import traceback


class OVSPlugin(object):

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.bridge_attributes = {
            'controller':{'listable':True, 'default':'tcp:132.206.206.133:6633'},
            'dpid':{'listable':True, 'default':self.default_dpid()}
        }
        self.attributes = {
            'name':{'listable':False, 'default':None, 'subattributes':None},
            'interfaces':{'listable':False, 'default':None, 'subattributes':None},
            'port_settings':{'listable':False, 'default':{}, 'subattributes':None},
            'bridge_settings':{'listable':False, 'default':{}, 'subattributes':self.bridge_attributes}
        } #Here listable also refers to the presence of sub_attributes
        self.entryFormat = {'flavor':'ovs', 'attributes':{}}

    def default_dpid(self):
        #Load tenant slice database
        config_db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     'config_db',
                                     str(self.tenant_id))

        dpidlist = [0]
        for file_ in glob.glob(os.path.join(config_db_dir, "*.json")):
            try:
                content = json.load(open(file_, 'r'))
                for bridge in content.get('VirtualBridges',None):
                    # DPID may be in the same format as a MAC address:
                    #     xx:xx:xx:xx:xx:xx
                    dpidlist.append(
                        int(bridge.get(
                                'attributes',{}
                            ).get(
                                'bridge_settings', {}
                            ).get(
                                'dpid',0
                            ).replace(':','')
                        )
                    )
            except Exception:
                traceback.print_exc(file=sys.stdout)

        return max(dpidlist) + 1
    
    def parse(self, entry, numSlice, currentIndex, entryIndex):
        dpidOffset = currentIndex + entryIndex #For Generation purposes, ensures a unique tuntag for each slice
        parsedEntry = copy.deepcopy(self.entryFormat)
        
       #First, ensure all attributes that are not default are present
        for attr in self.attributes.keys():
            if not self.attributes[attr]['default']:
                if not attr in entry['attributes']:
                    print('Error in json file, attributes do not match in ovs Flavor (VirtualBridges)!')
                    sys.exit(-1) #Maybe implement an exception?
            else:
                if not attr in entry['attributes']:
                    parsedEntry['attributes'][attr] = self.attributes[attr]['default']
                    
        #Loop through the attributes
        for key in self.attributes:
            if not self.attributes[key]['subattributes']: #Does not have sub_attributes, append to parsedEntry directly
                #parsedEntry['attributes'][key] = str(entry['attributes'][key])
                parsedEntry['attributes'][key] = entry['attributes'][key]
            else: #Check subattributes
                #Initialize to empty dictionary
                parsedEntry['attributes'][key] = {}
                for subkey in self.attributes[key]['subattributes']:
                    if not self.attributes[key]['subattributes'][subkey]['listable']: #Does not have list, append to parsedEntry directly
                        parsedEntry['attributes'][key][subkey] = str(entry['attributes'][key][subkey])   
                    elif not subkey in entry['attributes'][key]: #Default
                        #Dpid generator
                        if subkey == 'dpid':
                            parsedEntry['attributes'][key][subkey] = str(self.attributes[key]['subattributes'][subkey]['default'] + dpidOffset)
                        elif subkey == 'controller':
                            parsedEntry['attributes'][key][subkey] = self.attributes[key]['subattributes'][subkey]['default']
                    else: #Check List
                        #Case 1, single element in list (may have multiple slices, in which case we reuse the element for all slices)
                        if len(entry['attributes'][key][subkey]) == 1:
                            parsedEntry['attributes'][key][subkey] = str(entry['attributes'][key][subkey][0])
                    
                        #Case 2, multiple slices and multiple elements in list (must have 1-1 correspondance)
                        elif numSlice == len(entry['attributes'][key][subkey]):
                            parsedEntry['attributes'][key][subkey] = str(entry['attributes'][key][subkey][currentIndex])
                        
                        #Case 3, Empty list, we need to generate (will need to use init loaded json information)
                        elif len(entry['attributes'][key][subkey]) == 0 and subkey == 'dpid':
                            parsedEntry['attributes'][key][subkey] = str(self.attributes[key]['subattributes'][subkey]['default'] + dpidOffset)
                            
                        elif len(entry['attributes'][key][subkey]) == 0 and subkey == 'controller':
                            parsedEntry['attributes'][key][subkey] = self.attributes[key]['subattributes'][subkey]['default']
                        
                        #Case 4, error in data
                        else:
                            print('Error in json file, please check that the tunnel_tags match the number of APs!')
                            sys.exit(-1) #Maybe implement an exception?
            
        return parsedEntry

if __name__ == "__main__":
    OVSPlugin(1)

