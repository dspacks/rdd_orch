# Example Healthcare Data Dictionaries

This file contains example data dictionaries for various healthcare data types. Use these as:
- **Testing** - Try the ADE system with realistic data
- **Templates** - Starting points for your own data dictionaries
- **Reference** - See how different healthcare domains are structured

All examples follow common healthcare data standards (OMOP, LOINC, SNOMED, etc.).

---

## 1. Basic Diabetes Study

**Domain:** Clinical Research
**Variables:** 7
**Use Case:** Simple diabetes baseline measurements

```csv
Variable Name,Field Type,Field Label,Choices,Notes
patient_id,text,Patient ID,,Unique identifier
age,integer,Age (years),,Age at enrollment
sex,radio,Biological Sex,"1, Male | 2, Female | 3, Other",
bp_systolic,integer,Systolic Blood Pressure (mmHg),,
bp_diastolic,integer,Diastolic Blood Pressure (mmHg),,
diagnosis_date,date,Diagnosis Date,,Date of primary diagnosis
hba1c,decimal,Hemoglobin A1c (%),,Glycated hemoglobin
```

---

## 2. Electronic Health Record (EHR) Data

**Domain:** Clinical Care
**Variables:** 15
**Use Case:** Routine clinical encounter data
**Standards:** ICD-10 diagnosis codes

```csv
Variable Name,Field Type,Field Label,Choices,Notes
mrn,text,Medical Record Number,,Unique patient identifier
encounter_id,text,Encounter ID,,Unique visit identifier
visit_date,date,Visit Date,,Date of clinical encounter
chief_complaint,text,Chief Complaint,,Primary reason for visit
dx_code,text,Diagnosis Code (ICD-10),,Primary diagnosis
bp_systolic,integer,Systolic BP (mmHg),,"70-250, sitting position"
bp_diastolic,integer,Diastolic BP (mmHg),,"40-150, sitting position"
heart_rate,integer,Heart Rate (bpm),,"40-200"
temperature,decimal,Temperature (F),,"95.0-106.0"
respiratory_rate,integer,Respiratory Rate (breaths/min),,"8-40"
oxygen_sat,integer,Oxygen Saturation (%),,"70-100, room air"
bmi,decimal,Body Mass Index,,Calculated from height/weight
smoking_status,radio,Smoking Status,"0, Never | 1, Former | 2, Current",From social history
medication_count,integer,Number of Active Medications,,Count of current prescriptions
lab_ordered,yesno,Labs Ordered,"0, No | 1, Yes",Any lab tests ordered this visit
```

**Key Features:**
- Complete vital signs panel
- ICD-10 diagnosis coding
- Social history (smoking)
- Medication tracking

---

## 3. OMOP Common Data Model (CDM)

**Domain:** Research Data Warehouse
**Variables:** 12
**Use Case:** Standardized observational data
**Standards:** OMOP CDM v5.x

```csv
Variable Name,Field Type,Field Label,Choices,Notes
person_id,integer,Person ID,,OMOP person identifier
visit_occurrence_id,integer,Visit Occurrence ID,,Foreign key to VISIT_OCCURRENCE
measurement_date,date,Measurement Date,,Date of measurement
measurement_concept_id,integer,Measurement Concept ID,,OMOP standard concept for measurement type
value_as_number,decimal,Numeric Value,,Numeric result value
value_as_concept_id,integer,Categorical Value Concept ID,,OMOP concept for categorical results
unit_concept_id,integer,Unit Concept ID,,OMOP concept for unit of measure
range_low,decimal,Normal Range Lower Bound,,Lower limit of normal range
range_high,decimal,Normal Range Upper Bound,,Upper limit of normal range
provider_id,integer,Provider ID,,Foreign key to PROVIDER table
measurement_source_value,text,Source Value,,Original value from source system
measurement_source_concept_id,integer,Source Concept ID,,Concept ID from source vocabulary
```

**Key Features:**
- OMOP standard concept IDs
- Foreign key relationships
- Source value preservation
- Normal range tracking

---

## 4. Genomic/Genetic Data

**Domain:** Precision Medicine
**Variables:** 15
**Use Case:** Variant calling and clinical interpretation
**Standards:** HGNC, dbSNP, ClinVar, GRCh38

```csv
Variable Name,Field Type,Field Label,Choices,Notes
sample_id,text,Sample ID,,Unique biospecimen identifier
patient_id,text,Patient ID,,De-identified patient identifier
gene_symbol,text,Gene Symbol (HGNC),,Official gene symbol from HGNC
variant_id,text,Variant ID (dbSNP),,rs number from dbSNP database
chromosome,text,Chromosome,,"1-22, X, Y, MT"
position,integer,Genomic Position (hg38),,Position on reference genome GRCh38
ref_allele,text,Reference Allele,,"A, C, G, T"
alt_allele,text,Alternate Allele,,"A, C, G, T, or indel"
variant_type,radio,Variant Type,"1, SNV | 2, Insertion | 3, Deletion | 4, CNV",Single nucleotide or structural
genotype,text,Genotype,,"0/0, 0/1, 1/1"
read_depth,integer,Read Depth (DP),,Number of reads covering position
allele_frequency,decimal,Allele Frequency (AF),,"0.0-1.0, population frequency"
clinical_significance,radio,Clinical Significance,"0, Benign | 1, Likely Benign | 2, VUS | 3, Likely Pathogenic | 4, Pathogenic",ClinVar classification
phenotype_association,text,Associated Phenotype,,Disease or trait association
transcript_id,text,Transcript ID (Ensembl),,Canonical transcript identifier
```

**Key Features:**
- HGNC gene symbols
- dbSNP variant IDs
- ClinVar pathogenicity classifications
- GRCh38 reference genome positions
- VCF-compatible format

---

## 5. Clinical Trial Data (CDISC SDTM)

**Domain:** Regulated Clinical Trials
**Variables:** 15
**Use Case:** Phase II/III clinical trial
**Standards:** CDISC SDTM, MedDRA

```csv
Variable Name,Field Type,Field Label,Choices,Notes
studyid,text,Study Identifier,,Protocol number
usubjid,text,Unique Subject ID,,Unique across all studies
subjid,text,Subject ID,,ID within this study
siteid,text,Site ID,,Clinical site identifier
arm,radio,Treatment Arm,"1, Placebo | 2, Low Dose | 3, High Dose",Randomization arm
visit,text,Visit Name,,"Screening, Baseline, Week 4, Week 8, Week 12"
visitnum,integer,Visit Number,,"1-10"
visitdate,date,Visit Date,,Actual visit date
ae_term,text,Adverse Event Term,,MedDRA preferred term
ae_severity,radio,AE Severity,"1, Mild | 2, Moderate | 3, Severe",Intensity grading
ae_serious,yesno,Serious AE,"0, No | 1, Yes",SAE flag
ae_related,radio,Related to Study Drug,"0, Unrelated | 1, Unlikely | 2, Possible | 3, Probable | 4, Definite",Causality assessment
efficacy_score,decimal,Primary Efficacy Score,,"0-100, higher is better"
qol_score,decimal,Quality of Life Score,,"0-100, SF-36"
compliance,decimal,Medication Compliance (%),,"0-100, pill count"
```

**Key Features:**
- CDISC SDTM naming conventions
- MedDRA adverse event coding
- Causality assessment
- Protocol visit structure
- SAE flagging

---

## 6. Medical Imaging Data (DICOM)

**Domain:** Radiology/Imaging
**Variables:** 14
**Use Case:** Radiological study metadata
**Standards:** DICOM, RadLex

```csv
Variable Name,Field Type,Field Label,Choices,Notes
accession_number,text,Accession Number,,Unique exam identifier
patient_id,text,Patient ID,,De-identified patient ID
study_date,date,Study Date,,Date imaging was performed
modality,radio,Imaging Modality,"CT, MRI, PET, US, XR",Type of scan
body_region,text,Body Region (RadLex),,"Chest, Abdomen, Brain, etc."
protocol,text,Scan Protocol,,Specific imaging protocol used
slice_thickness,decimal,Slice Thickness (mm),,For CT/MRI
contrast_used,yesno,Contrast Agent Used,"0, No | 1, Yes",IV contrast administration
dose,decimal,Radiation Dose (mGy),,For CT/XR only
finding_present,yesno,Pathologic Finding,"0, No | 1, Yes",Any abnormality detected
finding_type,text,Finding Type,,Description of pathology
lesion_size,decimal,Lesion Size (mm),,Maximum diameter if applicable
radiologist_id,text,Interpreting Radiologist,,Reader ID
dicom_series_uid,text,DICOM Series Instance UID,,Unique series identifier
```

**Key Features:**
- DICOM metadata tracking
- RadLex body region coding
- Radiation dose recording
- Structured findings
- Series-level identifiers

---

## 7. Patient-Reported Outcomes (PRO)

**Domain:** Patient Experience
**Variables:** 14
**Use Case:** Mental health and quality of life assessment
**Standards:** PHQ-9, GAD-7, PROMIS, SF-36, PSQI

```csv
Variable Name,Field Type,Field Label,Choices,Notes
participant_id,text,Participant ID,,Study participant identifier
survey_date,date,Survey Completion Date,,Date PRO completed
survey_type,radio,Survey Type,"1, Baseline | 2, Follow-up | 3, Final",Assessment timepoint
phq9_total,integer,PHQ-9 Total Score,,"0-27, depression severity"
phq9_q1,radio,Little interest or pleasure,"0, Not at all | 1, Several days | 2, More than half | 3, Nearly every day",Over last 2 weeks
phq9_q2,radio,Feeling down or depressed,"0, Not at all | 1, Several days | 2, More than half | 3, Nearly every day",Over last 2 weeks
gad7_total,integer,GAD-7 Total Score,,"0-21, anxiety severity"
gad7_q1,radio,Feeling nervous/anxious,"0, Not at all | 1, Several days | 2, More than half | 3, Nearly every day",Over last 2 weeks
pain_severity,radio,Pain Severity (0-10),"0, None | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10, Worst",Numeric rating scale
pain_interference,radio,Pain Interference with Activities,"1, Not at all | 2, A little bit | 3, Somewhat | 4, Quite a bit | 5, Very much",PROMIS scale
fatigue_score,integer,PROMIS Fatigue T-Score,,"20-80, normalized T-score"
sleep_quality,radio,Sleep Quality,"1, Very poor | 2, Poor | 3, Fair | 4, Good | 5, Very good",PSQI component
qol_physical,decimal,Physical QOL Domain,,"0-100, SF-36"
qol_mental,decimal,Mental QOL Domain,,"0-100, SF-36"
```

**Key Features:**
- Validated depression screening (PHQ-9)
- Anxiety assessment (GAD-7)
- PROMIS item banks
- SF-36 quality of life domains
- Sleep quality (PSQI)

---

## 8. Laboratory Test Results

**Domain:** Clinical Laboratory
**Variables:** 16
**Use Case:** Lab test orders and results
**Standards:** LOINC, UCUM

```csv
Variable Name,Field Type,Field Label,Choices,Notes
specimen_id,text,Specimen ID,,Unique specimen identifier
patient_id,text,Patient ID,,Patient identifier
collection_date,date,Collection Date,,Date/time specimen collected
test_code,text,Test Code (LOINC),,LOINC code for test
test_name,text,Test Name,,Common test name
result_value,text,Result Value,,Numeric or categorical result
result_numeric,decimal,Numeric Result,,Numeric value if applicable
result_unit,text,Unit of Measure (UCUM),,UCUM unit code
reference_low,decimal,Reference Range Lower,,Normal range lower bound
reference_high,decimal,Reference Range Upper,,Normal range upper bound
abnormal_flag,radio,Abnormal Flag,"N, Normal | L, Low | H, High | LL, Critically Low | HH, Critically High",Interpretation
specimen_type,radio,Specimen Type,"1, Blood | 2, Urine | 3, CSF | 4, Other",Type of biospecimen
lab_id,text,Laboratory ID,,Performing lab identifier
method,text,Test Method,,Analytical method used
verified_by,text,Verified By,,Lab technician ID
loinc_code,text,LOINC Code,,Full LOINC identifier
```

**Key Features:**
- LOINC test coding
- UCUM units of measure
- Reference ranges
- Abnormal flag interpretation
- Specimen tracking

---

## Usage in Jupyter Notebook

All examples are available in the `ade_healthcare_documentation.ipynb` notebook:

```python
# Select your example
my_data = ehr_data_dictionary  # or any other example

# Process with the orchestrator
job_id = orchestrator.process_data_dictionary(
    source_data=my_data,
    source_file="example.csv",
    auto_approve=True  # or False for manual review
)

# Generate documentation
documentation = orchestrator.finalize_documentation(job_id)
```

## Creating Your Own Data Dictionary

Use these examples as templates. Follow the CSV format:

```csv
Variable Name,Field Type,Field Label,Choices,Notes
your_var,type,Label,,"Additional info"
```

**Supported Field Types:**
- `text` - Free text
- `integer` - Whole numbers
- `decimal` - Decimal numbers
- `date` - Dates
- `radio` - Single choice
- `yesno` - Binary choice
- `checkbox` - Multiple choice

## Healthcare Data Standards Referenced

- **OMOP CDM** - Observational Medical Outcomes Partnership Common Data Model
- **LOINC** - Logical Observation Identifiers Names and Codes
- **SNOMED CT** - Systematized Nomenclature of Medicine Clinical Terms
- **ICD-10** - International Classification of Diseases, 10th Revision
- **HGNC** - HUGO Gene Nomenclature Committee
- **dbSNP** - Single Nucleotide Polymorphism Database
- **ClinVar** - Clinical Variant Database
- **MedDRA** - Medical Dictionary for Regulatory Activities
- **CDISC SDTM** - Clinical Data Interchange Standards Consortium Study Data Tabulation Model
- **DICOM** - Digital Imaging and Communications in Medicine
- **RadLex** - Radiology Lexicon
- **UCUM** - Unified Code for Units of Measure
- **PROMIS** - Patient-Reported Outcomes Measurement Information System
- **PHQ-9** - Patient Health Questionnaire (9-item)
- **GAD-7** - Generalized Anxiety Disorder (7-item)
- **SF-36** - 36-Item Short Form Health Survey

## Contributing

Have a data dictionary example you'd like to add? Please contribute!

1. Follow the CSV format above
2. Include standard terminology codes where applicable
3. Add descriptive notes
4. Document the use case and domain

---

**Last Updated:** 2025-11-22
**Version:** 1.0
**Maintainer:** ADE Development Team
