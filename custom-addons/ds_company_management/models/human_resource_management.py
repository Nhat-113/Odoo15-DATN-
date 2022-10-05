# from datetime import date
from odoo import models, api,_ , tools
from odoo.http import request

class HumanResourceManagement(models.Model):
    _name = "human.resource.management"
    _description = "Human Resource Template"
    _auto = False

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
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
                        (
                            SELECT SUM(V.COL)/COUNT(*)
                            FROM (VALUES (SUM(MONTH1)),(SUM(MONTH2)),(SUM(MONTH3)),(SUM(MONTH4)),(SUM(MONTH5)),(SUM(MONTH6)),(SUM(MONTH7)),(SUM(MONTH8)),(SUM(MONTH9)),(SUM(MONTH10)),(SUM(MONTH11)),(SUM(MONTH12))) AS V(COL)
                            WHERE V.COL > 0
                        ) AS AVERAGE,
                        COMPANY_MANAGER_USER_ID,
                        DEPARTMENT_MANAGER_USER_ID,
                        COMPANY_ID,
                        DEPARTMENT_ID	
                    FROM (
                        SELECT DISTINCT EMP.NAME AS EMPLOYEE_NAME,
                        (SELECT NAME FROM RES_COMPANY RP WHERE RP.ID = EMP.COMPANY_ID) AS COMPANY_NAME,
                        (SELECT NAME FROM HR_DEPARTMENT HD WHERE HD.ID = EMP.DEPARTMENT_ID) AS DEPARTMENT_NAME,
                        BRM.START_DATE_MONTH,
                        (
                            EXTRACT(YEAR FROM BRM.START_DATE_MONTH)
                        )::TEXT AS YEAR_OF_PROJECT,
                        PP.NAME AS PROJECT_NAME,
                        (SELECT NAME FROM PROJECT_TYPE PT WHERE PT.ID = EW.PROJECT_TYPE_ID) AS PROJECT_TYPE_NAME,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (1 = EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (1 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 1 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 1 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (1 = EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 1 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (1 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH1,
                        CASE
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (2 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (2 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 2 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 2 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (2 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 2 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (2 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH2,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (3 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (3 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 3 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 3 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (3 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 3 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (3 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH3,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (4 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (4 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 4 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 4 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (4 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 4 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (4 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH4,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (5 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (5 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 5 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 5 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (5 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 5 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (5 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH5,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (6 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (6 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 6 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 6 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (6 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 6 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (6 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH6,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (7 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (7 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 7 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 7 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (7 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 7 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (7 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH7,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (8 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (8 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 8 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 8 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (8 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 8 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (8 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH8,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (9 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (9 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 9 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 9 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (9 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 9 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (9 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH9,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (10 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (10 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 10 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 10 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (10 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 10 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (10 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH10,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (11 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (11 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 11 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 11 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (11 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 11 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (11 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH11,
                        CASE 
                            WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) THEN 
                                CASE
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM NOW()) ) THEN 0
                                    WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM NOW()) ) THEN 
                                        CASE 
                                            WHEN (12 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN 0
                                            WHEN (12 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID))) THEN -1
                                        END	 
                                END	
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) < EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 12 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL)  THEN 0
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                            WHEN (EXTRACT(YEAR FROM (SELECT(MIN( HC2.DATE_START)) FROM HR_CONTRACT AS HC2 WHERE HC2.EMPLOYEE_ID=EMP.ID)) = EXTRACT(YEAR FROM BRM.START_DATE_MONTH)) THEN
                                CASE 
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 12 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (12 >= EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN 0
                                    WHEN (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) <> 12 OR EXTRACT(MONTH FROM BRM.START_DATE_MONTH) IS NULL) AND (12 < EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)))  THEN -1
                                    ELSE BRM.EFFORT_RATE_MONTH
                                END
                        END MONTH12,
                        (SELECT USER_ID FROM HR_EMPLOYEE HE WHERE HE.WORK_EMAIL = (SELECT USER_EMAIL FROM RES_COMPANY RC WHERE RC.ID = EMP.COMPANY_ID ) ) AS COMPANY_MANAGER_USER_ID,
                        (SELECT USER_ID FROM HR_EMPLOYEE HE WHERE HE.ID = (SELECT MANAGER_ID FROM HR_DEPARTMENT HD WHERE HD.ID = EMP.DEPARTMENT_ID)) AS DEPARTMENT_MANAGER_USER_ID,
                        EMP.COMPANY_ID,
                        EMP.DEPARTMENT_ID
                        FROM (PUBLIC.HR_EMPLOYEE AS EMP
                            LEFT JOIN PUBLIC.HR_CONTRACT AS HC ON EMP.ID = HC.EMPLOYEE_ID)
                                LEFT JOIN PUBLIC.BOOKING_RESOURCE_MONTH AS BRM ON HC.EMPLOYEE_ID = BRM.EMPLOYEE_ID
                                    LEFT JOIN PUBLIC.PLANNING_CALENDAR_RESOURCE AS PCR ON BRM.EMPLOYEE_ID = PCR.EMPLOYEE_ID
                                        LEFT JOIN PUBLIC.PROJECT_PROJECT AS PP ON PCR.PROJECT_ID=PP.ID
                                            LEFT JOIN PUBLIC.ESTIMATION_WORK AS EW ON PP.ESTIMATION_ID=EW.ID
                        WHERE ((EXTRACT(YEAR FROM BRM.START_DATE_MONTH) IS NULL) OR ((EXTRACT(YEAR FROM BRM.START_DATE_MONTH) = EXTRACT(YEAR FROM NOW())) AND (EXTRACT(MONTH FROM BRM.START_DATE_MONTH) BETWEEN 1 AND 12))) AND (EXTRACT(MONTH FROM (SELECT(MIN( HC1.DATE_START)) FROM HR_CONTRACT AS HC1 WHERE HC1.EMPLOYEE_ID=EMP.ID)) IS NOT NULL)
                    ) AS X
                    GROUP BY EMPLOYEE_NAME, COMPANY_NAME, DEPARTMENT_NAME, PROJECT_NAME, PROJECT_TYPE_NAME, YEAR_OF_PROJECT, COMPANY_MANAGER_USER_ID, DEPARTMENT_MANAGER_USER_ID, COMPANY_ID, DEPARTMENT_ID
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
        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value();
        # div_manager_department_id =  self.env.user.employee_ids.department_id.id
        cr = self._cr
        sql_domain_for_company = 'where company_id in ' + str(tuple(selected_companies)) 
        sql_domain_for_role = ''

        if self.env.user.has_group('ds_company_management.group_company_management_ceo') == True:
            sql_domain_for_role = ''

        elif self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_ceo') == False:
            sql_domain_for_role = 'and company_manager_user_id = ' + \
                str(user_id_login)

        elif self.env.user.has_group('ds_company_management.group_company_management_div') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == False:
            sql_domain_for_role = ' and department_manager_user_id = ' + \
                str(user_id_login)

        sql = ("""select * from human_resource_management """)
        sql += sql_domain_for_company
        sql += sql_domain_for_role

        cr.execute(sql)
        list_human_resource = cr.fetchall()

        return {
            'list_human_resource': list_human_resource,
        }
