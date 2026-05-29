# Senior Data Enginer Tech Challenge

This test is split into 4 sections:
1. Data ingestion pipeline
2. Database design
3. SQL reporting
4. Solution design
---


## Submission Guidelines
Please create a Github repository containing your submission and send us an email containing a link to the repository. While we do not discourage the use of AI, we would appreciate if you submit your individual reasoning particularly for sections 2 and 4. If using AI, explain how you would prompt AI what was the response you got and how you would apply that to the problem statement on hand. 

Dos:
- Frequent commits
- Descriptive commit messages
- Clear documentation of your reasoning and intent
- Comments in your code

Donts:
- Only one commit containing all the files
- Submitting a zip file
- Sparse or absent documentation
- Code which is hard to read
- Direct output from AI models without curation

## Section 1: Data ingestion pipeline

We oversee the course registrations by continuous education and training (CET) centres and the disbursement of learning credits.

In the data folder, the sample CSV file for course enrollments by learners are submitted by one CET.

You are tasked to ingest this data into the sqlite database. The database has the following schema below.

    create table courses as (
        course_id int,
        name string,
        description string,
        prerequisites string -- JSON string representation of array<int> e.g., [1,2,3]
    );

    create table enrollments as (
        enrollment_id int,
        participant_id string,
        participant_name string,
        course_id int,
        course_date date,
        amount float,
        subsidy float,
        credits_used float
    );

## Section 2: Database design

Describe your considerations for designing the database schema. Your answer should address at minimum:
-	How you would model the data across the Bronze, Silver, and Gold layers, and what transformations occur at each layer
-	How you handle the many-to-many relationship between courses and enrolments
-	What data quality checks or transformations you would apply between layers
-	How you would design the Gold layer to support efficient analytical queries

## Section 3: SQL reporting

In the given schema, prerequisites represents an array of course ids that are required to be completed before registering for the given course id.
Following from the task in Section 1, generate a SQL statement to produce a report that identifies participants that have registered for courses without meeting the prerequisites.

## Section 4: Solution design

Assuming that you are working with a courses table that contains 200 million records. Each course has a description, and your Data Scientist has built a machine learning model that reads a course description that predicts the skillsets required for that course. This model has been deployed as an AWS SageMaker endpoint, meaning your pipeline calls the model via an API to get predictions.

After running the pipeline, you realise it will take 2 months to process all 200 million records — which is far too long. Your task is to identify the bottleneck and explain how you would optimise this pipeline. Consider both how the SageMaker endpoint is being served, and how the script calling the endpoint is written.
