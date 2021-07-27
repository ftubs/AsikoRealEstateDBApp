DROP TABLE Used_as;
DROP TABLE Specializes_in;
DROP TABLE Recieved_award;
DROP TABLE Awards;
DROP TABLE Projects;
DROP TABLE Owned_by;
DROP TABLE Mortgage;
DROP TABLE Financed_by;
DROP TABLE Built_by;
DROP TABLE Designed_by;
DROP TABLE Lenders;
DROP TABLE Contractors;
DROP TABLE Designers;
DROP TABLE Developers;
DROP TABLE Companies;
DROP TABLE Property_types;
DROP TABLE Buildings;

CREATE TABLE Buildings (
  building_id SERIAL primary key,
  name varchar(64),
  size_sqf_0000 numeric not null,
  property_class varchar(2),
  status varchar(20) not null,
  street_num integer not null,
  street_name varchar(64) not null,
  city varchar(32) not null,
  state char(2) not null,
  zip integer not null,
  UNIQUE (street_num, street_name, zip),
  CONSTRAINT status_contraint CHECK (status in ('completed', 'under construction', 'planned')),
  CONSTRAINT class_constraint CHECK (property_class in ('AA', 'A', 'B', 'C')),
  CONSTRAINT zip_constraint CHECK (zip >= 00501 AND zip <= 99950)
);

CREATE TABLE Property_types (
  name varchar(64) primary key,
  CONSTRAINT type_name_contraint CHECK (name in ('Office', 'Industrial', 'Retail', 'Residential', 'Hospitality'))
);

CREATE TABLE Companies (
  fed_id char(10) primary key,
  name varchar(64) not null,
  num_of_employees integer,
  revenue_$mm numeric,
  email varchar(64),
  phone_number char(12) UNIQUE
);

CREATE TABLE Developers (
  fed_id char(10) primary key,
  regional_focus varchar(12),
  CONSTRAINT regional_focus_constraint CHECK (regional_focus in ('National', 'New England', 'Mid-Atlantic', 'Midwest', 'S.Atlantic', 'S.Central', 'West')),
  FOREIGN KEY (fed_id) REFERENCES Companies(fed_id) ON DELETE CASCADE
);

CREATE TABLE Designers (
  fed_id char(10) primary key,
  projects_completed integer,
  type varchar(20) not null,
  CONSTRAINT designer_type_constraint CHECK (type in ('Architect', 'Architect-Engineer', 'Engineer')),
  FOREIGN KEY (fed_id) REFERENCES Companies (fed_id) ON DELETE CASCADE
);

CREATE TABLE Contractors (
  fed_id char(10) primary key,
  sqft_completed_5yrs numeric,
  sqft_under_construction numeric,
  FOREIGN KEY (fed_id) REFERENCES Companies(fed_id) ON DELETE CASCADE
);

CREATE TABLE Lenders (
  fed_id char(10) primary key,
  min_loan_size_$mm numeric,
  max_loan_size_$mm numeric,
  min_rate numeric,
  max_rate numeric,
  max_ltc numeric,
  FOREIGN KEY (fed_id) REFERENCES Companies (fed_id) ON DELETE CASCADE
);

CREATE TABLE Designed_by (
  b_id integer,
  fed_id char(10),
  PRIMARY KEY (b_id, fed_id),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id),
  FOREIGN KEY (fed_id) REFERENCES Designers (fed_id)
);

CREATE TABLE Built_by (
  b_id integer,
  fed_id char(10),
  PRIMARY KEY (b_id, fed_id),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id),
  FOREIGN KEY (fed_id) REFERENCES Contractors (fed_id)
);

CREATE TABLE Financed_by (
  b_id integer,
  fed_id char(10),
  PRIMARY KEY (b_id, fed_id),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id),
  FOREIGN KEY (fed_id) REFERENCES Lenders (fed_id)
);

CREATE TABLE Mortgage (
  b_id integer,
  mortgage_id integer,
  amount_$mm numeric,
  rate numeric,
  agreement_date date not null,
  PRIMARY KEY (b_id, mortgage_id),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id) ON DELETE CASCADE
);

CREATE TABLE Owned_by (
  b_id integer,
  fed_id char(10),
  since date,
  PRIMARY KEY (b_id, fed_id),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id),
  FOREIGN KEY (fed_id) REFERENCES Companies (fed_id)
);

CREATE TABLE Projects (
  b_id integer,
  designer_id char(10),
  contractor_id char(10),
  lender_id char(10),
  developer_id char(10),
  completion_date date not null,
  PRIMARY KEY (b_id, designer_id, lender_id, contractor_id, developer_id),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id) ON DELETE CASCADE,
  FOREIGN KEY (designer_id) REFERENCES Designers (fed_id) ON DELETE CASCADE,
  FOREIGN KEY (contractor_id) REFERENCES Contractors (fed_id) ON DELETE CASCADE,
  FOREIGN KEY (lender_id) REFERENCES Lenders (fed_id) ON DELETE CASCADE,
  FOREIGN KEY (developer_id) REFERENCES Developers (fed_id) ON DELETE CASCADE
);

CREATE TABLE Awards (
  name varchar(64),
  organization varchar(64),
  PRIMARY KEY (name, organization)
);

CREATE TABLE Recieved_award (
  b_id integer,
  designer_id char(10),
  contractor_id char(10),
  lender_id char(10),
  developer_id char(10),
  award_name varchar(64),
  award_org varchar(64),
  award_year integer,
  PRIMARY KEY (b_id, designer_id, lender_id, contractor_id, developer_id, award_name, award_org, award_year),
  FOREIGN KEY (b_id, designer_id, lender_id, contractor_id, developer_id) REFERENCES Projects (b_id, designer_id, lender_id, contractor_id, developer_id) ON DELETE CASCADE,
  FOREIGN KEY (award_name, award_org) REFERENCES Awards (name, organization) ON DELETE CASCADE
);

CREATE TABLE Specializes_in (
  fed_id char(10),
  type_name varchar(64),
  PRIMARY KEY (fed_id, type_name),
  FOREIGN KEY (fed_id) REFERENCES Companies (fed_id),
  FOREIGN KEY (type_name) REFERENCES Property_types (name)
);

CREATE TABLE Used_as (
  b_id integer,
  type_name varchar(64),
  PRIMARY KEY (b_id, type_name),
  FOREIGN KEY (b_id) REFERENCES Buildings (building_id),
  FOREIGN KEY (type_name) REFERENCES Property_types (name)
);
