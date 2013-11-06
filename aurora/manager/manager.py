# Aurora Manager Functions
# SAVI Mcgill: Heming Wen, Prabhat Tiwary, Kevin Han, Michael Smith

import json
import sys
from slice_plugin import *
from sql_check import *
from aurora_db import *
import MySQLdb as mdb

class Manager():
    
    def __init__(self):
        #Initialize AuroraDB Object
        self.auroraDB = AuroraDB()
        
    def parseargs(self, function, args, tenant_id, user_id, project_id):
        # args is a generic dictionary passed to all functions (each function is responsible for parsing
        # their own arguments
        function = function.replace('-', '_') #For functions in python
        getattr(self, function)(args, tenant_id, user_id, project_id)
    
    def ap_filter(self, args): #STILL NEED TO IMPLEMENT TAG SEARCHING (location_tags table), maybe another connection with intersection?
        try:
            self.con = mdb.connect('localhost', 'root', 'supersecret', 'aurora') #Change address
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)
        
        if len(args) == 0: #No filter or tags
            try:
                with self.con:
                    cur = self.con.cursor()
                    cur.execute("SELECT * FROM ap")
                    tempList =  cur.fetchall()
                    #Prune thorugh list
                    newList = []
                    for i in range(len(tempList)):
                        newList.append([])
                        newList[i].append(tempList[i][0])
                        newList[i].append({})
                        newList[i][1]['region'] = tempList[i][1]
                        newList[i][1]['firmware'] = tempList[i][2]
                        newList[i][1]['version'] = tempList[i][3]
                        newList[i][1]['number_radio'] = tempList[i][4]
                        newList[i][1]['memory_mb'] = tempList[i][5]
                        newList[i][1]['free_disk'] = tempList[i][6]
                        newList[i][1]['supported_protocol'] = tempList[i][7]
                        newList[i][1]['number_radio_free'] = tempList[i][8]
                    return newList
            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
        else: #Multiple arguments (name=openflow & firmware=openwrt & region=mcgill & number_radio>1)
            args_list = args.split('&')
            for (index, entry) in enumerate(args_list):
                args_list[index] = entry.strip()
                if '=' in args_list[index]:
                    if (args.split('=')[0] == "name") or (args.split('=')[0] == "firmware") or (args.split('=')[0] == "region") or (args.split('=')[0] == "supported_protocol"):
                        args_list[index] = args_list[index].split('=')[0]+'=\''+args_list[index].split('=')[1]+'\''
                elif '!' in args_list[index]:
                    if (args.split('!')[0] == "name") or (args.split('!')[0] == "firmware") or (args.split('!')[0] == "region") or (args.split('!')[0] == "supported_protocol"):
                        args_list[index] = args_list[index].split('!')[0]+'<>\''+args_list[index].split('!')[1]+'\''
                    else:
                        args_list[index] = args_list[index].split('!')[0]+'<>'+args_list[index].split('!')[1]
                
            #Combine to 1 string
            expression = args_list[0]
            for (index, entry) in enumerate(args_list):
                if index != 0:
                    expression = expression+' AND '+ entry  
            
            #execute query
            try:
                with self.con:
                    cur = self.con.cursor()
                    cur.execute("SELECT * FROM ap WHERE "+expression)
            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
            tempList =  cur.fetchall()
            #Prune thorugh list
            newList = []
            for i in range(len(tempList)):
                newList.append([])
                newList[i].append(tempList[i][0])
                newList[i].append({})
                newList[i][1]['region'] = tempList[i][1]
                newList[i][1]['firmware'] = tempList[i][2]
                newList[i][1]['version'] = tempList[i][3]
                newList[i][1]['number_radio'] = tempList[i][4]
                newList[i][1]['memory_mb'] = tempList[i][5]
                newList[i][1]['free_disk'] = tempList[i][6]
                newList[i][1]['supported_protocol'] = tempList[i][7]
                newList[i][1]['number_radio_free'] = tempList[i][8]
            return newList
            
    def ap_list(self, args, tenant_id, user_id, project_id):
        if args['filter']:
            arg_filter = args['filter'][0]
        else:
            arg_filter = []
        arg_i = args['i']
        toPrint = self.ap_filter(arg_filter)
        for entry in toPrint:
            print('\nName: '+str(entry[0]))
            if arg_i == True: #Print extra data
                for attr in entry[1]:
                    print(str(attr)+': '+str(entry[1][attr]))
    
    def ap_show(self, args, tenant_id, user_id, project_id):
        arg_name = args['ap-show'][0]
        toPrint = self.ap_filter('name='+arg_name)
        for entry in toPrint:
            print('\nName: '+str(entry[0]))
            for attr in entry[1]:
                print(str(attr)+': '+str(entry[1][attr]))

    def ap_slice_clone(self, args, tenant_id, user_id, project_id):
        arg_ap = args['ap']
        arg_slice = args['ap-slice-clone'][0]
        data = {}
        data['action'] = 'ap-slice-clone'
        data['name'] = arg_slice
        data['list'] = arg_ap
        data['json'] = None
        toSend = json.dumps(data, sort_keys=True, indent=4)
        #Send
        print toSend
    
    def ap_slice_create(self, args, tenant_id, user_id, project_id):
        if 'ap' in args:
            arg_ap = args['ap']
        else:
            arg_ap = None
        if 'filter' in args:
            arg_filter = args['filter'][0]
        else:
            arg_filter = None
        if 'file' in args:
            arg_file = args['file'][0]
        else:
            arg_file = None
        arg_tag = args['tag']
        json_list = [] #If a file is provided for multiple APs, we need to split the file for each AP, saved here
        
        #Load optional json file if applicable
        if arg_file:
            try:
                JFILE = open(arg_file, 'r')
                jsonfile = json.load(JFILE)
                JFILE.close()
            except IOError:
                print('Error opening file!')
                sys.exit(-1)
        
        if arg_ap:
            aplist = arg_ap
        else: #We need to apply the filter
            result = self.ap_filter(arg_filter)
            aplist = []
            for entry in result:
                aplist.append(entry[0])
                
        #Initialize json_list structure
        for i in range(len(aplist)):
            json_list.append({'VirtualInterfaces':[], 'VirtualBridges':[], 'VirtualWIFI':[]})
            
        #Send to plugin for parsing
        json_list = SlicePlugin(tenant_id, user_id, arg_tag).parseCreateSlice(jsonfile, len(aplist), json_list)
        
        #Send
        for json_entry in json_list:
            print json.dumps(json_entry, sort_keys=True, indent=4)
    
    def ap_slice_delete(self, args, tenant_id, user_id, project_id):
        arg_name = args['ap-slice-delete']
        data = {}
        data['action'] = 'ap-slice-delete'
        data['name'] = arg_name
        data['list'] = None
        data['json'] = None
        toSend = json.dumps(data, sort_keys=True, indent=4)
        #Send
        print toSend
    
    def ap_slice_list(self, args, tenant_id, user_id, project_id):
        if args['filter']:
            arg_filter = args['filter'][0]
        else:
            arg_filter = []
        arg_i = args['i']
        try:
            self.con = mdb.connect('localhost', 'root', 'supersecret', 'aurora') #Change address
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)
        if len(arg_filter) == 0: #No filter or tags
            try:
                with self.con:
                    cur = self.con.cursor()
                    cur.execute("SELECT * FROM ap_slice")
                    tempList =  cur.fetchall()
                    #Prune thorugh list
                    newList = []
                    for i in range(len(tempList)):
                        newList.append({})
                        newList[i]['ap_slice_id'] = tempList[i][0]
                        newList[i]['tenant_id'] = tempList[i][1]
                        newList[i]['physical_ap'] = tempList[i][2]
                        newList[i]['project_id'] = tempList[i][3]
                        newList[i]['wnet_id'] = tempList[i][4]
                        newList[i]['status'] = tempList[i][5]
            
            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
        else: #Multiple arguments
            args_list = arg_filter.split('&')
            for (index, entry) in enumerate(args_list):
                args_list[index] = entry.strip()
                if '=' in args_list[index]:
                    args_list[index] = args_list[index].split('=')[0]+'=\''+args_list[index].split('=')[1]+'\''
                elif '!' in args_list[index]:
                    args_list[index] = args_list[index].split('!')[0]+'<>\''+args_list[index].split('!')[1]+'\''
                
            #Combine to 1 string
            expression = args_list[0]
            for (index, entry) in enumerate(args_list):
                if index != 0:
                    expression = expression+' AND '+ entry 
            
            #Execute Query
            try:
                with self.con:
                    cur = self.con.cursor()
                    cur.execute("SELECT * FROM ap_slice WHERE "+expression)
                    tempList = cur.fetchall()
                    #Prune thorugh list
                    newList = []
                    for i in range(len(tempList)):
                        newList.append({})
                        newList[i]['ap_slice_id'] = tempList[i][0]
                        newList[i]['tenant_id'] = tempList[i][1]
                        newList[i]['physical_ap'] = tempList[i][2]
                        newList[i]['project_id'] = tempList[i][3]
                        newList[i]['wnet_id'] = tempList[i][4]
                        newList[i]['status'] = tempList[i][5]
            
            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
        
        if arg_i == False:
            for entry in newList:
                print('ap_slice_id: '+entry['ap_slice_id']+'\n')
        else:
            for entry in newList:
                for attr in entry:
                    print(str(attr)+': '+str(entry[attr]))
                print('\n')
                
    def ap_slice_show(self, args, tenant_id, user_id, project_id):
        arg_id = args['ap-slice-show'][0]
        self.ap_slice_list({'filter':'ap_slice_id='+str(arg_id), 'i':True})
    
    def wnet_add_ap(self, args, tenant_id, user_id, project_id):
        arg_name = args['wnet-add-ap'][0]
        arg_slice = args['slice'][0]
        #Send to database
        self.auroraDB.wnet_add_slice(tenant_id, arg_slice, arg_name)
        
    
    def wnet_create(self, args, tenant_id, user_id, project_id):
        arg_name = args['wnet-create'][0]
        arg_slice = args['slice']
        arg_qos = args['qos_priority'][0]
        arg_share = args['shareable']
        if 'aggregate_rate' in args:
            arg_aggrate = args['aggregate_rate'][0]
        else:
            arg_aggrate = None
        #Send to database
        self.auroraDB.wnet_add(tenant_id, arg_name, arg_slice, arg_aggrate, arg_qos, arg_share)
    
    def wnet_delete(self, args, tenant_id, user_id, project_id):
        arg_name = args['wnet-delete'][0]
        arg_f = args['f']
        #Send to database
        self.auroraDB.wnet_remove(tenant_id, arg_name)
    
    def wnet_join(self, args, tenant_id, user_id, project_id): #TODO AFTER SAVI INTEGRATION
        arg_netname = args['wnet-join'][0]
        arg_wnetname = args['wnet_name'][0]
        #Send to database
        print('NOT YET IMPLEMENTED')
    
    def wnet_fetch(self, tenant_id):
        try:
            self.con = mdb.connect('localhost', 'root', 'supersecret', 'aurora') #Change address
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)
        if tenant_id == 0: #Admin, show all
            try:
                with self.con:
                    cur = self.con.cursor()
                    cur.execute("SELECT * FROM wnet")
                    tempList =  cur.fetchall()
                    #Prune thorugh list
                    newList = []
                    for i in range(len(tempList)):
                        newList.append({})
                        newList[i]['wnet_id'] = tempList[i][0]
                        newList[i]['name'] = tempList[i][1]
                        newList[i]['tenant_id'] = tempList[i][2]
                        newList[i]['project_id'] = tempList[i][3]
                        
            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                sys.exit(1)   
        else: #Match tenant_id
            try:
                with self.con:
                    cur = self.con.cursor()
                    cur.execute("SELECT * FROM wnet WHERE tenant_id=\'"+str(tenant_id)+"\'")
                    tempList =  cur.fetchall()
                    #Prune thorugh list
                    newList = []
                    for i in range(len(tempList)):
                        newList.append({})
                        newList[i]['wnet_id'] = tempList[i][0]
                        newList[i]['name'] = tempList[i][1]
                        newList[i]['tenant_id'] = tempList[i][2]
                        newList[i]['project_id'] = tempList[i][3]
                        
            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                sys.exit(1)
            
        return newList
    
    def wnet_remove_ap(self, args, tenant_id, user_id, project_id):
        arg_name = args['wnet-remove-ap'][0]
        arg_slice = args['slice']
        #Send to database
        self.auroraDB.wnet_remove_slice(tenant_id, arg_slice, arg_name)
    
    def wnet_list(self, args, tenant_id, user_id, project_id):
        toPrint = self.wnet_fetch(tenant_id)
        for entry in toPrint:
            for attr in entry:
                print(str(attr)+': '+str(entry[attr]))
            print('\n')
            
    
    def wnet_show(self, args, tenant_id, user_id, project_id):
        arg_name = args['wnet-show'][0]
        toPrint = self.wnet_fetch(tenant_id)
        for entry in toPrint:
            if entry['name'] == arg_name:
                for attr in entry:
                    print(str(attr)+': '+str(entry[attr]))
                print('\n')
        
#For Testing
#Manager().parseargs('ap-slice-create', {'filter':['region=mcgill & number_radio<2 & version<1.1 & number_radio_free!2 & supported_protocol=a/b/g'], 'file':['json/slicetemp.json'], 'tag':['first']},1,1,1)
#Manager().parseargs('ap-slice-create', {'ap':['of1', 'of2', 'of3', 'of4'],'file':['json/slicetemp.json'], 'tag':['first']},1,1,1)
#Manager().parseargs('ap-slice-create', {'ap':['of1'],'file':['json/slicetemp.json'], 'tag':['first']},1,1,1)
#Manager().parseargs('ap-list', {'filter':['name=openflow'], 'i':True},1,1,1)
#Manager().parseargs('ap-slice-list', {'filter':[''], 'i':False}, 1,1,1)
Manager().parseargs('wnet_show', {'wnet-show':['wnet-1']}, 0,1,1)