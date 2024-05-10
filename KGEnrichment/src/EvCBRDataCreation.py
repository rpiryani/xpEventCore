import rdflib
from rdflib import Graph
import pickle
import numpy as np
import json
import argparse
from pathlib import Path
from scipy.sparse import dok_matrix
from collections import defaultdict
from rdflib import URIRef
import os
import random
from typing import Dict
import time
from rdflib import Namespace
from pathlib import Path
import os
import pickle
import argparse

#from utils import *

DATA_DIR = ""
SEM = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")
FARO = Namespace("http://purl.org/faro/")
XPEVENT = Namespace("http://www.irit.fr/xpEvent/")

'''def selection_of_pairs(file_path,kg):
    test_causeeffect_choices = set()
    current_directory = os.getcwd()
    not_found = []
    # Print the current directory
    print("Current directory:", current_directory)
    with open(file_path) as f:
        lines = f.readlines()
        #print("Total Lines: "+str(len(lines)))
        total_E1_E2_as_events = 0
        for line in lines:
            line = line.replace("\n",'')
            line = line.split("\t")
            E1_event_flag = False
            E2_event_flag = False
            #if('ID_2032' in line[0]):
                #for p,o in kg.predicate_objects(subject=URIRef(line[0])):
                    #print("P: "+str(p)+"\tO: "+str(o))
                #for p,o in kg.predicate_objects(subject=URIRef(line[2].replace("\n",''))):
                    #print("P1: "+str(p)+"\tO1: "+str(o))
            for p,o in kg.predicate_objects(subject=URIRef(line[0])):
                
                if(("xpEvent/Event" in str(o)) or ("xpEvent/Actor" in str(o))):
                    E1_event_flag = True
                    break
            for p,o in kg.predicate_objects(subject=URIRef(line[2].replace("\n",''))):
                if(("xpEvent/Event" in str(o)) or ("xpEvent/Actor" in str(o))):
                    E2_event_flag = True
                    break
            if(E1_event_flag == True and E2_event_flag==True):
                total_E1_E2_as_events+=1
                test_causeeffect_choices.add((URIRef(line[0]),URIRef(line[2].replace('\n',''))))
            else:
                not_found.append((line))
    print(not_found)
    return test_causeeffect_choices'''


def selection_of_pairs(file_path, kg):
    test_causeeffect_choices = set()
    not_found = []
    try:
        with open(file_path) as file:
            for line in file:
                line = line.strip().split("\t")
                if len(line) != 3:
                    not_found.append(line)
                    continue
                if any("xpEvent/Event" in str(o) or "sem/Actor" in str(o) for _, o in kg.predicate_objects(subject=URIRef(line[0]))) \
                        and any("xpEvent/Event" in str(o) or "sem/Actor" in str(o) for _, o in kg.predicate_objects(subject=URIRef(line[2]))):
                    test_causeeffect_choices.add((URIRef(line[0]), URIRef(line[2])))
                else:
                    not_found.append(line)
            print("NOT FOUND: \n++++++++++++++++"+"Length: "+str(len(not_found))+"\n")
            print(str(not_found))
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    return test_causeeffect_choices#, not_found

def main(args):
    data_dir = args.data_dir
    input_dir = os.path.join(data_dir, args.input_dir)
    input_kg = os.path.join(input_dir,args.input_kg)
    out_dir = Path(os.path.join(input_dir, args.save_dir))
    WDT_HASEFFECT = XPEVENT[args.WDT_HASEFFECT]
    remove_similar_relation_flag = args.remove_similar_relation
    select_same_pair_flag = args.select_same_pair_flag
    select_same_pair_test_connection_files = os.path.join(input_dir,args.select_same_pair_test_connection)
    #input_kg = (DATA_DIR/input_kg).resolve()
    #subclass_kg = (DATA_DIR/args.subclass_kg).resolve()

    #out_dir = (DATA_DIR/out_dir).resolve()
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    print(f"Loading graphs")
    kg = rdflib.Graph()
    kg.parse(input_kg)

    #with open(RELEVANT_EVENTS_DATA, 'rb') as f:
    #    relevant_events = pickle.load(f)
    #relevant_events = set(relevant_events)

    eval_options = set()
    # to expand the amount of available data, convert all cause/effect types to just be "has effect" relations
    '''for effect_prop in EFFECT_PROPERTIES:
        remove_trips = []
        add_trips = []
        for s,o in kg.subject_objects(predicate=effect_prop):
            remove_trips.append((s, effect_prop, o))
            add_trips.append((s, WDT_HASEFFECT, o))
        for rt in remove_trips:
            kg.remove(rt)
        for at in add_trips:
            kg.add(at)
    for cause_prop in CAUSE_PROPERTIES:
        remove_trips = []
        add_trips = []
        for o, s in kg.subject_objects(predicate=cause_prop):
            remove_trips.append((o, cause_prop, s))
            add_trips.append((s, WDT_HASEFFECT, o))
        for rt in remove_trips:
            kg.remove(rt)
        for at in add_trips:
            kg.add(at)
    
    '''

    '''for s,o in kg.subject_objects(predicate=WDT_HASEFFECT):
        for cause_type in kg.objects(subject=s, predicate=WDT_INSTANCEOF):
            for o_ in kg.objects(subject=o, predicate=WDT_INSTANCEOF):
                if cause_type in relevant_events and o_ in relevant_events and \
                        s not in relevant_events and o not in relevant_events:
                    eval_options.add(cause_type)
                    break
    
    
    cause_effect_truth = set()
    for target_event_type in eval_options:
        eval_cases = list(kg.subjects(predicate=WDT_INSTANCEOF, object=target_event_type))
        for sc in eval_cases:
            for effect in kg.objects(subject=sc, predicate=WDT_HASEFFECT):
                effect_types = set(kg.objects(subject=effect, predicate=WDT_INSTANCEOF))
                if len(effect_types.intersection(relevant_events)) > 0 and effect not in relevant_events:
                    cause_effect_truth.add((sc, effect))'''
    cause_effect_truth = set()
    for s,o in kg.subject_objects(predicate=WDT_HASEFFECT):
        cause_effect_truth.add((s, o))

    print(f"{len(cause_effect_truth)} cause-effect pairs")



    # cleaning the kg
    print(f"Initial triples: {len(kg)}")
    rem_lit = set()
    for (s, p, o) in kg:
        if isinstance(o, rdflib.Literal):
            rem_lit.add(o)
    for lit in rem_lit:
        kg.remove((None, None, lit))
    print(f"literals removed, {len(kg)} triples present.")
    #rem_trip = set()
    #for (s, p, o) in kg.triples((None, WDT_DIFFERENTFROM, None)):
        #rem_trip.add((s, p, o))
    #for rt in rem_trip:
       # kg.remove(rt)
    #print(f"Removed 'differentFrom' relations, {len(kg)} triples present")
    #rem_wm = set()
    #print(f"removing URIs that look like media/images")
    #for (s, p, o) in kg:
    #    if "wikimedia.org" in o:
    #        rem_wm.add(o)
    #    elif "wikimedia" in o or ".png" in o or ".jpg" in o:
    #        rem_wm.add(o)
    #for ent in rem_wm:
    #    kg.remove((None, None, ent))
    #print(f"wikimedia URI removed, {len(kg)} triples present.")'''

    if(len(cause_effect_truth)==0):
        print("INFO: No pair found")
        return
    ###########################################
    if(select_same_pair_flag==True):
        test_causeeffect_choices = selection_of_pairs(select_same_pair_test_connection_files,kg)
    else:
        test_causeeffect_choices = random.sample(cause_effect_truth, k=100)
    #print("TEST CHOICE LENGTH: "+str(len(test_causeeffect_choices))+"\t one element: "+str(test_causeeffect_choices[0]))
    ########################################
    # if we need to select same pairs following blocks needs to be activate
    ###########################################

    ##############################################################

    test_causes = set([tup[0] for tup in test_causeeffect_choices])
    test_effects = set([tup[1] for tup in test_causeeffect_choices])
    for (cause, effect) in test_causeeffect_choices:
        if effect in test_causes:
            if effect in test_effects:
                test_effects.remove(effect)
        elif cause in test_effects:
            if cause in test_effects:
                test_effects.remove(cause)
    print(f'{len(test_effects)} effects selected for testing')
    
    print(f"removing nodes with only 1 connection")
    remove_nodes = []
    for n in kg.all_nodes():
        conn_count = 0
        for s,p, in kg.subject_predicates(object=n):
            conn_count += 1
            if conn_count > 1:
                break
        for p,o in kg.predicate_objects(subject=n):
            conn_count += 1
            if conn_count > 1:
                break
        if conn_count <= 1:
            remove_nodes.append(n)
    while remove_nodes:
        for rn in remove_nodes:
            kg.remove((None, None, rn))
            kg.remove((rn, None, None))
        remove_nodes = []
        for n in kg.all_nodes():
            conn_count = 0
            for s, p, in kg.subject_predicates(object=n):
                conn_count += 1
                if conn_count > 1:
                    break
            for p, o in kg.predicate_objects(subject=n):
                conn_count += 1
                if conn_count > 1:
                    break
            if conn_count <= 1:
                remove_nodes.append(n)

    print("setting up triples")
    test_triples = []
    test_connection_triples = []
    valid_triples = []
    valid_connection_triples = []
    train_ents = set()
    train_relations = set()
    train_triples = []

    training_kg = rdflib.Graph()
    not_consider = ["faro","sem/Core","sem/Event","sem/eventProperty","owl/topDataProperty","contingently_related_to","sameAs"]
    for t in kg:
        if remove_similar_relation_flag and any(nc in t[1] for nc in not_consider):
            continue
        elif t[0] in test_effects:
            test_triples.append(t)
        elif t[2] in test_effects:
            if t[0] in test_causes and WDT_HASEFFECT in t[1]:
                test_connection_triples.append(t)
                
        else:
            train_triples.append(t)
            train_ents.update([t[0], t[2]])
            train_relations.add(t[1])
            training_kg.add(t)


    # moving on to saving and preprocessing training data
    kg = training_kg

    ###############################
    
    with open((out_dir / "train.txt").resolve(), "w", encoding='utf-8') as f:
        for t in train_triples:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\n")
    with open((out_dir / "test.txt").resolve(), "w", encoding='utf-8') as f:
        for t in test_triples:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\n")
    with open((out_dir / "test_connections.txt").resolve(), "w", encoding='utf-8') as f:
        for t in test_connection_triples:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\n")

    entities = dict()
    for e in train_ents:
        entities[e] = len(entities)
    relations = dict()
    for r in train_relations:
        relations[r] = len(relations)
    rev_entities = {v: k for k, v in entities.items()}
    rev_relations = {v: k for k, v in relations.items()}
    with open((out_dir / "entities.dict").resolve(), "w", encoding='utf-8') as f:
        for i in range(len(rev_entities)):
            f.write(f"{i}\t{rev_entities[i]}\n")
    with open((out_dir / "relations.dict").resolve(), "w", encoding='utf-8') as f:
        for i in range(len(rev_relations)):
            f.write(f"{i}\t{rev_relations[i]}\n")

    #subkg = rdflib.Graph()
    #subkg.parse(subclass_kg)

    #kg += subkg
    print(f"Finished loading.")
    
    ##################################################


if __name__ == "__main__":
    args={}
    parser = argparse.ArgumentParser(description="Preprocess an rdflib graph into a matrix format")
    parser.add_argument("--data_dir",type=str,default="Emvista_Wikipedia_dataset")
    parser.add_argument("--input_dir",type=str,default="dataset")
    parser.add_argument("--input_kg", type=str, default="_latest_combined_01122023_resolved.ttl")
    parser.add_argument("--WDT_HASEFFECT", type=str, default="has_cause")
    parser.add_argument("--save_dir", type=str, default="EvCBR_dataset") # this directory should be inside the dataset directory
    parser.add_argument("--select_same_pair_flag",type=bool,default=False)
    parser.add_argument("--select_same_pair_test_connection", type=str,default='dataset_from_new_representation/updated_causal_resolve_issue/test_connections.txt')
    parser.add_argument("--remove_similar_relation",type=bool,default=False)
    args = parser.parse_args()
    main(args)