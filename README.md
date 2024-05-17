# XPEventCore ontolgy and KG Enrichment
## XPEventCore Ontology
<p align="justify"> We named our event ontology as XPEventCore, which can be used to describe events using the 5W1H characteristics, which include the "Who," "What," "When," "Where," "Why," and "How" dimensions.  It provides a structured and adaptable foundation for capturing the essential facets of an event. By leveraging XPEventCore, events can be represented consistently  across contexts and interconnect diverse datasets. Its flexibility allows to customize its structure, extending or refining it to accommodate particular scenarios' unique characteristics and requirements. </p>
<p align="justify">From comprehensive analysis [31], it appears that currently, in the literature, no ontology adequately represents an explainable event incorporating the 5W1H characteristics. SEM is a widely reused model in existing ontologies, as evidenced by its application in numerous research works [48,49,50,51,52,53,54]. These studies show how researchers have extended SEM to represent events to fulfill their requirements. While the SEM model is widely used in many ontologies, it has some limitations. For instance, it only represents four of the 5W1H characteristics and doesn’t allow linking different events or providing relations between classes of the same type. Whereas FARO does not represent “When” explicitly, it allows temporal relations, which means FARO has the answer to “When” question implicitly. Also, it doesn’t define classes or properties for “Where” and “Who” explicitly. LODE ontology aims for minimal modeling of events. CIDOC-CRM has many classes and properties, but only a subset defines the event. It doesn’t represent the “How” elements of 5W1H. To overcome these limitations, we have developed XPEventCore, an ontology derived from the extension of SEM. XPEventCore explicitly addresses the representation of explainable events incorporating the 5W1H characteristics. This extension involves the integration of other ontologies, including the FARO ontology, known for its rich set of relations. New classes and properties have been introduced within XPEventCore, notably the introduction of "How,” represented by the object property ”XPEventCore:how it occurs” under the ”sem:eventProperty”.</p>

![alt text](https://github.com/rpiryani/xpEventCore/blob/main/image/Ontology.JPG?raw=true)

## KG Enrichment
<p align="justify"> EvCBR [34], is a case-based reasoning model. It predicts the properties of new subsequent events based on similar cause-effect events present in the KG. EvCBR makes
path-based predictions without training by identifying similar occurrences using statistical measurements like entity similarity, case head similarity, case tail similarity and case selection. Generally, this task is a 2-hop Link Prediction (LP) task as illustrated in Figure given below: the first hop is a causal relation connecting a cause event to a new effect event, and the second hop is a property of the new effect event that is desired to be predicted. We apply this approach to other relations, such as temporal and purpose relations. </p>

![alt text](https://github.com/rpiryani/xpEventCore/blob/main/image/problem_statement.jpg?raw=true)

### Steps to Run EvCBR on EKG
i) Creating dataset for EvCBR algorithm from EKG TTL file 

   python .\src\EvCBRDataCreation.py --data_dir data --input_dir dataset --input_kg query_results_new_rep_updated_disable_sameAs_01122023.ttl --WDT_HASEFFECT before --save_dir EvCBR_dataset 

   Arguments: 

         --data_dir: name of data directory
   
         --input_dir: directory where Populated EventKG TTL file is stored
   
         --input_kg: name of Populated Event KG TTL file
   
         --WDT_HASEFFECT: name of relation such as has_cause, purpose, before
   
         --save_dir: directory to store dataset files of EvCBR dataset

   If you want to remove the similar kind of relations such as not_consider = ["faro","sem/Core","sem/Event","sem/eventProperty","owl/topDataProperty"] then you need to pass other argument

         -- remove_similar_relation False

      python .\src\EvCBRDataCreation.py --data_dir data --input_dir dataset --input_kg query_results_new_rep_updated_disable_sameAs_01122023.ttl --WDT_HASEFFECT before --save_dir EvCBR_dataset -- remove_similar_relation False

   If you want to select the similar pair of cause_effect pair from different ontology then you need to pass two other parameters

         --select_same_pair_flag True
   
         --select_same_pair_test_connection dataset_from_new_representation/EvCBR_dataset_1/test_connections.txt

      python .\src\EvCBRDataCreation.py --data_dir data --input_dir dataset --input_kg query_results_new_rep_updated_disable_sameAs_01122023.ttl --WDT_HASEFFECT before --save_dir EvCBR_dataset --select_same_pair_flag True --select_same_pair_test_connection dataset_from_new_representation/EvCBR_dataset_1/test_connections.txt

2)  Run EvCBR algorithm

    i)  python .\experiments_evcbr/preprocess_data_for_evcbr.py --process_emvista --emvista_input EvCBR_dataset --emvista_output evcbr_EvCBR_dataset

       Arguments:

         --process_emvista: program is set for different dataset that used in paper "process_wiki", "process_fb", for our dataset "process_emvista"
    
         --emvista_input: EvCBR dataset directory name created in step 4
    
         --emvista_output: directory name to store dataset files of process_emvista


    ii) python .\experiments_evcbr/run_evcbr_test.py --do_reverse_and_predict --pp_data_dir EvCBR_dataset --evcbr_pp_data_dir evcbr_EvCBR_dataset --save_dir EvCBR_dataset_results --processes 8 --n_cases 5 --n_cases_coverage 3 --n_paths 80 

       Agruments

         --do_reverse_and_predict will run EvCBR's additional refinement step. Without this tag, only the basic forward predictions will take place. Note that this flag will make the runtime longer.
    
         --processes is used to enable multiprocessing, which is highly recommended. You will likely need to adjust the number of processes being run based on what makes sense for your CPU. Note that increasing the number of processes will also require more memory.
    
         --n_cases and --n_cases_coverage define how many cases from the KG to retrieve in order to discover prediction paths.
    
         --n_paths determines how many prediction paths are sampled from each case.

    iii) python .\experiments_evcbr/show_evcbr_eval_results.py --eval_res_dir EvCBR_dataset_results --data_dir EvCBR_dataset 

