from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, Namespace, Literal, Graph, XSD, BNode
from urllib.parse import quote
from ReadingEmvistaJson import get_emvista_events_ids, process_em_graph, process_new_em_graph
import os
import json
from dateutil.parser import parse
import io
import pydotplus
from IPython.display import display, Image
from rdflib.tools.rdf2dot import rdf2dot
import pandas as pd
from owlrl import OWLRL
from rdflib.plugins.sparql import prepareUpdate
import argparse
from datetime import datetime
from tqdm import tqdm  # Import the tqdm module



class OntologyPopulationFunction:
    """ Base class for converter"""
    
    def __init__(self):
        self.ns_sem = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")
        self.ns_faro = Namespace("http://purl.org/faro/")
        self.ns_xpEvent = Namespace("http://www.irit.fr/xpEvent/")
    @staticmethod
    def createObject(prefix,text) :
        final=text.replace(" ", "_").replace("(", "").replace(")", "")
        return URIRef(prefix+final)

    @staticmethod
    def is_triple_in_graph(triple, graph):
        """ Checking if triple in graph """
        return triple in graph
    @staticmethod
    def is_date(string, fuzzy=False):
        """
        Return whether the string can be interpreted as a date.

        :param string: str, string to check for date
        :param fuzzy: bool, ignore unknown tokens in string if True
        """
        try: 
            parse(string, fuzzy=fuzzy)
            return True

        except ValueError:
            #print("VALUE ERROR")
            return False
        
    @staticmethod
    def getURI(graph, id):
        request = "Select ?value WHERE{?value  xpEvent:hasEmvistaID  '"+str(id)+"'^^xsd:string .}"
        result = graph.query(request)
        for res in result:
            return res[0]
        return None

    def getType(self,graph,id_in_graph):
        request = "Select ?value WHERE {<"+str(id_in_graph)+"> rdf:type ?value.}"
        result = graph.query(request)
        for res in result:
            return res[0].rsplit('/', 1)[-1]
        return None

    def getActorType(self,graph,id_in_graph):
        request = f"""SELECT ?value WHERE {{{{Select ?x WHERE{{<{str(id_in_graph)}> rdf:type sem:Actor. <{str(id_in_graph)}> sem:actorType ?x.}}}} ?x a sem:ActorType. ?x rdfs:label ?value.}}"""
        #print(request)
        result = graph.query(request)
        for res in result:
            return res[0]
        return None

    def getPlaceType(self,graph,id_in_graph):
        request = f"""SELECT ?value WHERE {{{{Select ?x WHERE{{<{str(id_in_graph)}> rdf:type sem:Place. <{str(id_in_graph)}> sem:placeType ?x.}}}} ?x a sem:PlaceType. ?x rdfs:label ?value.}}"""
        #print(request)
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    def getEventType(self,graph,id_in_graph):
        request = f"""SELECT ?value WHERE {{{{Select ?x WHERE{{<{str(id_in_graph)}> rdf:type sem:Event. <{str(id_in_graph)}> sem:eventType ?x.}}}} ?x a sem:EventType. ?x rdfs:label ?value.}}"""
        #print(request)
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    @staticmethod
    def getAncestorURI(graph, nodeURI):
        request = "Select ?value WHERE{?value  rdf:value  xpEvent:ID_"+str(nodeURI).split('_')[1]+" .}"
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    @staticmethod
    def getRoleTypeIdIfExist(graph, id):
        request = "Select ?value WHERE{?value   rdfs:label  '"+str(id)+"' .}"
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    @staticmethod
    def _add_label(graph, uri, label):
        graph.add((uri, RDFS.label, Literal(label)))
        return graph

    def _add_event(self, graph, event_data_properties,id):
        #Adding new codes
        event_exist_id = self.getURI(graph,event_data_properties['id'])
        if(event_exist_id!=None):
            event = event_exist_id
            id_type = self.getType(graph, event_exist_id)
        else:
            event = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1

        """ Init event triples in graph """
        graph.add((URIRef(event), RDF.type, self.ns_xpEvent.Event))
        graph.add((URIRef(event),self.ns_xpEvent.hasEmvistaID, Literal(event_data_properties['id'],datatype=XSD.string)))
        graph.add((URIRef(event),self.ns_xpEvent.hasEmvistaSemanticClass, Literal(event_data_properties['value'])))
        graph.add((URIRef(event),self.ns_xpEvent.hasEmvistaSource, Literal(event_data_properties['source'],lang='fr')))
        return id, graph, event
    
    def _add_place(self,graph, event, id, location_details):
        #Adding new codes
        #location_details = {'id':arg['id'], 'place_role':arg['role'], 'place_label':arg['value'], 'place_type':place_type}
        place_exist_id = self.getURI(graph,location_details['id'])
        if(place_exist_id!=None):
            place_instance = place_exist_id
        #End of new codes
        #creating blank node named actor_instance
        else:
            place_instance = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1
            graph.add((URIRef(place_instance), RDF.type, self.ns_sem.Place))
            graph.add((URIRef(place_instance),RDFS.label, Literal(location_details['place_label'],lang='fr')))
            graph.add((URIRef(place_instance),self.ns_xpEvent.hasEmvistaID, Literal(location_details['id'],datatype=XSD.string)))
        
        place_role = self.getRoleTypeIdIfExist(graph,location_details['place_role'])
        if(place_role==None):
            place_role = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1
            graph.add((URIRef(place_role),RDFS.label, Literal(location_details['place_role'])))
        #graph = self._add_actor_type(graph,actor_instance,actor_role)
        
        if(len(location_details['place_type'])):
            place_type = self.getRoleTypeIdIfExist(graph,location_details['place_type'])
            if(place_type==None):
                place_type = self.ns_xpEvent[f"ID_{str(id)}"]
                id = id+1
                graph.add((URIRef(place_type),RDFS.label, Literal(location_details['place_type'])))
            graph = self._add_location_type(graph,place_instance,place_type)
        
        blank_n = self.ns_xpEvent[f"ID_{str(id)}"]
        id = id+1
        graph = self._add_blank_node_attribute_place(graph, blank_n=blank_n,subj_event = event,obj_place=place_instance,obj_place_role=place_role)
        
        return id, graph
    def _add_actor(self, graph, event , id, actor_details):
        #Adding new codes
        actor_exist_id = self.getURI(graph,actor_details['id'])
        if(actor_exist_id!=None):
            actor_instance = actor_exist_id
        #End of new codes
        #creating blank node named actor_instance
        else:
            actor_instance = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1
            graph.add((URIRef(actor_instance), RDF.type, self.ns_sem.Actor))
            graph.add((URIRef(actor_instance),RDFS.label, Literal(actor_details['actor_label'],lang='fr')))
            graph.add((URIRef(actor_instance),self.ns_xpEvent.hasEmvistaID, Literal(actor_details['id'],datatype=XSD.string)))
        
        actor_role = self.getRoleTypeIdIfExist(graph,actor_details['actor_role'])
        if(actor_role==None):
            actor_role = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1
            graph.add((URIRef(actor_role),RDFS.label, Literal(actor_details['actor_role'])))
        #graph = self._add_actor_type(graph,actor_instance,actor_role)
        
        if(len(actor_details['actor_type'])):
            actor_type = self.getRoleTypeIdIfExist(graph,actor_details['actor_type'])
            if(actor_type==None):
                actor_type = self.ns_xpEvent[f"ID_{str(id)}"]
                id = id+1
                graph.add((URIRef(actor_type),RDFS.label, Literal(actor_details['actor_type'])))
            graph = self._add_actor_type(graph,actor_instance,actor_type)
        
        blank_n = self.ns_xpEvent[f"ID_{str(id)}"]
        id = id+1
        graph = self._add_blank_node_attribute_actor(graph, blank_n=blank_n,subj_event = event,obj_actor=actor_instance,obj_actor_role=actor_role)
        
        return id, graph
    
    def _add_time(self,graph, event, time_detials):
        sel_time = {'Time':'hasTimeStamp','TimeMin':'hasLatestBeginTimeStamp', 'TimeMax':'hasLatestEndTimeStamp','TimeExact':'hasTimeStamp'}
        if(time_detials['role'] in sel_time):
            predicate = self.createObject(self.ns_sem,sel_time[time_detials['role']])
            graph.add((event, predicate, Literal(time_detials['value'],datatype=XSD.string)))
        return graph

    def _add_discourse_connection(self, graph, dc_detail,dc_list):
        sel_dc = {'Cause':'has_cause','Consequence':'has_consequence','Opposition':'opposition','Comparison':'compared_to','Condition':'condition','Illustration':'illustration','Purpose':'purpose',
                  'Explanation':'explanation','Restriction':'restriction','Enumeration':'enumeration','Whatever':'whatever','Conclusion':'conclusion','Alternative':'alternative',"TimeDuration":'temporally_related_to'}
        subj = self.getURI(graph, dc_detail['from'])
        obj = self.getURI(graph, dc_detail['to'])

        if(dc_detail['role'] in sel_dc):
            predicate = self.createObject(self.ns_xpEvent,sel_dc[dc_detail['role']])
            graph.add((URIRef(subj),URIRef(predicate),URIRef(obj)))
            dc_list.append(dc_detail['role'])

        elif(dc_detail['role'] in ['TimeMax','TimeMin']):
            predicate = self.ns_xpEvent.before
            graph.add((subj,predicate,obj))
            dc_list.append(dc_detail['role'])
        
        return dc_list, graph
    
    @staticmethod
    def _get_variables(row):
        return URIRef(row.wd_page), URIRef(row.object), row.objectLabel, row.predicate

    def _add_instance_of(self, graph, row, counter):
        sub, obj, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.eventType, obj))
        graph.add((obj, RDF.type, self.ns_sem.EventType))
        return self._add_label(graph=graph, uri=obj, label=obj_l), counter

    def _add_blank_node_attribute_actor(self,graph,blank_n, subj_event, obj_actor,obj_actor_role):
        graph.add((subj_event, self.ns_sem.hasActor, blank_n))
        graph.add((blank_n, RDF.type, self.ns_sem.Role))
        graph.add((blank_n, RDF.value, obj_actor))
        graph.add((blank_n, self.ns_sem.roleType, obj_actor_role))
        graph.add((obj_actor_role, RDF.type, self.ns_sem.RoleType))
        return graph

    def _add_blank_node_attribute_place(self,graph,blank_n, subj_event, obj_place,obj_place_role):
        graph.add((subj_event, self.ns_sem.hasPlace, blank_n))
        graph.add((blank_n, RDF.type, self.ns_sem.Role))
        graph.add((blank_n, RDF.value, obj_place))
        graph.add((blank_n, self.ns_sem.roleType, obj_place_role))
        graph.add((obj_place_role, RDF.type, self.ns_sem.RoleType))
        return graph
    
    def _add_actor_type(self,graph,sub,obj):
        graph.add((sub, self.ns_sem.actorType, obj))
        graph.add((obj, RDF.type, self.ns_sem.ActorType))
        return graph #self._add_label(graph=graph, uri=obj, label=obj_l), counter

    def _add_location(self, graph, event, location_details,id):
        """ Init event triples in graph """
        place_id = self.getURI(graph,location_details['id'])
        if(place_id!=None):
            place = place_id
            graph.add((URIRef(event),self.ns_sem.hasPlace, URIRef(place)))
        else:
            place = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1 
            graph.add((URIRef(event),self.ns_sem.hasPlace, URIRef(place)))
            graph.add((URIRef(place), RDF.type, self.ns_sem.Place))
            graph.add((URIRef(place),self.ns_xpEvent.hasEmvistaID, Literal(location_details['id'],datatype=XSD.string)))          
            graph.add((URIRef(place),RDFS.label, Literal(location_details['value'],lang='fr')))
            if(len(location_details['tags'])):
                location_type = location_details['tags'][0].split('/')[-1]
                graph.add((URIRef(place),RDFS.label, Literal('Tag: '+location_type)))
        return id,graph
    
    def _add_location_type(self,graph,sub,obj):
        graph.add((sub, self.ns_sem.placeType, obj))
        graph.add((obj, RDF.type, self.ns_sem.PlaceType))
        return graph #self._add_label(graph=graph, uri=obj, label=obj_l), counter 
    
    def _add_event_type(self,graph,sub,obj):
        graph.add((sub, self.ns_sem.eventType, obj))
        graph.add((obj, RDF.type, self.ns_sem.EventType))
        return graph #self._add_label(graph=graph, uri=obj, label=obj_l), counter 
    
    def _add_identity(self, graph,source_id,target_id):
        subj = self.getURI(graph,source_id)
        obj = self.getURI(graph,target_id)
        if(subj!=None and obj!=None):
            graph.add((subj,OWL.sameAs,obj))
        return graph

    def visualize(self, graph,fileName):
        stream = io.StringIO()
        rdf2dot(graph, stream, opts = {display} )
        dg = pydotplus.graph_from_dot_data(stream.getvalue())
        png = dg.create_png()
        dg.write_png(fileName+'.png')
        display(Image(png))

    def getEventID(self, graph,addition_id):
        request = """SELECT DISTINCT ?event ?type where {
        {SELECT DISTINCT ?hasactor WHERE {
        {SELECT DISTINCT ?actor WHERE { ?actor a sem:Actor. ?actor xpEvent:hasEmvistaID ?value. FILTER (DATATYPE(?value) = xsd:string && ?value = \"%s\")}}
        ?hasactor a sem:Role.
        ?hasactor rdf:value ?actor.}}
        ?event a xpEvent:Event.
        ?event ?type ?hasactor.}
        """%addition_id
        result = graph.query(request)
        return result
    
    def getEventIDPlace(self, graph,addition_id):
        request = """SELECT DISTINCT ?event ?type where {
        {SELECT DISTINCT ?hasPlace WHERE {
        {SELECT DISTINCT ?place WHERE { ?place a sem:Place. ?place xpEvent:hasEmvistaID ?value. FILTER (DATATYPE(?value) = xsd:string && ?value = \"%s\")}}
        ?hasPlace a sem:Role.
        ?hasPlace rdf:value ?place.}}
        ?event a xpEvent:Event.
        ?event ?type ?hasPlace.}
        """%addition_id
        result = graph.query(request)
        return result
    
    def add_addition_as_events(self, graph,addition_details,id,disc_conn,dc_list,events_id):
        discourse_connection = ['Cause','Consequence','Opposition','Conclusion','Comparison','Condition','Illustration','Purpose','Restriction','Explanation','Whatever','Alternative']
        emvista_location = ['Destination','Location','LocationSource','LocationDestination','LocationExact']
        emvista_time = ['Time','TimeExact','TimeFuzzy','TimeMin','TimeMax','TimeDuration']
        exist_events = []
        emivista_events_id = []
        for arg in addition_details['arguments']:
            if(arg['role']=='Addition'):
                event_id = self.getURI(graph,arg['id'])
                if(event_id!=None):
                    exist_events.append(event_id)
                    emivista_events_id.append(arg['id'])
                    graph.add((URIRef(event_id),self.ns_xpEvent.hasEmvistaAdditionId, Literal(addition_details['id'],datatype=XSD.string)))
            elif(arg['role'] in discourse_connection):
                for ee in emivista_events_id:
                    dc = {'role':arg['role'],'from':ee,'to':arg['id']}
                    event_id = self.getURI(graph,arg['id'])
                    if(event_id!=None):
                        dc_list,graph = self._add_discourse_connection(graph,dc,dc_list)    
            elif(arg['role'] in emvista_location):
                for ee in exist_events:
                    id, graph = self._add_location(graph,ee,arg,id)

            
        for dc in disc_conn:
            if(dc['role'] not in emvista_time and dc['value']=='et'):
                for ee in emivista_events_id:
                    dc ['to']= ee
                    dc_list, graph = self._add_discourse_connection(graph,dc,dc_list)          
        return id,graph,dc_list
    
    def addition_checker(self, property, addition_id):
        return None
    
    def delete_addition_node_as_actor(self,graph, addition_URI,event,relation_type):
        #Step 1: Delete addition_URI
        sparql_query = f"""
        DELETE WHERE {{
            <{addition_URI}> ?predicate ?object .
        }}
        """
        graph.update(sparql_query)

        #Step 2: DELETING ALL THE INSTANCES OF ADDITOIN URI from the GRAPH
        # i) Find where addition URI was connected
        query = f"""
        SELECT DISTINCT ?hasactor WHERE{{?hasactor a sem:Role. ?hasactor rdf:value <{addition_URI}>.}}"""
        result = graph.query(query)
        #print("LEN: "+str(len(result)))
        for r in result:
            sparql_query = f"""
            DELETE WHERE {{
                <{str(r['hasactor'])}> ?predicate ?object .
            }}
            """
            # Execute the SPARQL DELETE query as a string
            graph.update(sparql_query)
            #print("ACTOR:"+str(r['hasactor']))
            graph.remove((event,URIRef(relation_type),URIRef(str(r['hasactor']))))

    def delete_addition_node_as_place(self,graph, addition_URI,event,relation_type):
        #Step 1: Delete addition_URI
        sparql_query = f"""
        DELETE WHERE {{
            <{addition_URI}> ?predicate ?object .
        }}
        """
        graph.update(sparql_query)

        #Step 2: DELETING ALL THE INSTANCES OF ADDITOIN URI from the GRAPH
        # i) Find where addition URI was connected
        query = f"""
        SELECT DISTINCT ?hasPlace WHERE{{?hasPlace a sem:Role. ?hasPlace rdf:value <{addition_URI}>.}}"""
        result = graph.query(query)
        #print("LEN: "+str(len(result)))
        for r in result:
            sparql_query = f"""
            DELETE WHERE {{
                <{str(r['hasPlace'])}> ?predicate ?object .
            }}
            """
            # Execute the SPARQL DELETE query as a string
            graph.update(sparql_query)
            #print("ACTOR:"+str(r['hasactor']))
            graph.remove((event,URIRef(relation_type),URIRef(str(r['hasPlace']))))

    def _addition_actors(self,graph, addition_details,event_id,id):
        for index, arg in enumerate(addition_details['arguments']):
            #print('ARGUMENT: '+str(index)+"\tDETAILS: "+str(arg))
            ##################################################################
            #Adding new codes
            actor_exist_id = self.getURI(graph,arg['id'])
            if(actor_exist_id!=None):
                #print('it exist')
                actor_instance = actor_exist_id
                graph.add((URIRef(actor_instance),self.ns_xpEvent.hasEmvistaAdditionId, Literal(addition_details['id'],datatype=XSD.string)))
                graph.add((URIRef(actor_instance), RDF.type, self.ns_sem.Actor))
            #End of new codes
            #creating blank node named actor_instance
            else:
                actor_instance = self.ns_xpEvent[f"ID_{str(id)}"]
                id = id+1
                graph.add((URIRef(actor_instance), RDF.type, self.ns_sem.Actor))
                graph.add((URIRef(actor_instance),RDFS.label, Literal(arg['value'],lang='fr')))
                graph.add((URIRef(actor_instance),self.ns_xpEvent.hasEmvistaID, Literal(arg['id'],datatype=XSD.string)))
                #graph.add((URIRef(actor_instance),self.ns_xpEvent.hasEmvistaID, Literal(arg['id'],datatype=XSD.string)))
                graph.add((URIRef(actor_instance),self.ns_xpEvent.hasEmvistaAdditionId, Literal(addition_details['id'],datatype=XSD.string)))
                #ADDITION id NEEDS TO BE ADDED FOR REFERENCE
            
            actor_role = self.getRoleTypeIdIfExist(graph,arg['role'])
            if(actor_role==None):
                actor_role = self.ns_xpEvent[f"ID_{str(id)}"]
                id = id+1
                graph.add((URIRef(actor_role),RDFS.label, Literal(arg['role'])))
            #graph = self._add_actor_type(graph,actor_instance,actor_role)
            actor_type=''
            if(len(arg['tags'])):
                actor_type = arg['tags'][0].split('/')[-1]
                if(len(actor_type)):
                    actor_type = self.getRoleTypeIdIfExist(graph,actor_type)
                    if(actor_type==None):
                        actor_type = self.ns_xpEvent[f"ID_{str(id)}"]
                        id = id+1
                        graph.add((URIRef(actor_type),RDFS.label, Literal(actor_type)))
                graph = self._add_actor_type(graph,actor_instance,actor_type)
            
            blank_n = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1
            graph = self._add_blank_node_attribute_actor(graph, blank_n=blank_n,subj_event = event_id,obj_actor=actor_instance,obj_actor_role=actor_role)
        return id,graph
    
    def _addition_places(self,graph, addition_details,event_id,id):
        for index, arg in enumerate(addition_details['arguments']):
            place_exist_id = self.getURI(graph,arg['id'])
            if(place_exist_id!=None):
                place_instance = place_exist_id
                graph.add((URIRef(place_instance),self.ns_xpEvent.hasEmvistaAdditionId, Literal(addition_details['id'],datatype=XSD.string)))
                graph.add((URIRef(place_instance), RDF.type, self.ns_sem.Place))
            #End of new codes
            #creating blank node named actor_instance
            else:
                place_instance = self.ns_xpEvent[f"ID_{str(id)}"]
                id = id+1
                graph.add((URIRef(place_instance), RDF.type, self.ns_sem.Place))
                graph.add((URIRef(place_instance),RDFS.label, Literal(arg['value'],lang='fr')))
                graph.add((URIRef(place_instance),self.ns_xpEvent.hasEmvistaID, Literal(arg['id'],datatype=XSD.string)))
            
            place_role = self.getRoleTypeIdIfExist(graph,arg['role'])
            if(place_role==None):
                place_role = self.ns_xpEvent[f"ID_{str(id)}"]
                id = id+1
                graph.add((URIRef(place_role),RDFS.label, Literal(arg['role'])))
            #graph = self._add_actor_type(graph,actor_instance,actor_role)
            
            if(len(arg['tags'])):
                location_type = arg['tags'][0].split('/')[-1]
                place_type = self.getRoleTypeIdIfExist(graph,location_type)
                if(place_type==None):
                    place_type = self.ns_xpEvent[f"ID_{str(id)}"]
                    id = id+1
                    graph.add((URIRef(place_type),RDFS.label, Literal(location_type)))
                graph = self._add_location_type(graph,place_instance,place_type)
            
            blank_n = self.ns_xpEvent[f"ID_{str(id)}"]
            id = id+1
            graph = self._add_blank_node_attribute_place(graph, blank_n=blank_n,subj_event = URIRef(event_id),obj_place=place_instance,obj_place_role=place_role)
            ####################################################
        
        return id,graph
        
    def add_addition_as_actor(self, graph, addition_details,id,event_id, addition_type):
        addition_URI = self.getURI(graph,addition_details['id'])
        #Steps: i) search event where addition URI is connected
        self.delete_addition_node_as_actor(graph,addition_URI,event_id,addition_type)
        id,graph=self._addition_actors(graph,addition_details,event_id,id)

        return id,graph
    
    def add_addition_as_actor_and_place(self, graph, addition_details,id,event_id, addition_type_actor,addition_type_place):
        addition_URI = self.getURI(graph,addition_details['id'])
        #Steps: i) search event where addition URI is connected
        id,graph=self._addition_actors(graph,addition_details,event_id,id)
        id,graph=self._addition_places(graph,addition_details,event_id,id)
        self.delete_addition_node_as_actor(graph,addition_URI,event_id,addition_type_actor)

        return id,graph
    
    def add_addition_as_place(self, graph, addition_details,id):
        addition_URI = self.getURI(graph,addition_details['id'])
        #Steps: i) search event where addition URI is connected
        gE = self.getEventIDPlace(graph,addition_details['id'])
        if(len(gE)>0):
            event_id = ""
            addition_type = ""
            for e in gE:
                event_id= e['event']
                addition_type = e['type']
                self.delete_addition_node_as_place(graph,addition_URI,event_id,addition_type)
                if("hasPlace" in addition_type):
                    #add as actor
                    id,graph=self._addition_places(graph,addition_details,event_id,id)
                    ##################################################################
            
        return id,graph
  
    def exist_actor_type(self,graph,property_type):
        request = f"""SELECT ?x WHERE {{ ?x a sem:ActorType. ?x rdfs:label "{str(property_type)}".}}"""
        #print(request)
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    def exist_place_type(self,graph,property_type):
        request = f"""SELECT ?x WHERE {{ ?x a sem:PlaceType. ?x rdfs:label "{str(property_type)}".}}"""
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    def exist_event_type(self,graph,property_type):
        request = f"""SELECT ?x WHERE {{ ?x a sem:EventType. ?x rdfs:label "{str(property_type)}".}}"""
        result = graph.query(request)
        for res in result:
            return res[0]
        return None
    
    def _add_type_property(self,graph, subj,prop,id):
        type = self.getType(graph,subj)
        
        if(type=='Actor'):
            #whether ActorType Already exist or not
            actorType = self.getActorType(graph,subj)
            prop_type = prop['arguments'][1]['value'].rsplit('/')[-1]
            
            existence = self.exist_actor_type(graph,prop_type)
            if(((actorType!=None) and (existence!=None)) or ((actorType==None) and (existence!=None))):
                graph = self._add_actor_type(graph,subj,existence)
            elif((actorType!=None) and (str(actorType) != prop_type)):
                    actor_type = self.ns_xpEvent[f"ID_{str(id)}"]
                    id = id+1
                    graph.add((URIRef(actor_type),RDFS.label, Literal(prop_type)))
                    graph = self._add_actor_type(graph,subj,actor_type)
            elif((actorType==None)):
                    actor_type = self.ns_xpEvent[f"ID_{str(id)}"]
                    id = id+1
                    graph.add((URIRef(actor_type),RDFS.label, Literal(prop_type)))
                    self._add_actor_type(graph,subj,actor_type)
                    #print("ACTOR TYPE ADDED FOR SUBJ"+subj+" as "+actor_type)
        elif(type=='Place'):
            #whether ActorType Already exist or not
            placeType = self.getPlaceType(graph,subj)
            prop_type = prop['arguments'][1]['value'].rsplit('/')[-1]
            #print("PROP_TYPE: "+prop_type+" len:"+str(len(prop_type))+"\tmatch: "+ str((str(placeType) == prop_type)))
            existence = self.exist_place_type(graph,prop_type)
            if(((placeType!=None) and (existence!=None)) or ((placeType==None) and (existence!=None))):
                graph = self._add_location_type(graph,subj,existence)
            elif((placeType!=None) and (str(placeType) != prop_type)):
                    placeType = self.ns_xpEvent[f"ID_{str(id)}"]
                    id = id+1
                    graph.add((URIRef(placeType),RDFS.label, Literal(prop_type)))
                    graph = self._add_location_type(graph,subj,placeType)
            elif((placeType==None)):
                    place_Type_instance = self.ns_xpEvent[f"ID_{str(id)}"]
                    id = id+1
                    graph.add((URIRef(place_Type_instance),RDFS.label, Literal(prop_type)))
                    graph = self._add_location_type(graph,subj,place_Type_instance)
                    #print("PROP TYPE: "+str(prop_type)+"ID: "+str(id))
                    #print("ACTOR TYPE ADDED FOR SUBJ"+subj+" as "+actor_type)
        elif(type=='Event'): ##eeg_04.json
            eventType = self.getEventType(graph,subj)
            prop_type = prop['arguments'][1]['value'].rsplit('/')[-1]
            #print("PROP_TYPE: "+prop_type+" len:"+str(len(prop_type))+"\tmatch: "+ str((str(placeType) == prop_type)))
            existence = self.exist_event_type(graph,prop_type)
            if(((eventType!=None) and (existence!=None)) or ((eventType==None) and (existence!=None))):
                    graph = self._add_event_type(graph,subj,existence)
            elif((eventType!=None) and (str(eventType) != prop_type)):
                        eventType = self.ns_xpEvent[f"ID_{str(id)}"]
                        id = id+1
                        graph.add((URIRef(eventType),RDFS.label, Literal(prop_type)))
                        graph = self._add_event_type(graph,subj,eventType)
            elif((eventType==None)):
                    event_Type_instance = self.ns_xpEvent[f"ID_{str(id)}"]
                    id = id+1
                    graph.add((URIRef(event_Type_instance),RDFS.label, Literal(prop_type)))
                    graph = self._add_event_type(graph,subj,event_Type_instance)
            #print(prop) 
        return id,graph
    
    def _add_point_in_time(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_begin_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasBeginTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_end_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasEndTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_earliest_begin_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasEarliestBeginTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_earliest_end_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasEarliestEndTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_latest_begin_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasLatestBeginTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def _add_latest_end_ts(self, graph, row, counter):
        sub, _, obj_l, _ = self._get_variables(row)
        graph.add((sub, self.ns_sem.hasLatestEndTimeStamp, Literal(obj_l,datatype=XSD.date)))
        return graph, counter

    def __call__(self, graph, df_info):
        return graph

    def _blank_node(self, id_counter):
        blank_n = self.ns_xpEvent[f"ID_{str(id_counter)}"]
        id_counter = id_counter+1
        #nodeIndividualName = URIRef(blank_n)
        #graph.add(B)
        return id_counter,blank_n

    def sparqlQuery(self,graph):
        #request = "SELECT DISTINCT ?eventID ?eventName ?actorID ?roleID WHERE {?eventID rdf:type xpEvent:Event . ?eventID rdfs:label ?eventName . ?eventID sem:hasActor ?actorID . ?actorID rdf:value ?actorV. ?actorID sem:roleType ?roleID}ORDER BY (?eventID)"
        '''request = """SELECT DISTINCT ?eventName ?actorV 
                   WHERE {
                    ?eventID rdf:type xpEvent:Event . 
                    ?eventID rdfs:label ?eventName . 
                    ?eventID sem:hasActor ?actorID . 
                    ?actorID rdf:value ?actorVID. 
                    ?actorVID rdfs:label ?actorV. 
                    ?actorID sem:roleType ?roleID
                }ORDER BY (?eventID)"""
        '''
        request = """SELECT DISTINCT ?eventID  ?eventName ?actorID ?roleID ?actorV ?hasLBTS ?hasLETS
        WHERE {
            ?eventID rdf:type xpEvent:Event .
            ?eventID rdfs:label ?eventName .
            ?eventID sem:hasActor ?actorID .
            
            OPTIONAL{
                ?eventID sem:hasLatestEndTimeStamp ?hasLETS .
                ?eventID sem:hasLatestBeginTimeStamp ?hasLBTS.    
            }
            FILTER(lang(?eventName)= "")
        }ORDER BY (?eventName)"""
        result = graph.query(request)
        
        return result
    
def init_graph():
        """ Init empty graph with namespaces"""
        graph = Graph()
        graph.bind("sem", Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/"))
        graph.bind("faro", Namespace("http://purl.org/faro/"))
        graph.bind("xpEvent", Namespace("http://www.irit.fr/xpEvent/"))
        return graph

def sparqlQuery(graph):
    #request = "SELECT DISTINCT ?eventID ?eventName ?actorID ?roleID WHERE {?eventID rdf:type xpEvent:Event . ?eventID rdfs:label ?eventName . ?eventID sem:hasActor ?actorID . ?actorID rdf:value ?actorV. ?actorID sem:roleType ?roleID}ORDER BY (?eventID)"
    '''request = """SELECT DISTINCT ?eventName ?actorV 
                WHERE {
                ?eventID rdf:type xpEvent:Event . 
                ?eventID rdfs:label ?eventName . 
                ?eventID sem:hasActor ?actorID . 
                ?actorID rdf:value ?actorVID. 
                ?actorVID rdfs:label ?actorV. 
                ?actorID sem:roleType ?roleID
            }ORDER BY (?eventID)"""
    '''
    #in sparql query # is used to add the
    request = """SELECT DISTINCT ?eventID  ?eventName ?actorID ?roleID ?actorV ?roleV ?placeV ?hasTS ?hasLBTS ?hasLETS ?hasEBTS ?hasEETS ?consequence ?causedBy
                WHERE {
                    ?eventID rdf:type xpEvent:Event; #WHAT: Happened
                            rdfs:label ?eventName .
                    OPTIONAL{#WHO
                        ?eventID sem:hasActor ?actorID . 
                        ?actorID rdf:value ?actorVID;
                                sem:roleType ?roleID.  
                        ?actorVID rdfs:label ?actorV. 
                        ?roleID rdfs:label ?roleV.
                    }
                    OPTIONAL{ #WHY caused by 
                        ?eventID xpEvent:causes ?caused. 
                        ?caused rdfs:label ?causedBy.
                        FILTER(lang(?causedBy)= "fr")
                    }
                    OPTIONAL{#Why 
                        ?eventID xpEvent:is_consequence_of ?cons.
                        ?cons rdfs:label ?consequence.
                        FILTER(lang(?consequence)= "fr")
                    }
                    OPTIONAL{#WHERE
                        ?eventID sem:hasPlace ?placeID.
                        ?placeID rdfs:label ?placeV.
                        FILTER(lang(?placeV)="fr")
                    }
                    OPTIONAL{?eventID sem:hasTimeStamp ?hasTS.} #WHEN
                    OPTIONAL{?eventID sem:hasLatestBeginTimeStamp ?hasLBTS.} #WHEN
                    OPTIONAL{?eventID sem:hasLatestEndTimeStamp ?hasLETS.} #WHEN
                    OPTIONAL{?eventID sem:hasEarliestBeginTimeStamp ?hasEBTS.} #WHEN
                    OPTIONAL{?eventID sem:hasEarliestEndTimeStamp ?hasEETS.} #WHEN
                    FILTER(lang(?eventName)= "")
                } ORDER BY (?eventName)""" 
    request1 = """SELECT DISTINCT ?eventID  ?eventName (group_concat(?actorID) as ?actorIDs) ?placeV ?hasTS ?hasLBTS ?hasLETS ?hasEBTS ?hasEETS ?consequence ?causedBy
                WHERE {
                    ?eventID rdf:type xpEvent:Event; #WHAT: Happened
                            rdfs:label ?eventName .
                    OPTIONAL{#WHO
                        ?eventID sem:hasActor ?actorID . 
                        ?actorID rdf:value ?actorVID;
                                sem:roleType ?roleID.  
                        ?actorVID rdfs:label ?actorV. 
                        ?roleID rdfs:label ?roleV.
                    }
                    OPTIONAL{ #WHY caused by 
                        ?eventID xpEvent:causes ?caused. 
                        ?caused rdfs:label ?causedBy.
                        FILTER(lang(?causedBy)= "fr")
                    }
                    OPTIONAL{#Why 
                        ?eventID xpEvent:is_consequence_of ?cons.
                        ?cons rdfs:label ?consequence.
                        FILTER(lang(?consequence)= "fr")
                    }
                    OPTIONAL{#WHERE
                        ?eventID sem:hasPlace ?placeID.
                        ?placeID rdfs:label ?placeV.
                        FILTER(lang(?placeV)="fr")
                    }
                    OPTIONAL{?eventID sem:hasTimeStamp ?hasTS.} #WHEN
                    OPTIONAL{?eventID sem:hasLatestBeginTimeStamp ?hasLBTS.} #WHEN
                    OPTIONAL{?eventID sem:hasLatestEndTimeStamp ?hasLETS.} #WHEN
                    OPTIONAL{?eventID sem:hasEarliestBeginTimeStamp ?hasEBTS.} #WHEN
                    OPTIONAL{?eventID sem:hasEarliestEndTimeStamp ?hasEETS.} #WHEN
                    FILTER(lang(?eventName)= "")
                } ORDER BY (?eventName)"""
    result = graph.query(request)
    
    return result

def getWs(g):
    request = """SELECT DISTINCT ?eventID ?placeV
                                (GROUP_CONCAT(DISTINCT ?eventName;separator=";") AS ?eventNames) #?eventName
                                #?causedBy
                                #?consequence
                                (GROUP_CONCAT(DISTINCT COALESCE(?placeV,"None"); separator=";") AS ?placeVs)  
                                (GROUP_CONCAT(DISTINCT COALESCE(?actorV,"None"); separator=";") AS ?actorVs) 
                                (GROUP_CONCAT(DISTINCT COALESCE(?roleV,"None");  separator=";") AS ?roleVs)
                                (GROUP_CONCAT(DISTINCT COALESCE(?causedBy,"None"); separator=";") AS ?causedBys)
                                (GROUP_CONCAT(DISTINCT COALESCE(?consequence,"None"); separator=";") AS ?consequences)
                                ?hasTS ?hasLBTS ?hasLETS ?hasEBTS ?hasEETS 
                                WHERE{
                    ?eventID rdf:type xpEvent:Event. #WHAT: Happened
                           
                    OPTIONAL{
                        ?eventID rdfs:label ?eventName .
                        #(GROUP_CONCAT(?eventName,separator=";") AS ?eventNames)
                    }
                    OPTIONAL{#WHO
                        ?eventID sem:hasActor ?actorID. 
                        ?actorID rdf:value ?actorVID;
                                sem:roleType ?roleID.  
                        ?actorVID rdfs:label ?actorV. 
                        ?roleID rdfs:label ?roleV.
                    }
                    OPTIONAL{ #WHY caused by 
                        ?eventID xpEvent:causes ?caused. 
                        ?caused rdfs:label ?causedBy.
                        #FILTER(lang(?causedBy)= "fr")
                    }
                    OPTIONAL{#Why 
                        ?eventID xpEvent:is_consequence_of ?cons.
                        ?cons rdfs:label ?consequence.
                        #FILTER(lang(?consequence)= "fr")
                    }
                    OPTIONAL{#WHERE
                        ?eventID sem:hasPlace ?placeID.
                        ?placeID rdfs:label ?placeV.
                        #FILTER(lang(?placeV)="fr")
                    }
                    OPTIONAL{?eventID sem:hasTimeStamp ?hasTS.} #WHEN
                    OPTIONAL{?eventID sem:hasLatestBeginTimeStamp ?hasLBTS.} #WHEN
                    OPTIONAL{?eventID sem:hasLatestEndTimeStamp ?hasLETS.} #WHEN
                    OPTIONAL{?eventID sem:hasEarliestBeginTimeStamp ?hasEBTS.} #WHEN
                    OPTIONAL{?eventID sem:hasEarliestEndTimeStamp ?hasEETS.} #WHEN
                    #FILTER(lang(?eventName) = "").
                } group by ?eventID
                """
    result = g.query(request)      
    return result

def generate_graph(jsonFile,onto_pop_fun_inst,g, emvista_events,id_counter):
    actors = ['Agent','Pivot','Recipient','Beneficiary','Experiencer','Attribute','Theme','Patient','Topic','Stimulus', 'Product','Asset','Material','Instrument']
    discourse_connection = ['Cause','Consequence','Opposition','Conclusion','Comparison','Condition','Illustration','Purpose','Restriction','Explanation','Whatever','Alternative']
    emvista_time = ['Time','TimeExact','TimeFuzzy','TimeMin','TimeMax','TimeDuration']
    emvista_location = ['Destination','Location','LocationSource','LocationDestination','LocationExact']
    disc_conn =[]
    dc_list = []
    with open(os.path.join(jsonFile), 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
        events, properties = process_new_em_graph(data['result']['predicates'],emvista_events)
        events_id = []
        added_events_id = []
        for event in events:
            event_data_properties = {'id':event['id'],'value':event['value'],'source':event['source']}
            events_id.append(event['id'])
            id_counter, g, eve = onto_pop_fun_inst._add_event(g,event_data_properties,id_counter)
            for arg in event['arguments']:
                if(arg['role'] in actors):
                    actor_type=''
                    if(len(arg['tags'])):
                            actor_type = arg['tags'][0].split('/')[-1]
                    actor_details = {'id':arg['id'], 'actor_role':arg['role'], 'actor_label':arg['value'], 'actor_type':actor_type}
                    id_counter, g = onto_pop_fun_inst._add_actor(g, eve, id_counter, actor_details)

                elif(arg['role'] in discourse_connection):
                    disc_conn.append({'role':arg['role'],'from':event['id'],'to':arg['id'],'value':arg['value']})
                
                elif(arg['role'] in emvista_time):
                    if(onto_pop_fun_inst.is_date(arg['value'])):
                            g = onto_pop_fun_inst._add_time(g,eve,arg)
                    elif(arg['role'] in ['TimeMin','TimeMax']):
                            disc_conn.append({'role':arg['role'],'from':event['id'],'to':arg['id']})
                    else:
                            g = onto_pop_fun_inst._add_time(g,eve,arg)
                                
                elif(arg['role'] in emvista_location):
                    place_type=''
                    if(len(arg['tags'])):
                            place_type = arg['tags'][0].split('/')[-1]
                    location_details = {'id':arg['id'], 'place_role':arg['role'], 'place_label':arg['value'], 'place_type':place_type}
                    id_counter, g = onto_pop_fun_inst._add_place(g, eve, id_counter, location_details)
        counter = 0
        for prop in properties:
            if(prop['value']=='addition'):
                gE = onto_pop_fun_inst.getEventID(g,prop['id'])                        
                if(len(gE)>0):
                    counter +=1
                    addition_type = ""
                    for e in gE:
                        addition_type = e['type']
                        event_id= e['event']
                        if("hasActor" in addition_type):
                                addition_URI = onto_pop_fun_inst.getURI(g,prop['id'])
                                #check whether actor exists or connect to the particular event with same emvista id
                                if(addition_URI!=None):
                                        #check = onto_pop_fun_inst.checkActorExistence(g,event_id,addition_URI)
                                        id_counter, g = onto_pop_fun_inst.add_addition_as_actor(g,prop,id_counter,event_id,addition_type)
                
                gE = onto_pop_fun_inst.getEventIDPlace(g,prop['id'])
                addition_actor_flag = False
                addition_place_flag = False
                event_id = ""
                if(len(gE)>0):
                    addition_type_actor = ""
                    addition_type_place = ""
                    for e in gE:
                        if("hasActor" in str(e['type'])):
                            addition_type_actor = e['type']
                            addition_actor_flag = True
                            event_id = e['event']
                        if("hasPlace" in str(e['type'])):
                            addition_type_place = e['type']
                            addition_place_flag = True
                    if(addition_actor_flag==True and addition_place_flag == True):
                        id_counter,g = onto_pop_fun_inst.add_addition_as_actor_and_place(g, prop,id_counter,event_id, addition_type_actor,addition_type_place)
                    elif(addition_actor_flag==True and addition_place_flag == False):
                        id_counter, g = onto_pop_fun_inst.add_addition_as_actor(g,prop,id_counter,event_id,addition_type_actor)
                    elif(addition_place_flag == True and addition_actor_flag == False):
                        id_counter, g = onto_pop_fun_inst.add_addition_as_place(g,prop,id_counter)
                else:
                    for arg in prop['arguments']:
                        if(arg['role']=='Addition' and (arg['id'] in events_id)):
                            id_counter,g ,dc_list= onto_pop_fun_inst.add_addition_as_events(g,prop,id_counter,disc_conn,dc_list,events_id)
                            break                                
                                
        for prop in properties:
            if(prop['value']=='identity'):
                source_id = str(prop['arguments'][0]['id'])
                target_id = str(prop['arguments'][1]['id'])
                #print("source_Id: "+source_id+"\tt_id: "+target_id)
                g = onto_pop_fun_inst._add_identity(g,source_id,target_id)
            elif(prop['value']=='type'):
                subj = onto_pop_fun_inst.getURI(g, prop['arguments'][0]['id'])
                if(subj!=None):   
                    id_counter,g = onto_pop_fun_inst._add_type_property(g,subj,prop,id_counter)
            elif(prop['value']=='polarity'):
                subj = onto_pop_fun_inst.getURI(g, prop['arguments'][1]['id'])   
                if(subj!=None):
                    g.add((URIRef(subj),onto_pop_fun_inst.ns_xpEvent.hasEmvistaPolarity, Literal(prop['arguments'][0]['value'],datatype=XSD.string)))
                    #print(prop)   
            elif(prop['value']=='aspect'):
                subj = onto_pop_fun_inst.getURI(g, prop['arguments'][1]['id'])   
                if(subj!=None):                                
                    g.add((URIRef(subj),onto_pop_fun_inst.ns_xpEvent.hasEmvistaAspect, Literal(prop['arguments'][0]['value'],datatype=XSD.string)))

        for dc in disc_conn:
            #print("DC: "+str(dc))
            subj = onto_pop_fun_inst.getURI(g, dc['from'])
            obj = onto_pop_fun_inst.getURI(g, dc['to'])
            if(subj!=None and obj!=None):
                dc_list, g = onto_pop_fun_inst._add_discourse_connection(g,dc,dc_list)
        
    return dc_list,g,id_counter
        

def get_et_elements(graph,actorLabel,eventID):
    #request = "SELECT DISTINCT ?eventID ?eventName ?actorID ?roleID WHERE {?eventID rdf:type xpEvent:Event . ?eventID rdfs:label ?eventName . ?eventID sem:hasActor ?actorID . ?actorID rdf:value ?actorV. ?actorID sem:roleType ?roleID}ORDER BY (?eventID)"
        request = "SELECT ?firstIDL ?restIDL WHERE {<"+eventID+"> sem:hasActor ?actorID.  ?actorID rdf:value ?actorVID. ?actorVID rdfs:label \""+actorLabel+"\"@fr. ?actorVID rdf:first ?firstID. ?firstID rdfs:label ?firstIDL. ?actorVID rdf:rest ?restID. ?restID rdfs:label ?restIDL. FILTER(lang(?firstIDL)=\"fr\").FILTER(lang(?restIDL)=\"fr\").}"
        #print(request)
        result = graph.query(request)
        return result
def temp(graph):
        request = "Select ?s ?p ?o WHERE{?s  ?p ?o.}"
        result = graph.query(request)
        return result

def main(args):
    data_dir = args.data_dir
    input_dir = os.path.join(data_dir, args.input_dir)
    save_dir = os.path.join(data_dir, args.save_dir)
    
    emvista_events = get_emvista_events_ids("")
    id_counter = 0
    g=Graph()
    g.parse('src/XPEVENT_updated.ttl')
    
    # Get the current date and time
    current_datetime = datetime.now()
    # Format the datetime as a string (adjust the format as needed)
    timestamp = current_datetime.strftime("%Y%m%d_%H%M%S")
    # Construct the file name with the timestamp
    file_name = f"latest_{timestamp}.ttl"  # Adjust the prefix and file extension

    onto_pop_fun_inst = OntologyPopulationFunction()
    output_fileName = os.path.join(save_dir,file_name)
    input_dir_files = os.listdir(input_dir)
    
    for index, in_file in enumerate(tqdm(input_dir_files, desc="Processing Files")):
        input_fileName = os.path.join(input_dir,in_file)
        dc_list, g, id_counter = generate_graph(input_fileName,onto_pop_fun_inst,g,emvista_events,id_counter)

    g.serialize(output_fileName, format='turtle')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="Emvista_Wikipedia_dataset")
    parser.add_argument("--input_dir", type=str, default="combined_json")
    parser.add_argument("--save_dir", type=str, default="dataset")
    parser.add_argument('--ontology_name',type=str, default="XPEVENT_updated.ttl")
    args = parser.parse_args()
    main(args)