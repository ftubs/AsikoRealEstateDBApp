"""
Transform and display data retrieved from database in web browser

Function:

    show(object: Dict or Set, string)
    transform(pd.DataFrame, string)
"""

import streamlit as st


def show(data, cat):
    """
    Displays data in web browser.

    :param data:  A dictionary or set object containing data to be displayed
    :param cat: A string object denoting processing option
    :return: void
    """
    if cat == 'p':
        st.write(f" {len(data)} result(s):  \n")
        for key, val in data.items():
            propertyInfo = 'Name: ' + val[0] + '  \n Address: ' + val[1] \
                           + '  \nSize (sqft): ' + val[2] + '  \nType: ' \
                           + (val[3][0] if len(val[3]) == 1 else ('Mixed-use consisting of ' + ', '.join(val[3]))) \
                           + '  \nProperty Class: ' + val[4] \
                           + '  \nStatus: ' + val[5] + '.'
            st.write(f"{propertyInfo}  \n")
    elif cat == 'pd':
        for prop in data:
            developer = data[prop]['developer']
            designers = ', '.join(data[prop]['designers'])
            contractors = ', '.join(data[prop]['contractors'])
            lenders = ', '.join(data[prop]['lenders'])
            owners = ', '.join(data[prop]['owners'])
            awards = 'None' if len(data[prop]['awards']) < 0 else ', '.join(data[prop]['awards'])
            status = data[prop]['status']
            completionDate = data[prop]['date']

            st.write(f"Owner(s): {owners}  \n", f"Developed by: {developer}  \n",
                     f"Designed by: {designers}  \n", f"Built by: {contractors}  \n",
                     f"Financed by: {lenders}  \n", f"Status: {status}  \n",
                     f"Completion Date: {completionDate}  \n", f"Awards won: {awards}  \n")
    elif cat in {'l', 'c'}:
        out = '  \n\n'.join(data)
        st.write(f" {len(data)} result(s):  \n{out}")
    else:
        st.write(f" {len(data)} result(s):  \n")
        for key, val in sorted(data.items(), key=lambda p: p[1][0]):
            out = f"Name: {val[0]} " \
                  f"  \nNumber of Employees: {val[1]} " \
                  f"  \nAnnual revenues: {val[2]}" \
                  f"  \n{('Regional Focus: ' if cat == 'd' else 'Type: ')} {val[3]} " \
                  f"  \n{('Specialization: ' if cat == 'd' else 'Associated Property types: ')} {', '.join(val[4])} " \
                  f"  \nNumber of projects in database: {val[5]} " \
                  f"  \nContact info (email / phone #): {val[6]} / {val[7]}."
            st.write(f"{out}  \n")


def transform(data, cat):
    """
    Transforms a dataset into a web-friendly format

    :param data: A pandas Dataframe object to be transformed
    :param cat: a string object denoting processing option
    :return: void
    """
    if data.empty:
        st.write(f"No search results.")
    else:
        dataDict = {}
        dataSet = set()
        for _, r in data.iterrows():
            if cat == 'p':
                name, strNum, strName, city, state, zip, sqft, propType, propClass, s, propid = \
                    r.loc['name'], r.loc['street_num'], r.loc['street_name'], r.loc['city'], r.loc['state'], \
                    r.loc['zip'], r.loc['size_sqf_0000'], r.loc['type_name'], r.loc['property_class'], r.loc['status'], \
                    r.loc['building_id']

                if r.loc['name'] is None:
                    name = 'None'
                if r.loc['property_class'] is None:
                    propClass = 'TBD'

                if propid not in dataDict:
                    dataDict[propid] = [name, ' '.join([str(strNum), strName, city, state, str(zip)]),
                                        "{:,.2f}mm".format(sqft), [], propClass, s]
                dataDict[propid][3].append(propType)  # mixed-use properties associated with multiple types
            elif cat == 'pd':
                devlpName = r.loc['developer']
                if devlpName not in dataDict:
                    dataDict[devlpName] = {'developer': devlpName, 'designers': set(), 'contractors': set(),
                                           'lenders': set(), 'owners': set(), 'awards': set(),
                                           'status': r.loc['status'], 'date': ''}
                dataDict[devlpName]['designers'].add(r.loc['designer'])
                dataDict[devlpName]['contractors'].add(r.loc['contractor'])
                dataDict[devlpName]['lenders'].add(r.loc['lender'])
                dataDict[devlpName]['owners'].add(r.loc['owner'])
                if r.loc['a_name'] != 'No Awards':
                    award = f"{r.loc['a_name']}, {r.loc['a_org']}({str(r.loc['a_year'])})"
                    dataDict[devlpName]['awards'].add(award)
                if r.loc['status'] == 'completed':
                    dataDict[devlpName]['date'] = r.loc['completion_date']
                else:
                    dataDict[devlpName]['date'] = f"{(r.loc['completion_date']).strftime('%Y-%m-%d')} (anticipated)"
            else:
                fid, name, employees, revenue, email, phone, numProjs = r.loc['fed_id'], r.loc['name'], \
                                                                        r.loc['num_employees'], \
                                                                        r.loc['revenue'], r.loc['email'], \
                                                                        r.loc['phone_number'], \
                                                                        r.loc['num_proj']
                revenue = "unknown" if revenue == -1 else "${:,.2f}mm".format(revenue)
                employees = "unknown" if employees == -1 else "{:,}".format(employees)
                email = "unknown" if not email else email
                phone = "unknown" if not phone else phone

                info = f"Name: {name} " \
                       f"  \nNumber of Employees: {employees} " \
                       f"  \nAnnual Revenues: {revenue}"
                contactInfo = f"  \nContract info (email / phone #): ({email} / {phone})."

                if cat in {'d', 'e', 'a'}:
                    propType = r.loc['type_name']
                    region, compType = None, None
                    if cat == 'd':
                        region = r.loc['regional_focus'] if r.loc['regional_focus'] else 'unknown'
                    if cat in {'e', 'a'}:
                        compType = r.loc['type']
                    if fid not in dataDict:
                        dataDict[fid] = [name, employees, revenue, (region if cat == 'd' else compType), [],
                                         str(numProjs), email, phone]
                    dataDict[fid][4].append(propType)
                if cat == 'c':
                    complete, underCons = r.loc['sqft_completed_5yrs'], r.loc['sqft_under_construction']
                    complete = 'unknown' if complete == -1 else '{:,.2f}mm'.format(complete)
                    underCons = 'unknown' if underCons == -1 else '{:,.2f}mm'.format(underCons)

                    addInfo = f"  \nSpace Completed over the past 5 years (sqft): {complete}" \
                              f"  \nSpace Currently under constructions (sqft): {underCons}" \
                              f"  \nNumber of projects in database: {str(numProjs)} " \
                              f"{contactInfo}"
                    info += addInfo
                    dataSet.add(info)
                if cat == 'l':
                    maxL, minL, maxR, minR, ltc = r.loc['max_loan'], r.loc['min_loan'], r.loc['max_rate'], \
                                                  r.loc['min_rate'], r.loc['max_ltc']
                    maxL = 'unknown' if maxL == -1 else '${:,.2f}mm'.format(maxL)
                    minL = 'unknown' if minL == -1 else '${:,.2f}mm'.format(minL)
                    maxR = 'unknown' if maxR == -1 else '${:,.2f}%'.format(maxR)
                    minR = 'unknown' if minR == -1 else '${:,.2f}%'.format(minR)
                    ltc = 'unknown' if ltc == -1 else '${:,.2f}%'.format(ltc)

                    addInfo = f"  \nLoan Amounts: {minL} - {maxL}" \
                              f"  \nLoan Rates: {minR} - {maxR} " \
                              f"  \nMaximum Loan-to-cost ratio: {ltc} " \
                              f"  \nNumber of projects in database: {str(numProjs)} " \
                              f"{contactInfo}"
                    info += addInfo
                    dataSet.add(info)

        if cat in {'l', 'c'}:
            show(dataSet, cat)
        else:
            show(dataDict, cat)
