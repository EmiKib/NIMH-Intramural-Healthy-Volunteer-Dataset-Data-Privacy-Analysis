

## Data privacy analysis of The National Institute of Mental Health (NIMH) Intramural Healthy Volunteer Dataset https://openneuro.org/datasets/ds004215/versions/1.0.3

The data can be viewed as 3 different entities, with its respective individual datasets: 

1. Preliminary Online Screening Questionnaires + participants.tsv


- #### participants.tsv
  - Quasi-Identifers that together can be used to identify an individual :heavy_exclamation_mark:
 

- #### Alcohol Use Disorders Identification Test (AUDIT)	audit.tsv
  - A sensitive attributes that could potentially be harming for the participant in an event of a data breach ❗

- #### Demographics	demographics.tsv
    - Quasi-Identifers that together can be used to identify an individual :heavy_exclamation_mark:
      

###### Bilingual: Originally the dataset contained the variables LANGUAGES and OTHER_LANGUAGES this has been made into 1 column stating if the subject is bilingual or not. 


  
- #### Drug Use Questionnaire	drug_use.tsv
    - A sensitive attributes that could potentially be harming for the participant in an event of a data breach :heavy_exclamation_mark:

- #### Edinburgh Handedness Inventory (EHI)	ehi.tsv
  -  Nothing to do here, handedness is already included as a varible in itself) :white_check_mark:
     
- #### Health History Questions	health_history_questions.tsv
  - A mix of quasi & sensitive-indentifers ❗
  
- #### Health Rating	health_rating.tsv
  - Subjective score of how a subject would rate their health pose no data risk :white_check_mark:

- #### Mental Health Questions	mental_health_questions.tsv
  - Subjective score of how a subject would rate their mental health pose limited risk to data breach :white_check_mark:
    

- #### World Health Organization Disability Assessment Schedule 2.0 (WHODAS 2.0)	whodas.tsv
  - Subjective disability assessment pose limited risk to data breach :white_check_mark:




_______________________________________________________________________________________________________________________________________________________________________






2. On-Campus In-Person Screening Visit

Adverse Childhood Experiences (ACEs)	ace.tsv
Beck Anxiety Inventory (BAI)	bai.tsv
Beck Depression Inventory-II (BDI-II)	bdi.tsv
Clinical Variable Form	clinical_variable_form.tsv
Family Interview for Genetic Studies (FIGS)	figs.tsv
Kaufman Brief Intelligence Test 2nd Edition (KBIT-2) and Vocabulary Assessment Scale (VAS)	kbit2_vas.tsv
NIH Toolbox Cognition Battery	nih_toolbox.tsv
Perceived Health Rating	perceived_health_rating.tsv
Satisfaction Survey	satisfaction.tsv
Structured Clinical Interview for DSM-5 Disorders (SCID-5)	scid5.tsv

3. Optional On-Campus In-Person MRI Visit

Acute Care Panel	acute_care.tsv
Blood Chemistry	blood_chemistry.tsv
Complete Blood Count with Differential	cbc_with_differential.tsv
Hematology Panel	hematology.tsv
Hepatic Function Panel	hepatic.tsv
Infectious Disease Panel	infectious_disease.tsv
Lipid Panel	lipid.tsv
Other Panel	other.tsv
Urinalysis	urinalysis.tsv
Urine Chemistry	urine_chemistry.tsv
Vitamin Levels	vitamin_levels.tsv
