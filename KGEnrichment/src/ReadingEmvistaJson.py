from html import entities
from math import degrees
#from tqdm import tqdm
from random import shuffle
import os
import json
import ast
import argparse
import csv

## NODES TO FILTER OUT (i.e. DO NOT TREAT AS EVENTS)
non_events = [
    "type",             # used to get entitites gender and semantic type (or question type)
    "polarity",         # used to get verbs and adjectives' polarity (Pos/Neg)
    "modality",         # used to get predicates' modeal values
    "aspect",           # used to get predicates' aspectual values
    "cardinality",      # used to get entities cardinality
    "partOf",           # meronymy (unused as of now)
    "subClassOf",       # subsumption (unused as of now)
    "named",            # PROPN modifying NOUNs (i.e. president Biden)
    "property",         # ADJ modifying nominals 
    "identity",         # coreference (with same As links)
    "instanceOf",        # used in questions when the unknown item is introduced by 'which'
    "degree"
]

state_non_events = [
    "state",            # John is a doctor
    "exist-47.1-1"      # There is a cat
]

location_non_events = [
    "locatedAt",        # There is a cat on the table
    "located_at",       # same idea
    "located_at-1"      # same idea
]
possession_non_events = [
    "own",              # same as own-100
    "own-100",          # John owns a car OR His car
    "own-100.1",        # The car belongs to John
    "own-100.2"         # same as own-100
]

# Those two ar special cases, but they are NOT events per se
# Those represent conjuctions (inclusive and exclusive);
# The elements linked to this node by "Addition" or "Alternative" links can be anythings
# - Events: "John at and drank", addition (eat, drink)
# - Entities: "I saw John and Mary", addition (John, Mary)
# - Properties: "This car is black and blue", addition (black, blue)

coonjuctions = [
    "addition",
    "alternative"
]  

#EVERYTHING ELSE CAN BE CONSIDERED AN EVENT (until proven otherwise... :)

def get_emvista_events_ids(data_path):
    emvista_events = []
    with open(os.path.join(data_path,'emvista-events_valid-class-ids.txt'),'r') as f:
        emvista_events = f.read().splitlines()
    return emvista_events


def process_em_graph(graph,emvista_events):
    events, properties = [], []
    em_properties = [['identity'],['type'],['cardinality'],['polarity'],['aspect'],['addition']]
    for predicate in graph:
        if(predicate['value'] in em_properties):
            properties.append(predicate)
        #elif(predicate['value'][0] in emvista_events):
        elif((predicate['value'][0] not in non_events) and 
             (predicate['value'][0] not in state_non_events) and 
             (predicate['value'][0] not in location_non_events) and 
             (predicate['value'][0] not in possession_non_events) and 
             (predicate['value'][0] not in coonjuctions)):
            events.append(predicate)
    return events, properties

def process_new_em_graph(graph,emvista_events):
    events, properties = [], []
    em_properties = ['identity','type','cardinality','polarity','aspect','addition']
    type_event_identifier = ["devenir", "être", "se montrer", "demeurer", "passer pour", "paraître", "sembler", "rester", "avoir l'air"]
    property_event_identifier = ["devenir", "être", "se montrer", "demeurer", "passer pour", "paraître", "sembler", "rester", "avoir l'air"]
    for predicate in graph:
        if(predicate['value']=='type' and predicate['source'] in type_event_identifier):
            events.append(predicate)
        elif(predicate['value']=='property' and predicate['source'] in property_event_identifier):
            events.append(predicate)
        elif(predicate['value'] in em_properties):
           properties.append(predicate)
        #elif(predicate['value'] in emvista_events):
        if((predicate['value'] not in non_events) and 
             (predicate['value'] not in state_non_events) and 
             (predicate['value'] not in location_non_events) and 
             (predicate['value'] not in possession_non_events) and 
             (predicate['value'] not in coonjuctions)):
            events.append(predicate)
    return events, properties