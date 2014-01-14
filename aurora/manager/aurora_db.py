# mySQL Database Functions
# SAVI McGill: Heming Wen, Prabhat Tiwary, Kevin Han, Michael Smith

"""
Collection of methods for adding, updating, deleting, and querying the database
"""

import sys, json, os
import MySQLdb as mdb

class AuroraDB():
    #Default values in __init__ should potentially be omitted
    def __init__(self, 
                 mysql_host = 'localhost', 
                 mysql_username = 'root',
                 mysql_password = 'supersecret', 
                 mysql_db = 'aurora'):
        print "Constructing AuroraDB..."
        #Connect to Aurora mySQL database
        try:
            self.con = mdb.connect(mysql_host, mysql_username,\
                                   mysql_password, mysql_db) #Change address
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)
    
    def __del__(self):
        print "Destructing AuroraDB..."
        if self.con:
            self.con.close()
        else:
            print('Connection already closed!')
    
    def wslice_belongs_to(self, tenant_id, project_id, ap_slice_id):
        if tenant_id == 0:
            return True
        else:
            try:
                with self.con:
                    cur = self.con.cursor()
                    to_execute = ( "SELECT ap_slice_id FROM ap_slice WHERE "
                                   "tenant_id = '%s' AND "
                                   "project_id = '%s'" % (tenant_id, project_id) )
                    cur.execute(to_execute)
                    tenant_ap_slices_tt = cur.fetchall()
                    tenant_ap_slices = []
                    for tenant_t in tenant_ap_slices_tt:
                        tenant_ap_slices.append(tenant_t[0])
                    if ap_slice_id in tenant_ap_slices:
                        return True

            except mdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                sys.exit(1)
        return False
    
    #TODO: This function is untested
    def wnet_belongs_to(self, tenant_id, project_id, wnet_name):
        if tenant_id == 0:
            return True
        else:
            try:
                with self.con:
                    cur = self.con.cursor()
                    to_execute = ( "SELECT name, wnet_id FROM wnet WHERE "
                                   "tenant_id = '%s' AND "
                                   "project_id = '%s'" % (tenant_id, project_id) )
                    cur.execute(to_execute)
                    tenant_wnets_tt = cur.fetchall()
                    tenant_wnets = []
                    for t in tenant_wnets_tt:
                        tenant_wnets.append(t[0])
                        tenant_wnets.append(t[1])
                    if wnet_name in tenant_wnets:
                        return True
            except mdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    sys.exit(1)
        return False

    def wslice_has_tag(self, ap_slice_id, tag):
        try:
            with self.con:
                cur = self.con.cursor()
                to_execute = ( "SELECT name FROM tenant_tags WHERE "
                               "ap_slice_id = '%s'" % ap_slice_id )
                cur.execute(to_execute)
                ap_slice_tags_tt = cur.fetchall()
                ap_slice_tags = []
                for tag_t in ap_slice_tags_tt:
                    ap_slice_tags.append(tag_t[0])
                if tag in ap_slice_tags:
                    return True
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)
        return False
            
    def wslice_physical_ap(self, ap_slice_id):
        try:
            with self.con:
                cur = self.con.cursor()
                to_execute = ( "SELECT physical_ap FROM ap_slice WHERE "
                               "ap_slice_id='%s'" % ap_slice_id )
                db.execute(to_execute)
                return db.fetchone()[0]
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)

    def wnet_add_wslice(self, tenant_id, slice_id, name):
        try:
            with self.con:
                #First get wnet-id
                cur = self.con.cursor()
                to_execute = ( "SELECT wnet_id FROM wnet WHERE "
                               "wnet_id='%s' OR "
                               "name='%s'" % (name, name) )
                cur.execute(to_execute)
                wnetID = cur.fetchone()[0]
                
                #TODO: Check if already exists
                to_execute = ( "SELECT ap_slice_id FROM ap_slice WHERE "
                               "wnet_id = '%s'" % wnetID )
                cur.execute(to_execute)
                ap_slice_id_tt = cur.fetchall()
                ap_slice_id = []
                for id_t in ap_slice_id_tt:
                    ap_slice_id.append(id_t[0])
                if slice_id in ap_slice_id:
                    return "Slice '%s' already in '%s'.\n" % (slice_id, name)
                else:
                    #Update to SQL database
                    to_execute = ( "UPDATE ap_slice SET wnet_id='%s' WHERE "
                                   "ap_slice_id='%s'" % (wnetID, slice_id) )
                    cur.execute(to_execute)
                    return "Added '%s' to '%s'.\n" % (slice_id, name)
        
        except mdb.Error, e:
            err_msg = "Error %d: %s" % (e.args[0], e.args[1])
            print err_msg
            return err_msg + '\n'
           
    def wnet_remove_wslice(self, tenant_id, slice_id, name):        
        #Update to SQL database
        try:
            with self.con:
                #First get wnet-id
                cur = self.con.cursor()
                to_execute = ( "SELECT wnet_id FROM wnet WHERE "
                               "wnet_id='%s' OR "
                               "name='%s'" % (name, name) )
                cur.execute(to_execute)
                wnetID = cur.fetchone()[0]
                
                #Update to SQL database
                to_execute = ( "UPDATE ap_slice SET wnet_id=NULL WHERE "
                               "ap_slice_id='%s' AND "
                               "wnet_id='%s'" % (slice_id, wnetID) )
                cur.execute(to_execute)
                #TODO: Add messaging
        except mdb.Error, e:
            err_msg = "Error %d: %s" % (e.args[0], e.args[1])
            print err_msg
            return err_msg + '\n'
            
    def wnet_add(self, wnet_id, name, tenant_id, project_id):
        
        #Update the SQL database
        try:
            with self.con:
                cur = self.con.cursor()
                to_execute = ( "SELECT wnet_id FROM wnet WHERE "
                               "name = '%s' AND tenant_id = '%s'" % (name, tenant_id) )
                cur.execute(to_execute)
                wnet_id_tt = cur.fetchall()
                if len(wnet_id_tt) > 0:
                    return "You already own '%s'.\n" % name
                else:

                    to_execute = ( "INSERT INTO wnet VALUES ('%s', '%s', %s, %s)" %
                                   (wnet_id, name, tenant_id, project_id) )
                    cur.execute(to_execute)
                    return "Created '%s'.\n" % name
        except mdb.Error, e:
            err_msg = "Error %d: %s" % (e.args[0], e.args[1])
            print err_msg
            return err_msg + '\n'

    def wnet_remove(self, wnet_id):
        #Update the SQL database, at this point we know the wnet exists under the specified tenant
        try:
            with self.con:
                cur = self.con.cursor()
                to_execute = ( "DELETE FROM wnet WHERE "
                               "name='%s' OR "
                               "wnet_id='%s'" % (wnet_id, wnet_id) )
                cur.execute(to_execute)
        
        except mdb.Error, e:
            err_msg = "Error %d: %s" % (e.args[0], e.args[1])
            print err_msg
            return err_msg + '\n'
    
    def wslice_add(self, slice_uuid, tenant_id, physAP, project_id):
        try:
            with self.con:
                cur = self.con.cursor()
                to_execute = ( "INSERT INTO ap_slice VALUES ('%s', %s, '%s', %s, %s, '%s')" %
                               (slice_uuid,  tenant_id, physAP,
                                project_id, "NULL", "PENDING") )
                print to_execute
                cur.execute(to_execute)
                return "Added slice %s on %s.\n" % (slice_uuid, physAP)
        except mdb.Error, e:
            err_msg = "-->> Error %d: %s" % (e.args[0], e.args[1])
            print err_msg
            return err_msg + '\n'
    
    def wslice_delete(self, slice_id):
        #Update SQL database and JSON file
        #Remove tags
        try:
            with self.con:
                cur = self.con.cursor()
                to_execute = ( "UPDATE ap_slice SET status='DELETING' WHERE "
                               "ap_slice_id='%s'" % slice_id )
                db.execute(to_execute)
                to_execute = ( "DELETE FROM tenant_tags WHERE "
                               "ap_slice_id='%s'" % slice_id )
                db.execute(to_execute)
                return "Deleted slice %s.\n" % slice_id
        except mdb.Error, e:
            err_msg = "Error %d: %s" % (e.args[0], e.args[1])
            print err_msg
            return err_msg + '\n'
        
    def wslice_add_tag(self, ap_slice_id, tag):
        if self.wslice_has_tag(ap_slice_id, tag):
            return "Tag '%s' already exists for ap_slice '%s'\n" % (tag, ap_slice_id)
        else:
            try:
                with self.con:
                    cur = self.con.cursor()
                    to_execute = "INSERT INTO tenant_tags VALUES (%s, '%s')" % (tag, ap_slice_id)      
                    cur.execute(to_execute)
                    return "Added tag '%s' to ap_slice '%s'.\n" % (tag, ap_slice_id)
            except mdb.Error, e:
                err_msg = "Error %d: %s\n" % (e.args[0], e.args[1])
                print err_msg
                return err_msg + '\n'
    
    def wslice_remove_tag(self, ap_slice_id, tag):
        if self.wslice_has_tag(ap_slice_id, tag):
            try:
                with self.con:
                    cur = self.con.cursor()
                    to_execute = ( "DELETE FROM tenant_tags WHERE "
                                   "name='%s' AND ap_slice_id='%s'" %
                                   (tag, ap_slice_id) )
                    cur.execute(to_execute)
                    return "Deleted tag '%s' from ap_slice '%s'\n" % (tag, ap_slice_id)
            except mdb.Error, e:
                err_msg = "Error %d: %s\n" % (e.args[0], e.args[1])
                print err_msg
                return err_msg + '\n'
        else:
            return "Tag '%s' not found.\n" % (tag)
            
         
    def wnet_join(self, tenant_id, name):
        pass #TODO AFTER SAVI INTEGRATION
      
      
        
        
        










