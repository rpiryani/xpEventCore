# XPEventCore ontolgy and KG Enrichment
## XPEventCore Ontology
We named our event ontology as XPEventCore, which can be used to describe events using the 5W1H characteristics, which include the "Who," "What," "When," "Where," "Why," and "How" dimensions.  It provides a structured and adaptable foundation for capturing the essential facets of an event. By leveraging XPEventCore, events can be represented consistently  across contexts and interconnect diverse datasets. Its flexibility allows to customize its structure, extending or refining it to accommodate particular scenarios' unique characteristics and requirements. 
<p align="justify"> Your Text From comprehensive analysis [31], it appears that currently, in the literature, no ontology adequately represents an explainable event incorporating the 5W1H characteristics. SEM is a widely reused model in existing ontologies, as evidenced by its application in numerous research works [48,49,50,51,52,53,54]. These studies show how researchers have extended SEM to represent events to fulfill their requirements. While the SEM model is widely used in many ontologies, it has some limitations. For instance, it only represents four of the 5W1H characteristics and doesn’t allow linking different events or providing relations between classes of the same type. Whereas FARO does not represent “When” explicitly, it allows temporal relations, which means FARO has the answer to “When” question implicitly. Also, it doesn’t define classes or properties for “Where” and “Who” explicitly. LODE ontology aims for minimal modeling of events. CIDOC-CRM has many classes and properties, but only a subset defines the event. It doesn’t represent the “How” elements of 5W1H. To overcome these limitations, we have developed XPEventCore, an ontology derived from the extension of SEM. XPEventCore explicitly addresses the representation of explainable events incorporating the 5W1H characteristics. This extension involves the integration of other ontologies, including the FARO ontology, known for its rich set of relations. New classes and properties have been introduced within XPEventCore, notably the introduction of ”How,” represented by the object property ”XPEventCore:how it occurs” under the ”sem:eventProperty”.</p>
![alt text](https://github.com/rpiryani/xpEventCore/blob/main/image/Ontology.JPG?raw=true)
