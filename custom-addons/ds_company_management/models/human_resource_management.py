# from datetime import date
from odoo import models, api,_ , tools
from odoo.http import request
from helper.company_management_common import get_sql_by_department, is_ceo, is_sub_ceo, is_div_manager, is_group_leader
COLUMNS = """
                id, employee_name, company_name, department_name, project_name, project_type_name, year_of_project,
                month1, month2, month3, month4, month5, month6, month7, month8, month9, month10, month11, month12,
                average, company_manager_user_id, department_manager_user_id, company_project_id, company_id, department_id,
                employee_id, project_department_id, department_manager_project_id, user_id_sub_ceo_project, 
                start_date_contract, end_date_contract
            """
class HumanResourceManagement(models.Model):
    _name = "human.resource.management"
    _description = "Human Resource Template"
    _auto = False

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (					
                WITH HUMAN_RESOURCE_DRAFT AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY EMPLOYEE_NAME ASC) AS ID,
                        EMPLOYEE_NAME,
                        COMPANY_NAME,
                        DEPARTMENT_NAME,
                        PROJECT_NAME,
                        PROJECT_TYPE_NAME,
                        YEAR_OF_PROJECT,
                        SUM(MONTH1) AS MONTH1,
                        SUM(MONTH2) AS MONTH2,
                        SUM(MONTH3) AS MONTH3,
                        SUM(MONTH4) AS MONTH4,
                        SUM(MONTH5) AS MONTH5,
                        SUM(MONTH6) AS MONTH6,
                        SUM(MONTH7) AS MONTH7,
                        SUM(MONTH8) AS MONTH8,
                        SUM(MONTH9) AS MONTH9,
                        SUM(MONTH10) AS MONTH10,
                        SUM(MONTH11) AS MONTH11,
                        SUM(MONTH12) AS MONTH12,
                        (SELECT SUM(V.COL)/COUNT(*)
                            FROM (VALUES (SUM(MONTH1)),
                                        (SUM(MONTH2)),
                                        (SUM(MONTH3)),
                                        (SUM(MONTH4)),
                                        (SUM(MONTH5)),
                                        (SUM(MONTH6)),
                                        (SUM(MONTH7)),
                                        (SUM(MONTH8)),
                                        (SUM(MONTH9)),
                                        (SUM(MONTH10)),
                                        (SUM(MONTH11)),
                                        (SUM(MONTH12))
                                ) AS V(COL)
                            WHERE V.COL > 0
                        )::NUMERIC(20,2) AS AVERAGE,
                        COMPANY_MANAGER_USER_ID,
                        DEPARTMENT_MANAGER_USER_ID,
                        COMPANY_PROJECT_ID,
                        COMPANY_ID,
                        DEPARTMENT_ID,
                        EMPLOYEE_ID,
                        PROJECT_DEPARTMENT_ID,
                        DEPARTMENT_MANAGER_PROJECT_ID,
                        START_DATE_CONTRACT,
                        END_DATE_CONTRACT
                    FROM (
                        SELECT DISTINCT EMP.NAME AS EMPLOYEE_NAME,
                            RC.NAME AS COMPANY_NAME,
                            HD.NAME AS DEPARTMENT_NAME,
                            
                            (EXTRACT(YEAR FROM BRM.START_DATE_MONTH))::TEXT AS YEAR_OF_PROJECT,
                            
                            PT.NAME AS PROJECT_TYPE_NAME,
                            PP.DEPARTMENT_ID AS PROJECT_DEPARTMENT_ID,
                            HE.USER_ID AS COMPANY_MANAGER_USER_ID,
                            HEHD.USER_ID AS DEPARTMENT_MANAGER_USER_ID,
                            (SELECT USER_ID FROM HR_EMPLOYEE HE WHERE HE.ID = (SELECT MANAGER_ID FROM HR_DEPARTMENT HD WHERE HD.ID = PP.DEPARTMENT_ID)) AS DEPARTMENT_MANAGER_PROJECT_ID,	
                            PP.COMPANY_ID AS COMPANY_PROJECT_ID,
                            EMP.COMPANY_ID,
                            EMP.DEPARTMENT_ID, 
                            PP.NAME AS PROJECT_NAME,
                            EMP.ID AS EMPLOYEE_ID,
                            BRM.START_DATE_MONTH,
                        
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 1 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH1,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 2 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH2,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 3 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH3,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 4 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH4,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 5 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH5,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 6 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH6,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 7 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH7,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 8 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH8,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 9 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH9,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 10 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH10,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 11 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH11,
                            CASE 
                                WHEN BRM.START_DATE_MONTH IS NULL THEN 0
                                WHEN (PP.ID = (SELECT PCR2.PROJECT_ID FROM PUBLIC.PLANNING_CALENDAR_RESOURCE PCR2 WHERE BRM.BOOKING_ID=PCR2.ID)) THEN
                                    CASE 
                                        WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 12 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                        ELSE BRM.EFFORT_RATE_MONTH
                                    END
                            END::NUMERIC(20,2) MONTH12,
                            
                            (
                                SELECT STRING_AGG(
                                    (CASE
                                        WHEN EXTRACT(YEAR FROM DATE_START) < EXTRACT(YEAR FROM CURRENT_DATE) AND   
                                            EXTRACT(YEAR FROM DATE_END) >= EXTRACT(YEAR FROM CURRENT_DATE) THEN 1
                                        ELSE EXTRACT(MONTH FROM DATE_START)
                                        END)::TEXT || '-' || 
                                    (CASE
                                        WHEN EXTRACT(YEAR FROM DATE_START) < EXTRACT(YEAR FROM CURRENT_DATE) 
                                            AND EXTRACT(YEAR FROM DATE_END) >= EXTRACT(YEAR FROM CURRENT_DATE) 
                                            THEN EXTRACT(YEAR FROM CURRENT_DATE)
                                        ELSE EXTRACT(YEAR FROM DATE_START)
                                    END)::TEXT, ','
                                    ) START_DATE_CONTRACT
                                FROM HR_CONTRACT 
                                WHERE EMPLOYEE_ID=EMP.ID AND (STATE = 'open' OR STATE = 'close' OR STATE = 'draft') 
                            ),
                            (SELECT
                                    STRING_AGG(
                                    (CASE
                                        WHEN DATE_END IS NULL THEN 0
                                        WHEN --DATE_END IS NULL OR 
                                              EXTRACT(YEAR FROM DATE_END) > EXTRACT(YEAR FROM CURRENT_DATE) 
                                            THEN 12
                                        ELSE EXTRACT(MONTH FROM DATE_END)
                                    END)::TEXT 
                                    || '-' ||
                                    (CASE
                                        WHEN DATE_END IS NULL THEN 0 --EXTRACT(YEAR FROM CURRENT_DATE) 
                                        ELSE EXTRACT(YEAR FROM DATE_END)
                                    END)::TEXT
                                        , ',') END_DATE_CONTRACT
                                FROM HR_CONTRACT 
                                WHERE EMPLOYEE_ID=EMP.ID AND (STATE = 'open' OR STATE = 'close' OR STATE = 'draft')	
                            )
                        FROM HR_EMPLOYEE AS EMP 
                        RIGHT JOIN HR_CONTRACT AS HC
                            ON EMP.ID = HC.EMPLOYEE_ID
                        LEFT JOIN BOOKING_RESOURCE_MONTH AS BRM 
                            ON HC.EMPLOYEE_ID = BRM.EMPLOYEE_ID
                            AND EXTRACT(YEAR FROM brm.start_date_month) = EXTRACT(YEAR FROM CURRENT_DATE)
                        LEFT JOIN PLANNING_CALENDAR_RESOURCE AS PCR 
                            ON BRM.BOOKING_ID = PCR.ID
                        LEFT JOIN PROJECT_PROJECT AS PP 
                            ON PCR.PROJECT_ID=PP.ID
                        LEFT JOIN PROJECT_TYPE AS PT
                            ON PT.ID = PP.PROJECT_TYPE
                        
                        LEFT JOIN PUBLIC.ESTIMATION_WORK AS EW 
                            ON PP.ESTIMATION_ID=EW.ID
                        
                        LEFT JOIN RES_COMPANY AS RC
                            ON RC.ID = EMP.COMPANY_ID
                        LEFT JOIN HR_DEPARTMENT AS HD
                            ON HD.ID = EMP.DEPARTMENT_ID
                        LEFT JOIN HR_EMPLOYEE AS HE
                            ON HE.WORK_EMAIL = RC.USER_EMAIL
                        LEFT JOIN HR_EMPLOYEE AS HEHD
                            ON HEHD.ID = HD.MANAGER_ID
                        WHERE hc.state != 'cancel' 
                                  AND (hc.date_end IS NULL OR EXTRACT(YEAR FROM hc.date_end) >= EXTRACT(YEAR FROM CURRENT_DATE))
                -- 		WHERE (BRM.START_DATE_MONTH IS NULL 
                -- 			   	OR EXTRACT(YEAR FROM BRM.START_DATE_MONTH) = EXTRACT(YEAR FROM CURRENT_DATE)
                -- 			  )
                -- 			   AND (EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) 
                -- 									   	FROM HR_CONTRACT AS HC1 
                -- 									   	WHERE HC1.EMPLOYEE_ID=EMP.ID)
                -- 						  ) IS NOT NULL)
                    ) AS X
                    GROUP BY EMPLOYEE_NAME, 
                            COMPANY_NAME, 
                            DEPARTMENT_NAME, 
                            PROJECT_NAME, 
                            PROJECT_TYPE_NAME, 
                            YEAR_OF_PROJECT, 
                            COMPANY_MANAGER_USER_ID, 
                            DEPARTMENT_MANAGER_USER_ID, 
                            COMPANY_PROJECT_ID, 
                            COMPANY_ID, 
                            DEPARTMENT_ID, 
                            EMPLOYEE_ID, 
                            PROJECT_DEPARTMENT_ID, 
                            DEPARTMENT_MANAGER_PROJECT_ID, 
                            START_DATE_CONTRACT, 
                            END_DATE_CONTRACT
                    ),
                    GET_ID_SUB_CEO_OF_PROJECT  AS (
                        SELECT PROJECT_PROJECT.COMPANY_ID as ID_PROJECT_COMPANY , 
                                  HR_EMPLOYEE.USER_ID AS  USER_ID_SUB_CEO_PROJECT
                        FROM PROJECT_PROJECT 
                        INNER JOIN RES_COMPANY ON PROJECT_PROJECT.COMPANY_ID = RES_COMPANY.ID
                        INNER JOIN HR_EMPLOYEE ON HR_EMPLOYEE.WORK_EMAIL =  RES_COMPANY.USER_EMAIL
                    ),
                    hr_contract_order_by AS (
                        SELECT
                            employee_id,
                            date_start,
                            date_end

                        FROM hr_contract
                        WHERE state != 'cancel' AND
                                ( EXTRACT(YEAR FROM date_start) >= EXTRACT(YEAR FROM CURRENT_DATE) OR
                                    EXTRACT(YEAR FROM date_end) >= EXTRACT(YEAR FROM CURRENT_DATE) OR
                                    date_end IS NULL)
                        ORDER BY employee_id, date_start
                        ),
                        
                    duration_contract AS (
                        SELECT
                            employee_id,
                            STRING_AGG(
                                        EXTRACT(MONTH FROM date_start)::TEXT || ' ' || 
                                        EXTRACT(YEAR FROM date_start)::TEXT || ' ' ||
                                        COALESCE(NULLIF(EXTRACT(MONTH FROM date_end), NULL), 12)::TEXT || ' ' || 
                                        COALESCE(NULLIF(EXTRACT(YEAR FROM date_end), NULL), EXTRACT(YEAR FROM CURRENT_DATE))::TEXT,
                                        ','
                                        ) duration_contract
                        FROM hr_contract_order_by
                        GROUP BY employee_id
                    )
                    SELECT 
                        HRD.ID, 
                        HRD.EMPLOYEE_NAME, 
                        HRD.COMPANY_NAME, 
                        HRD.DEPARTMENT_NAME, 
                        HRD.PROJECT_NAME, 
                        HRD.PROJECT_TYPE_NAME, 
                        HRD.YEAR_OF_PROJECT, 
                        HRD.MONTH1, 
                        HRD.MONTH2, 
                        HRD.MONTH3, 
                        HRD.MONTH4, 
                        HRD.MONTH5, 
                        HRD.MONTH6, 
                        HRD.MONTH7, 
                        HRD.MONTH8, 
                        HRD.MONTH9, 
                        HRD.MONTH10, 
                        HRD.MONTH11, 
                        HRD.MONTH12, 
                        HRD.AVERAGE, 
                        HRD.COMPANY_MANAGER_USER_ID,
                        HRD.DEPARTMENT_MANAGER_USER_ID, 
                        HRD.COMPANY_PROJECT_ID, 
                        HRD.COMPANY_ID, 
                        HRD.DEPARTMENT_ID, 
                        HRD.EMPLOYEE_ID, 
                        HRD.PROJECT_DEPARTMENT_ID, 
                        HRD.DEPARTMENT_MANAGER_PROJECT_ID, 
                        GIS.USER_ID_SUB_CEO_PROJECT,
                        HRD.START_DATE_CONTRACT, 
                        HRD.END_DATE_CONTRACT,
                        dc.duration_contract

                    FROM HUMAN_RESOURCE_DRAFT AS HRD 
                    LEFT JOIN GET_ID_SUB_CEO_OF_PROJECT AS GIS
                        ON HRD.COMPANY_PROJECT_ID = GIS.ID_PROJECT_COMPANY
                    LEFT JOIN duration_contract AS dc
			            ON HRD.employee_id = dc.employee_id

                    GROUP BY HRD.ID, 
                            HRD.EMPLOYEE_NAME, 
                            HRD.COMPANY_NAME, 
                            HRD.DEPARTMENT_NAME, 
                            HRD.PROJECT_NAME, 
                            HRD.PROJECT_TYPE_NAME, 
                            HRD.YEAR_OF_PROJECT, 
                            HRD.MONTH1, 
                            HRD.MONTH2, 
                            HRD.MONTH3, 
                            HRD.MONTH4, 
                            HRD.MONTH5, 
                            HRD.MONTH6, 
                            HRD.MONTH7, 
                            HRD.MONTH8, 
                            HRD.MONTH9, 
                            HRD.MONTH10, 
                            HRD.MONTH11, 
                            HRD.MONTH12, 
                            HRD.AVERAGE, 
                            HRD.COMPANY_MANAGER_USER_ID,
                            HRD.DEPARTMENT_MANAGER_USER_ID, 
                            HRD.COMPANY_PROJECT_ID, 
                            HRD.COMPANY_ID, 
                            HRD.DEPARTMENT_ID, 
                            HRD.EMPLOYEE_ID, 
                            HRD.PROJECT_DEPARTMENT_ID, 
                            HRD.DEPARTMENT_MANAGER_PROJECT_ID, 
                            gis.user_id_sub_ceo_project,
                            HRD.START_DATE_CONTRACT, 
                            HRD.END_DATE_CONTRACT,
                            dc.duration_contract
    )
        """ % (self._table)
        )

    # def get_default_action(self):
    #     action_id = self.env.ref(
    #     'human_resource_template.action_dynamic_dashboard')
    #     if action_id:
    #         return action_id.id
    #     else:
    #         return False

    def get_current_company_value(self):
        cookies_cids = [int(r) for r in request.httprequest.cookies.get('cids').split(",")] \
            if request.httprequest.cookies.get('cids') \
            else [request.env.user.company_id.id]

        for company_id in cookies_cids:
            if company_id not in self.env.user.company_ids.ids:
                cookies_cids.remove(company_id)
        if not cookies_cids:
            cookies_cids = [self.env.company.id]
        if len(cookies_cids) == 1:
            cookies_cids.append(0)
        return cookies_cids

    # function get data human resource
    @api.model
    def get_list_human_resource(self):
        current_user = self.env.user
        selected_companies = self.get_current_company_value()
        
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()		
        cr = self._cr
    
        sql_domain_for_company = ''
        sql_for_department = ''

        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department_emp = ''
            sql_domain_for_department_proj = ''
        else: 
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (department_id  NOT IN ' + str(tuple(id_all_mirai_department)) \
                                            + ' OR department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (PROJECT_DEPARTMENT_ID  NOT IN ' + str(tuple(id_all_mirai_department)) \
                                            + ' OR PROJECT_DEPARTMENT_ID IS NULL )' 

        if is_ceo(current_user):
            sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_sub_ceo(current_user):
            sql_domain_for_company = 'where ( company_manager_user_id = ' + str(current_user.id) \
                                        + ' and company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_div_manager(current_user) or is_group_leader(current_user):
            sql_domain_for_company = 'where ( company_id = ' + str(current_user.company_id.id)
            sql_for_department = get_sql_by_department(self)


        sql = ("""select """ + COLUMNS + """ from human_resource_management """)
        sql += sql_domain_for_company
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj
        sql += sql_for_department

        cr.execute(sql)
        list_human_resource = cr.fetchall()

        return {
            'list_human_resource': list_human_resource,
        }
    
    @api.model
    def get_list_human_resource_support(self):
        current_user = self.env.user
        selected_companies = self.get_current_company_value()
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()		
        # div_manager_department_id =  self.env.user.employee_ids.department_id.id
        cr = self._cr
    
        # sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ' or company_project_id in ' + str(tuple(selected_companies)) + ')'
        sql_domain_for_company = ''

        sql_domain_for_role = ''

        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department_emp = ''
            sql_domain_for_department_proj = ''
        else :
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (department_id  NOT IN ' + str(tuple(id_all_mirai_department)) \
                                            + ' OR department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (PROJECT_DEPARTMENT_ID  NOT IN ' + str(tuple(id_all_mirai_department)) \
                                            + ' OR PROJECT_DEPARTMENT_ID IS NULL )' 

        if is_ceo(current_user):
            sql_domain_for_company = 'where company_id != company_project_id and  ( company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_sub_ceo(current_user):
            sql_domain_for_company = ' where ( company_manager_user_id != ' + str(current_user.id) \
                                    + ' and user_id_sub_ceo_project = ' + str(current_user.id)\
                                    + ' and company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_div_manager(current_user) or is_group_leader(current_user):
            sql_domain_for_role = ' where ( (department_manager_user_id != ' + str(current_user.id) \
                                + ' or department_manager_user_id is null  )' \
                                + ' and department_manager_project_id = ' + str(current_user.id) \
                                + ' and company_id in ' + str(tuple(selected_companies)) + ')'

        sql = ("""select """ + COLUMNS + """ from human_resource_management """)
        sql += sql_domain_for_company
        sql += sql_domain_for_role
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj

        cr.execute(sql)
        list_human_resource_support = cr.fetchall()

        return {
            'list_human_resource_support': list_human_resource_support,
        }

    @api.model
    def get_human_resource_free(self):
        current_user = self.env.user
        selected_companies = self.get_current_company_value()
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()
        cr = self._cr
        sql_domain_for_company = ''
        sql_for_department = ''
        sql_domain_for_role = ''

        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department_emp = ''
            sql_domain_for_department_proj = ''
        else:
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (human_resource_management.department_id  NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR human_resource_management.department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (human_resource_management.PROJECT_DEPARTMENT_ID  NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR human_resource_management.PROJECT_DEPARTMENT_ID IS NULL )' 

        sql_domain_for_group_by = 'GROUP BY employee_id, employee_name ,company_name, department_name, company_id, start_date_contract, end_date_contract order by employee_name asc'

        if is_ceo(current_user):
            sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_sub_ceo(current_user):
            sql_domain_for_role = 'where ( company_manager_user_id = ' + str(current_user.id) + ')'

        elif is_div_manager(current_user) or is_group_leader(current_user):
            sql_domain_for_role = ' where (department_manager_user_id = ' + str(current_user.id) + ''
            sql_for_department = get_sql_by_department(self)


        sql = ("""SELECT  employee_id, employee_name, company_name, department_name,
                SUM (month1 ) as month1,
                SUM (month2) as month2,
                SUM (month3) as month3,
                SUM (month4) as month4,
                SUM (month5) as month5,
                SUM (month6) as month6,
                SUM (month7) as month7,
                SUM (month8) as month8,
                SUM (month9) as month9,
                SUM (month10) as month10,
                SUM (month11) as month11,
                SUM (month12) as month12,
                company_id,
                start_date_contract,
                end_date_contract
                FROM human_resource_management 
                    """)
        sql += sql_domain_for_company
        sql += sql_domain_for_role
        sql += sql_for_department
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj
        sql += sql_domain_for_group_by

        cr.execute(sql)

        list_human_resource_free = cr.fetchall()

        return {
            'list_human_resource_free': list_human_resource_free,
        }
        
    @api.model
    def human_resource_it_boc_management(self):
        user_login = str(self.env.user.id)
        selected_companies = str(tuple(self.get_current_company_value()))
        department_removed = "(SELECT department_id FROM department_mirai_fnb)"
        role_user = self.check_role_user_login()
        cr = self._cr
        
        department_domain = ''
        company_domain = ''
  
        if len(department_removed) != 0:
            department_domain += ' AND (department_id IS NULL OR department_id NOT IN ' + department_removed \
                                + ') AND (PROJECT_DEPARTMENT_ID IS NULL OR PROJECT_DEPARTMENT_ID NOT IN ' + department_removed + ')'
        
        if role_user == 'ceo':
            company_domain += ' AND (company_id in ' + selected_companies + ')'
        elif role_user == 'subceo':
            company_domain += ' AND (company_id in ' + selected_companies \
                               + ' AND company_manager_user_id = ' + user_login + ')'
        else:
            company_domain += ' AND (department_manager_user_id = ' + user_login + ')'

        query = """
                  SELECT 
                        --employee_id,
                        employee_name,
                        company_name,
                        department_name,
                        project_name,
                        project_type_name,
                        month1,
                        month2,
                        month3,
                        month4,
                        month5,
                        month6,
                        month7,
                        month8,
                        month9,
                        month10,
                        month11,
                        month12,
                        duration_contract
                  FROM human_resource_management 
                    WHERE project_type_name != 'Internal' """ \
                + department_domain \
                + company_domain
    
        cr.execute(query)
        data = cr.fetchall()
        overview = self.get_total_man_month_project_billable(user_login, selected_companies, role_user)
        total_member_company = self.get_total_member_company(user_login, selected_companies, role_user)
        
        return {'data': data, 'overview': overview, 'total_member_company': total_member_company}



    def get_total_man_month_project_billable(self, user_login, selected_companies, role_user):
        cr = self._cr
        div_login = str(self.env.user.employee_id.id)
        domain = ''
        if role_user == 'ceo':
            domain += ' company_id IN ' + selected_companies
        elif role_user == 'subceo':
            domain += ' representative = ' + user_login + ' AND company_id IN ' + selected_companies
        else:
            domain += ' manager_id = ' + div_login + ' AND company_id IN ' + selected_companies
            
        query = """
                SELECT
                    months,
                    SUM(mm) AS mm
                FROM human_resource_management_itboc
                WHERE years = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND """ + domain \
                + ' GROUP BY months ORDER BY months'
        cr.execute(query)
        return cr.fetchall()

    def get_total_member_company (self, user_login, selected_companies, role_user):
        cr = self._cr
        domain = ''
        company_user_id = str(self.env.user.company_id.id)
        if role_user == 'ceo':
            domain += ' company_id IN ' + selected_companies
        elif role_user == 'subceo':
            domain += ' sub_ceo = ' + user_login + ' AND company_id IN ' + selected_companies
        else:
            domain += ' company_id = ' + company_user_id + ' AND company_id IN ' + selected_companies
            
        query = """
                SELECT
                    EXTRACT(MONTH FROM months) AS months,
                    COUNT(DISTINCT employee_id) AS total_members
                FROM human_resource_management_member_company
                WHERE EXTRACT(YEAR FROM months) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND """ + domain \
                + ' GROUP BY months ORDER BY months'
        cr.execute(query)
        return cr.fetchall()
    
    
    def check_role_user_login(self):
        if self.env.user.has_group('ds_company_management.group_company_management_ceo') == True:
            return 'ceo'
        elif self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_ceo') == False:
            return 'subceo'
        else:
            return 'div'
      
            