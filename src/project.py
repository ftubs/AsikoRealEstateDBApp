"""
Implementation of web front-end for database application

Functions:

    get_config(file, string)
    query_db(string)
"""

import pandas as pd
import psycopg2
import streamlit as st
from configparser import ConfigParser
import re
import helper
from constants import (
    OPTIONS,
    STATES,
    PROPERTY_TYPES,
    PROPERTY_CLASSES,
    STATUSES,
    REGIONS,
    DESIGNER_TYPES,
    SIZES,
)


'# Project Demo'


@st.cache
def get_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    return {k: v for k, v in parser.items(section)}


@st.cache
def query_db(sql: str):
    # print(f'Running query_db(): {sql}')

    db_info = get_config()

    # Connect to an existing database
    conn = psycopg2.connect(**db_info)

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Execute a command: this creates a new table
    cur.execute(sql)

    # Obtain data
    data = cur.fetchall()

    column_names = [desc[0] for desc in cur.description]

    # Make the changes to the database persistent
    conn.commit()

    # Close communication with the database
    cur.close()
    conn.close()

    df = pd.DataFrame(data=data, columns=column_names)

    return df


'## How can we help you?'
search_choice = st.selectbox('What can we help you find today?', OPTIONS)
if search_choice:
    if search_choice == 'Select an option':
        st.write(f"Select an option to get started")

    if search_choice == 'Projects':
        state = st.selectbox('State (required):', STATES)
        city = st.text_input('City (required):')
        zipcode = st.text_input("ZIP Code (optional):", max_chars=5)
        property_type = st.multiselect('Property Type (any):', PROPERTY_TYPES, default=PROPERTY_TYPES)
        property_class = st.multiselect('Property Class (any):', PROPERTY_CLASSES, default=PROPERTY_CLASSES)
        status = st.multiselect('Status (any):', STATUSES, default=STATUSES)

        type_tuple = tuple(property_type)
        class_tuple = tuple(property_class)
        status_tuple = tuple(status)

        if len(property_type) < 2:
            if len(property_type) < 1:
                type_tuple = ('######', '######')
            else:
                type_tuple = (property_type[0], '######')
        if len(property_class) < 2:
            if len(property_class) < 1:
                class_tuple = ('######', '######')
            else:
                class_tuple = (property_class[0], '######')
        if len(status) < 2:
            if len(status) < 1:
                status_tuple = ('######', '######')
            else:
                status_tuple = (status[0], '######')

        try:
            if state and city:
                city = city.strip().lower()
                if zipcode:
                    zipcode = zipcode.strip()
                    if len(zipcode) < 5:
                        raise ValueError("zipcode")
                    zipcode = int(zipcode)
                    sql_building = f"""SELECT DISTINCT B.*, U2.* FROM Buildings B INNER JOIN Used_as U 
                                        ON B.building_id = U.b_id LEFT OUTER JOIN Used_as U2 
                                        ON B.building_id = U2.b_id
                                        WHERE B.state = '{state}' 
                                        AND LOWER(B.city) = '{city}' AND B.zip = {zipcode}
                                        AND U.type_name IN {type_tuple}
                                        AND B.property_class IN {class_tuple}
                                        AND B.status IN {status_tuple};"""
                else:
                    sql_building = f"""SELECT DISTINCT B.*, U2.* FROM Buildings B INNER JOIN Used_as U 
                                        ON B.building_id = U.b_id LEFT OUTER JOIN Used_as U2
                                        ON B.building_id = U2.b_id
                                        WHERE B.state = '{state}' 
                                        AND LOWER(B.city) = '{city}'
                                        AND U.type_name IN {type_tuple}
                                        AND B.property_class IN {class_tuple}
                                        AND B.status IN {status_tuple};"""
                building_info = query_db(sql_building)
                helper.transform(building_info, 'p')
        except (KeyError, ValueError) as e:
            if 'zipcode' in str(e) or 'invalid literal for int() with base 10' in str(e):
                st.write(f"zipcode must be 5 numeric digits.")
            else:
                st.write(f"an error occured")
    elif search_choice == 'Project details':
        street_address = st.text_input('Street Address (required):')
        city = st.text_input('City (required):')
        state = st.selectbox('State (required):', STATES)
        zipcode = st.text_input('ZIP Code (required):', max_chars=5)

        try:
            if street_address and city and state and zipcode:
                st_num, st_name = street_address.strip().split(" ", 1)
                st_name = ' '.join(st_name.strip().split())
                st_name = re.sub(r'[^\w\s]', '', st_name)
                st_name = st_name.lower()
                city = city.strip().lower()
                zipcode = zipcode.strip()
                st_num = int(st_num)
                if len(zipcode) < 5:
                    raise ValueError("zipcode")
                zipcode = int(zipcode)
                sql_building_details = f"""SELECT DISTINCT C5.name as owner, C4.name as developer, C1.name as designer,
                                            C2.name as contractor, C3.name as lender, B.status, P.completion_date, 
                                            COALESCE(A.award_name, 'No Awards') as a_name, 
                                            COALESCE(A.award_org, 'No Awards') as a_org, 
                                            COALESCE(A.award_year, 0) as a_year
                                            FROM BUILDINGS B, PROJECTS P, COMPANIES C1, COMPANIES C2, 
                                            COMPANIES C3, COMPANIES C4, COMPANIES C5, Owned_by O,  
                                            (SELECT DISTINCT B2.building_id, R.award_name, R.award_org, R.award_year 
                                            FROM BUILDINGS B2 LEFT OUTER JOIN Recieved_award R 
                                            ON B2.building_id = R.b_id) as A
                                            WHERE B.building_id = P.b_id AND B.building_id = O.b_id 
                                            AND B.street_num = {st_num} AND LOWER(B.street_name) LIKE '%{st_name}%'
                                            AND LOWER(B.city) = '{city}' AND B.state = '{state}' AND B.zip = {zipcode}
                                            AND P.designer_id = C1.fed_id AND P.contractor_id = C2.fed_id
                                            AND P.lender_id = C3.fed_id AND P.developer_id = C4.fed_id
                                            AND O.fed_id = C5.fed_id AND B.building_id = A.building_id;"""

                building_details = query_db(sql_building_details)
                helper.transform(building_details, 'pd')
        except (Exception, ValueError) as e:
            is_other = True
            if 'zipcode' in str(e):
                st.write(f"zipcode must be 5 numeric digits.")
                is_other = False
            if 'invalid literal for int() with base 10' in str(e):
                st.write(f"Invalid street address format. Street number must be numeric.")
                is_other = False
            if is_other is True:
                st.write(f"an error occured")
    elif search_choice == 'Lead Generation':
        lead_options = ['Developers', 'Architects', 'Engineers', 'Contractors', 'Lenders']
        lead_search_options = st.selectbox('What kind of companies are you interested in learning more about?',
                                           lead_options)
        if lead_search_options == 'Developers':
            property_type = st.multiselect('Property Type (any):', PROPERTY_TYPES)
            region = st.multiselect('Regional Focus (any):', REGIONS)
            num_of_projects = st.number_input('Minimum number of projects in database:', value=0, min_value=0, step=1)
            developer_name = st.text_input('Developer Name:')
            type_tuple = tuple(property_type)
            if len(property_type) == 1:
                type_tuple = (property_type[0], property_type[0])
            region_tuple = tuple(region)
            if len(region_tuple) < 2:
                if len(region_tuple) < 1:
                    regions_sql = "SELECT DISTINCT regional_focus FROM Developers;"
                    regions = query_db(regions_sql)['regional_focus'].tolist()
                    region_tuple = tuple(regions)
                else:
                    region_tuple = (region[0], region[0])
            if len(developer_name) == 0:
                developer_name = '_'
            else:
                developer_name = developer_name.strip().lower()

            try:
                if not property_type:
                    sql_developers = f"""SELECT DISTINCT CO.fed_id, CO.name, CO.email, CO.phone_number,  
                                            COALESCE(CO.num_of_employees, -1) num_employees, 
                                            COALESCE(CO.revenue_$mm, -1) as revenue, D.regional_focus, 
                                            COALESCE(S2.type_name,'None') as type_name, 
                                            P3.num_proj 
                                            FROM Developers D INNER JOIN Companies CO ON D.fed_id = CO.fed_id 
                                            LEFT OUTER JOIN Projects P ON D.fed_id = P.developer_id
                                            LEFT OUTER JOIN Specializes_in S ON D.fed_id = S.fed_id 
                                            LEFT OUTER JOIN Specializes_in S2 ON D.fed_id = S2.fed_id
                                            LEFT OUTER JOIN
                                            (SELECT D2.fed_id, COALESCE(COUNT(DISTINCT P2.b_id),0) as num_proj 
                                            FROM Developers D2 LEFT OUTER JOIN Projects P2 
                                            ON P2.developer_id = D2.fed_id 
                                            GROUP BY D2.fed_id) P3 ON D.fed_id = P3.fed_id
                                            WHERE LOWER(CO.name) LIKE '%{developer_name}%'
                                            AND D.regional_focus IN {region_tuple} 
                                            AND P3.num_proj >= {num_of_projects};"""
                else:
                    sql_developers = f"""SELECT DISTINCT CO.fed_id, CO.name, CO.email, CO.phone_number, 
                                            COALESCE(CO.num_of_employees, -1) num_employees, 
                                            COALESCE(CO.revenue_$mm, -1) as revenue, D.regional_focus, 
                                            COALESCE(S2.type_name,'None') as type_name, 
                                            P3.num_proj 
                                            FROM Developers D INNER JOIN Companies CO ON D.fed_id = CO.fed_id 
                                            LEFT OUTER JOIN Projects P ON D.fed_id = P.developer_id
                                            LEFT OUTER JOIN 
                                            (SELECT D2.fed_id, COALESCE(COUNT(DISTINCT P2.b_id),0) as num_proj 
                                            FROM Developers D2 LEFT OUTER JOIN Projects P2 
                                            ON P2.developer_id = D2.fed_id 
                                            GROUP BY D2.fed_id) P3 ON D.fed_id = P3.fed_id
                                            LEFT OUTER JOIN Specializes_in S ON D.fed_id = S.fed_id 
                                            LEFT OUTER JOIN Specializes_in S2 ON D.fed_id = S2.fed_id
                                            WHERE D.regional_focus IN {region_tuple} AND S.type_name IN {type_tuple} 
                                            AND LOWER(CO.name) LIKE '%{developer_name}%' 
                                            AND P3.num_proj >= {num_of_projects};"""
                developers = query_db(sql_developers)
                helper.transform(developers, 'd')
            except Exception as e:
                st.write(f"An error occurred.")
        elif lead_search_options == 'Architects':
            property_type = st.multiselect('Property Type Specialization (any):', PROPERTY_TYPES)
            num_of_projects = st.number_input('Minimum number of projects in database:', value=0, min_value=0, step=1)
            arch_name = st.text_input('Architect Name :')
            type_tuple = tuple(property_type)
            if len(property_type) == 1:
                type_tuple = (property_type[0], property_type[0])
            if len(arch_name) == 0:
                arch_name = '_'
            else:
                arch_name = arch_name.strip().lower()

            try:
                if not property_type:
                    sql_archs = f"""SELECT DISTINCT CO.fed_id, CO.name, CO.email, CO.phone_number, 
                                    COALESCE(CO.num_of_employees, -1) num_employees, 
                                    COALESCE(CO.revenue_$mm, -1) as revenue, D.type, S2.type_name, 
                                    P3.num_proj 
                                    FROM Designers D INNER JOIN Companies CO 
                                    ON (D.fed_id = CO.fed_id AND 
                                    (D.type = 'Architect' OR D.type = 'Architect-Engineer')) 
                                    INNER JOIN Specializes_in S ON D.fed_id = S.fed_id 
                                    LEFT OUTER JOIN Projects P ON D.fed_id = P.designer_id
                                    LEFT OUTER JOIN 
                                    (SELECT D2.fed_id, COALESCE(COUNT(DISTINCT P2.b_id),0) as num_proj 
                                    FROM Designers D2 LEFT OUTER JOIN Projects P2 ON P2.designer_id = D2.fed_id 
                                    GROUP BY D2.fed_id) P3 ON D.fed_id = P3.fed_id
                                    INNER JOIN Specializes_in S2 ON D.fed_id = S2.fed_id 
                                    WHERE LOWER(CO.name) LIKE '%{arch_name}%' AND P3.num_proj >= {num_of_projects};"""
                else:
                    sql_archs = f"""SELECT DISTINCT CO.fed_id, CO.name, CO.email, CO.phone_number, 
                                    COALESCE(CO.num_of_employees, -1) num_employees, 
                                    COALESCE(CO.revenue_$mm, -1) as revenue, D.type, S2.type_name, 
                                    P3.num_proj 
                                    FROM Designers D INNER JOIN Companies CO 
                                    ON (D.fed_id = CO.fed_id AND 
                                    (D.type = 'Architect' OR D.type = 'Architect-Engineer')) 
                                    INNER JOIN Specializes_in S ON (D.fed_id = S.fed_id 
                                    AND S.type_name IN {type_tuple}) 
                                    LEFT OUTER JOIN Projects P ON D.fed_id = P.designer_id
                                    LEFT OUTER JOIN 
                                    (SELECT D2.fed_id, COALESCE(COUNT(DISTINCT P2.b_id),0) as num_proj 
                                    FROM Designers D2 LEFT OUTER JOIN Projects P2 ON P2.designer_id = D2.fed_id 
                                    GROUP BY D2.fed_id) P3 ON D.fed_id = P3.fed_id
                                    INNER JOIN Specializes_in S2 ON D.fed_id = S2.fed_id 
                                    WHERE LOWER(CO.name) LIKE '%{arch_name}%' AND P3.num_proj >= {num_of_projects};"""
                archs = query_db(sql_archs)
                helper.transform(archs, 'a')
            except Exception as e:
                st.write(f"An error occurred.")
        elif lead_search_options == 'Engineers':
            property_type = st.multiselect('Engineers who have experience with any of the following:', PROPERTY_TYPES)
            num_of_projects = st.number_input('Minimum number of projects in database:', value=0, min_value=0, step=1)
            eng_name = st.text_input('Engineering Company Name :')
            type_tuple = tuple(property_type)
            if len(property_type) == 1:
                type_tuple = (property_type[0], property_type[0])
            if len(eng_name) == 0:
                eng_name = '_'
            else:
                eng_name = eng_name.strip().lower()

            try:
                if not property_type:
                    sql_engineers = f"""SELECT DISTINCT CO.fed_id, CO.name, CO.email, CO.phone_number,  
                                    COALESCE(CO.num_of_employees, -1) num_employees, 
                                    COALESCE(CO.revenue_$mm, -1) as revenue, D.type, U.type_name, 
                                    P3.num_proj 
                                    FROM Designers D INNER JOIN Companies CO 
                                    ON (D.fed_id = CO.fed_id AND 
                                    (D.type = 'Engineer' OR D.type = 'Architect-Engineer'))
                                    LEFT OUTER JOIN Projects P ON D.fed_id = P.designer_id
                                    LEFT OUTER JOIN 
                                    (SELECT D2.fed_id, COALESCE(COUNT(DISTINCT P2.b_id),0) as num_proj 
                                    FROM Designers D2 LEFT OUTER JOIN Projects P2 ON P2.designer_id = D2.fed_id 
                                    GROUP BY D2.fed_id) P3 ON D.fed_id = P3.fed_id 
                                    INNER JOIN Used_as U ON P.b_id = U.b_id
                                    WHERE LOWER(CO.name) LIKE '%{eng_name}%' AND P3.num_proj >= {num_of_projects};"""
                else:
                    sql_engineers = f"""SELECT DISTINCT CO.fed_id, CO.name, CO.email, CO.phone_number,  
                                    COALESCE(CO.num_of_employees, -1) num_employees, 
                                    COALESCE(CO.revenue_$mm, -1) as revenue, D.type, U4.type_name, 
                                    P3.num_proj 
                                    FROM Designers D INNER JOIN Companies CO 
                                    ON (D.fed_id = CO.fed_id AND 
                                    (D.type = 'Engineer' OR D.type = 'Architect-Engineer')) 
                                    LEFT OUTER JOIN Projects P ON D.fed_id = P.designer_id
                                    LEFT OUTER JOIN
                                    (SELECT D2.fed_id, COALESCE(COUNT(DISTINCT P2.b_id),0) as num_proj 
                                    FROM Designers D2 LEFT OUTER JOIN Projects P2 ON P2.designer_id = D2.fed_id 
                                    GROUP BY D2.fed_id) P3 ON D.fed_id = P3.fed_id
                                    INNER JOIN Used_as U ON P.b_id = U.b_id
                                    INNER JOIN (SELECT D3.fed_id, U3.type_name FROM Used_as U3, Designers D3, 
                                    Projects P4 WHERE U3.b_id = P4.b_id AND D3.fed_id = P4.designer_id) U4 
                                    ON D.fed_id = U4.fed_id
                                    WHERE LOWER(CO.name) LIKE '%{eng_name}%' 
                                    AND U.type_name IN {type_tuple} 
                                    AND P3.num_proj >= {num_of_projects};"""
                engs = query_db(sql_engineers)
                helper.transform(engs, 'e')
            except Exception as e:
                st.write(f"An error occurred.")
        elif lead_search_options == 'Contractors':
            space = st.selectbox('Space completed over the previous 5 years (millions):', SIZES)
            num_of_projects = st.number_input('Minimum number of projects in database:', value=0, min_value=0, step=1)
            contractor_name = st.text_input('Contractor Name:')
            if space:
                space = space.split(" ")[1]
                if space == 'Any':
                    space = 0.0
                else:
                    space = int(space)
            if len(contractor_name) == 0:
                contractor_name = '_'
            else:
                contractor_name = contractor_name.strip().lower()

            try:
                sql_contractors = f"""SELECT CO.fed_id, CO.name, CO.email, CO.phone_number, 
                                        COALESCE(CO.num_of_employees, -1) num_employees, 
                                        COALESCE(CO.revenue_$mm, -1) as revenue, 
                                        COALESCE(CC.sqft_completed_5yrs, -1) as sqft_completed_5yrs,
                                        COALESCE(CC.sqft_under_construction, -1) as sqft_under_construction,
                                        COALESCE(COUNT(DISTINCT P.b_id),0) as num_proj
                                        FROM Contractors CC INNER JOIN Companies CO ON CC.fed_id = CO.fed_id 
                                        LEFT OUTER JOIN Projects P ON CC.fed_id = P.contractor_id 
                                        WHERE CC.sqft_completed_5yrs >= {space} 
                                        AND LOWER(CO.name) LIKE '%{contractor_name}%' 
                                        GROUP BY CO.fed_id, CO.name, CO.email, CO.phone_number, CO.num_of_employees, 
                                        CO.revenue_$mm, CC.sqft_completed_5yrs, CC.sqft_under_construction 
                                        HAVING COALESCE(COUNT(DISTINCT P.b_id),0) >= {num_of_projects};"""
                contractors = query_db(sql_contractors)
                helper.transform(contractors, 'c')
            except Exception:
                st.write(f"An error occurred")
        elif lead_search_options == 'Lenders':
            loan_amt = st.number_input('How much are you looking to raise? (in $mm):', min_value=0.0, step=5.0)
            loan_rate = st.number_input('What rate are you willing to pay? (in %)', min_value=0.0,
                                        max_value=100.0, step=0.25)
            loan_ltc = st.number_input('How much of the construction cost will you be financing (in %)?',
                                       min_value=0.0, max_value=100.0, step=5.0)
            num_of_projects = st.number_input('Minimum number of projects in database:', value=0, min_value=0, step=1)
            lender_name = st.text_input('Lender Name: ')
            if len(lender_name) == 0:
                lender_name = '_'
            else:
                lender_name = lender_name.strip().lower()

            try:
                if loan_amt or loan_rate or loan_ltc:
                    sql_lenders = f"""SELECT CO.fed_id, CO.name, CO.email, CO.phone_number, 
                                        COALESCE(CO.num_of_employees, -1) num_employees, 
                                        COALESCE(CO.revenue_$mm, -1) as revenue, 
                                        COALESCE(L.min_loan_size_$mm, -1) as min_loan,
                                        COALESCE(L.max_loan_size_$mm, -1) as max_loan, 
                                        COALESCE(L.min_rate, -1) as min_rate,
                                        COALESCE(L.max_rate, -1) as max_rate,
                                        COALESCE(L.max_ltc, -1) as max_ltc,
                                        COALESCE(COUNT(DISTINCT P.b_id),0) as num_proj
                                        FROM Lenders L INNER JOIN Companies CO ON L.fed_id = CO.fed_id
                                        LEFT OUTER JOIN Projects P ON L.fed_id = P.lender_id 
                                        WHERE L.min_loan_size_$mm <= {loan_amt} AND L.max_loan_size_$mm >= {loan_amt} 
                                        AND L.min_rate <= {loan_rate} AND L.max_rate >= {loan_rate} 
                                        AND L.max_ltc >= {loan_ltc} AND LOWER(CO.name) LIKE '%{lender_name}%' 
                                        GROUP BY CO.fed_id, CO.name, CO.email, CO.phone_number, 
                                        CO.num_of_employees, CO.revenue_$mm, 
                                        L.min_loan_size_$mm, L.max_loan_size_$mm, L.min_rate, L.max_rate, L.max_ltc 
                                        HAVING COALESCE(COUNT(DISTINCT P.b_id),0) >= {num_of_projects};"""
                    lenders = query_db(sql_lenders)
                    helper.transform(lenders, 'l')
            except Exception:
                st.write(f"An error occurred.")
