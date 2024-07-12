from django.http import JsonResponse
from django.db import connection

def user_stats(request, user_id):
    with connection.cursor() as cursor:
        query = """
        SELECT
            u.id AS user_id,
            u.full_name,
            
            -- Hours within schedule on weekdays
            CAST(SUM(CASE 
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours > 8 THEN 8
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours <= 8 THEN w.hours
                    ELSE 0
                END) AS DECIMAL(10, 2)) AS hours_within_schedule_weekdays,
                
            -- Hours exceeding schedule on weekdays
            CAST(SUM(CASE 
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours > 8 THEN (w.hours - 8)
                    ELSE 0
                END) AS DECIMAL(10, 2)) AS hours_exceeding_schedule_weekdays,
                
            -- Hours within schedule on weekends
            CAST(SUM(CASE 
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours > 8 THEN 8
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours <= 8 THEN w.hours
                    ELSE 0
                END) AS DECIMAL(10, 2)) AS hours_within_schedule_weekends,
                
            -- Hours exceeding schedule on weekends
            CAST(SUM(CASE 
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours > 8 THEN (w.hours - 8)
                    ELSE 0
                END) AS DECIMAL(10, 2)) AS hours_exceeding_schedule_weekends,

            -- Hours within schedule on off days
            CAST(SUM(CASE 
                    WHEN o.date IS NOT NULL AND w.hours > 8 THEN 8
                    WHEN o.date IS NOT NULL AND w.hours <= 8 THEN w.hours
                    ELSE 0
                END) AS DECIMAL(10, 2)) AS hours_within_schedule_off_days,
                
            -- Hours exceeding schedule on off days
            CAST(SUM(CASE 
                    WHEN o.date IS NOT NULL AND w.hours > 8 THEN (w.hours - 8)
                    ELSE 0
                END) AS DECIMAL(10, 2)) AS hours_exceeding_schedule_off_days,
                
            -- Total working hours (including weekdays, weekends, and off days)
            CAST(SUM(
                CASE
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours > 8 THEN 8
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours <= 8 THEN w.hours
                    ELSE 0
                END
                + CASE
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours > 8 THEN (w.hours - 8)
                    ELSE 0
                END
                + CASE
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours > 8 THEN 8
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours <= 8 THEN w.hours
                    ELSE 0
                END
                + CASE
                    WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours > 8 THEN (w.hours - 8)
                    ELSE 0
                END
                + CASE
                    WHEN o.date IS NOT NULL AND w.hours > 8 THEN 8
                    WHEN o.date IS NOT NULL AND w.hours <= 8 THEN w.hours
                    ELSE 0
                END
                + CASE
                    WHEN o.date IS NOT NULL AND w.hours > 8 THEN (w.hours - 8)
                    ELSE 0
                END
            ) AS DECIMAL(10, 2)) AS total_working_hours,
            
            -- Hourly rate calculation
            CAST(u.total_paga / (8 * 22) AS DECIMAL(10, 2)) AS hourly_rate,
            
            -- Total wage calculation
            CAST((
                (u.total_paga / (8 * 22)) * (
                    SUM(
                        CASE
                            WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours <= 8 THEN w.hours
                            WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours > 8 THEN 8
                            ELSE 0
                        END
                    ) -- Regular hours on weekdays
                )
                + (u.total_paga / (8 * 22)) * 1.25 * (
                    SUM(
                        CASE
                            WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) NOT IN (1, 7) AND w.hours > 8 THEN (w.hours - 8)
                            ELSE 0
                        END
                    ) -- Overtime hours on weekdays
                )
                + (u.total_paga / (8 * 22)) * 1.5 * (
                    SUM(
                        CASE
                            WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours <= 8 THEN w.hours
                            WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours > 8 THEN 8
                            ELSE 0
                        END
                    ) -- Regular hours on weekends
                )
                + (u.total_paga / (8 * 22)) * 2 * (
                    SUM(
                        CASE
                            WHEN DAYOFWEEK(STR_TO_DATE(w.date, '%%Y-%%m-%%d')) IN (1, 7) AND w.hours > 8 THEN (w.hours - 8)
                            ELSE 0
                        END
                    ) -- Overtime hours on weekends
                )
                + (u.total_paga / (8 * 22)) * 1.5 * (
                    SUM(
                        CASE
                            WHEN o.date IS NOT NULL AND w.hours <= 8 THEN w.hours
                            WHEN o.date IS NOT NULL AND w.hours > 8 THEN 8
                            ELSE 0
                        END
                    ) -- Regular hours on off days
                )
                + (u.total_paga / (8 * 22)) * 2 * (
                    SUM(
                        CASE
                            WHEN o.date IS NOT NULL AND w.hours > 8 THEN (w.hours - 8)
                            ELSE 0
                        END
                    ) -- Overtime hours on off days
                )
            ) AS DECIMAL(10, 2)) AS total_wage
        FROM
            users u
        JOIN
            working_days w ON u.id = w.user_id
        LEFT JOIN
            off_days o ON w.date = o.date 
        WHERE
            u.id = %s
        GROUP BY
            u.id, u.full_name;
        """
        
        cursor.execute(query, [user_id])
        row = cursor.fetchone()
        
        if row:
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, row))
            return JsonResponse(result)
        else:
            return JsonResponse({'error': 'User not found or no data available'}, status=404)
