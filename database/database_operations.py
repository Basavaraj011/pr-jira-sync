"""
Data access functions for running SQL queries and returning data.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import text
import logging
from datetime import datetime
from config.settings import DATABASE_NAME, DATABASE_SCHEMA, DATABASE_URL, JIRA_URL
from connections.database_connections import DatabaseManager

logger = logging.getLogger(__name__)

def fetch_errors_from_db(db_manager, limit: int = None, severity_filter: str = None, similarity_search: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch error logs from the ERROR_LOGS table
    Args:
        limit: Maximum number of errors to fetch
        severity_filter: Filter by severity level (LOW, MEDIUM, HIGH, CRITICAL)
        similarity_search: Flag to indicate if the fetch is for similarity search
    Returns:
        List of error records
    """
    try:
        if not similarity_search:
            col_list = [
                    "error_id", 
                    "event_timestamp",
                    "error_message",
                    "stack_trace",
                    "cleaned_stack_trace",
                    "project_id",
                    "repo_name",
                    "error_tool"
                    ]
        query = f"""
            SELECT 
                {', '.join(col_list)}
            FROM {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
            WHERE processed = 0
        """
        params = {}
        ordered_params = []
        
        if severity_filter:
            query += " AND severity_level = @severity"
            params['severity'] = severity_filter
            ordered_params.append('severity')
        
        query += " ORDER BY event_timestamp DESC"
        
        if limit:
            query += f"\nOFFSET 0 ROWS\nFETCH NEXT {limit} ROWS ONLY"
        
        # Use DatabaseManager's fetch_all method
        results = db_manager.fetch_all(query, params, ordered_params if params else None)
        
        logger.info(f"Fetched {len(results)} errors from database")
        return results
        
    except Exception as e:
        logger.error(f"Failed to fetch errors from database: {e}", exc_info=True)
        return []


"""
Data access functions for running SQL queries and returning data.
"""


def update_processed_errors(error_id: int,db_manager):
    """
    Update processed errors in the ERROR_LOGS table
    """
    #db_manager = DatabaseManager(DATABASE_URL)
    try:
        query = f"""
            UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
            SET processed = 1
            WHERE processed = 0
            AND error_id = {error_id}
        """
        db_manager.execute(query)
        logger.info("Updated processed errors in database")
        return True
    except Exception as e:
        logger.error(f"Failed to update processed errors in database: {e}", exc_info=True)
        return False
    

def fetch_jira_deets_from_db(error_id, db_manager = None) -> List[Dict[str, Any]]:
    """ Fetch error logs from the ERROR_LOGS table
    Args:
        limit: Maximum number of errors to fetch
        severity_filter: Filter by severity level (LOW, MEDIUM, HIGH, CRITICAL)
        similarity_search: Flag to indicate if the fetch is for similarity search
    Returns:
        List of error records """
    try:
        query = f"""
            SELECT 
            {error_id['query_error_id']} as error_id,
            ERROR_LOGS.root_cause_id,
            ROOT_CAUSES.root_cause,
            ERROR_LOGS.error_tool,
            ERROR_LOGS.error_message,
            ERROR_LOGS.stack_trace,
            ROOT_CAUSES.root_cause,
            ERROR_LOGS.severity_level
            FROM {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
            JOIN {DATABASE_NAME}.{DATABASE_SCHEMA}.ROOT_CAUSES
            ON 
            ROOT_CAUSES.root_cause_id = ERROR_LOGS.root_cause_id
            WHERE 1=1
            AND ERROR_LOGS.error_id =  '{error_id['similar_id']}'
        """
        # Use DatabaseManager's fetch_all method
        results = db_manager.fetch_all(query)
        
        logger.info(f"Fetched {len(results)} errors from database")
        return results[0], results[0]['root_cause'] if results else None
    except Exception as e:
        logger.error(f"Failed to fetch details from database: {e}", exc_info=True)
        return [], None


def update_processed_errors(db_manager):
    """
    Insert error records into the ERROR_LOGS table
    """
    #db_manager = DatabaseManager(DATABASE_URL)
    try:
        query = f"""
            UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
            SET processed = 1
            WHERE processed = 0"""
        db_manager.execute(query)
        logger.info("Updated processed errors in database")
        return True
    except Exception as e:
        logger.error(f"Failed to update processed errors in database: {e}", exc_info=True)
        return False


def insert_error_logs_data(error_data: List[Dict[str, Any]], db_manager) -> bool:
    """
    Insert error logs data into the ERROR_LOGS table
    Args:
        error_data: List of error records to insert
    Returns:
        True if insertion is successful, False otherwise
    """
    try:
        for error in error_data:
            query = f""" INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS 
                (error_message, stack_trace, cleaned_stack_trace, severity_level, project_id, repo_name, event_timestamp)
                VALUES 
                (@error_message, @stack_trace, @cleaned_stack_trace, @severity_level, @project_id, @repo_name, @event_timestamp);"""
            params = {
                'error_message': error.get('error_message', ''),
                'stack_trace': error.get('stack_trace', ''),
                'cleaned_stack_trace': error.get('cleaned_stack_trace', ''),
                'severity_level': str(error.get('severity_level', '')),
                'project_id': error.get('project_id', ''),
                'repo_name': error.get('repo_name', ''),
                'event_timestamp': error.get('event_timestamp', '')
            }
            ordered_params = ['event_timestamp','error_tool','project_name', 'repo_name', 'error_message', 'stack_trace', 'cleaned_stack_trace','severity_level']
            db_manager.execute(query, params, ordered_params)
        return True
    except Exception as e:
        logger.error(f"Failed to insert error logs data into database: {e}", exc_info=True)
        return False
    

def upsert_rootcause_data(rca_data: List[Dict[str, Any]], rca, is_ai: bool, db_manager) -> bool:
    """
    Upsert root cause data into the ROOT_CAUSES table
    Args:
        rca_data: List of root cause records to insert
    Returns:
        True if insertion is successful, False otherwise
    """
    try:
        if is_ai:
            
            query = f"""INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.ROOT_CAUSES 
                (error_id, root_cause)
                OUTPUT INSERTED.root_cause_id
                VALUES 
                (@error_id, @root_cause);"""
            params = {
                'error_id': rca_data['error_id'],
                'root_cause': str(rca)
            }
            ordered_params = ['error_id', 'root_cause']
            root_cause_id_result = db_manager.fetch_one(query, params, ordered_params)
            root_cause_id = root_cause_id_result['root_cause_id'] if root_cause_id_result else None
            logger.info(f"Inserted {len(rca_data)} root cause records into database")
        else:
            root_cause_id = rca_data['root_cause_id']
        

        
        
        query = f"""
                UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
                SET ROOT_CAUSE_ID = @root_cause_id, severity_level = @severity_level
                WHERE error_id = @error_id"""

        
        params = {
            'root_cause_id': root_cause_id,
            'error_id': rca_data['error_id'],
            'severity_level': str(rca['severity'])
        }
        ordered_params = ['root_cause_id', 'severity_level', 'error_id']
        db_manager.execute(query, params, ordered_params)
        logger.info(f"Updated ERROR_LOGS with ROOT_CAUSE_ID for error_id {rca_data['error_id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert root cause data into database: {e}", exc_info=True)
        return False
    
def insert_jira_ticket_details(ticket_key, incident, rca, db_manager) -> bool:
    """
    Insert JIRA ticket details into the JIRA_TICKETS table
    Args:
        ticket_key: The key of the created JIRA ticket
    Returns:
        True if insertion is successful, False otherwise
    """
    try:
        print(f"Inserting JIRA ticket details into database for ticket {ticket_key}")
        description = f"""Error Tools: {incident['error_tool']}
            Stack Trace: {incident['stack_trace']}
            Root Cause Analysis:
            {rca}
            Environment: Production
            Service: Backend API   """
        
        insert_query = f"""
            INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.JIRA_TICKET_DETAILS 
            (ticket_id, error_id, jira_title, description, created_at, jira_ticket_link)
            OUTPUT INSERTED.jira_id
            VALUES (@ticket_id, @error_id, @jira_title, @description, @created_at, @jira_ticket_link);
        """
        params = {
            'ticket_id': ticket_key,
            'error_id': incident['error_id'],
            'jira_title': incident['error_message'],
            'description': description,
            'created_at': datetime.utcnow(),
            'jira_ticket_link': f"{JIRA_URL}/browse/{ticket_key}"
        }
        
        ordered_params = ['ticket_id', 'error_id', 'jira_title', 'description', 'created_at', 'jira_ticket_link']
        #db_manager.execute(insert_query, params, ordered_params)
        

        jira_id_result = db_manager.fetch_one(insert_query, params, ordered_params)
        jira_id = jira_id_result['jira_id'] if jira_id_result else None
        logger.info(f"Inserted JIRA ticket details into database for ticket {ticket_key}")
        print(f"Retrieved JIRA_ID {jira_id} for ticket {ticket_key}")
        
        update_query = f"""
            UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
            SET jira_id = @jira_id
            WHERE error_id = @error_id
        """

        update_params = {
            'jira_id': jira_id,
            'error_id': incident['error_id']
        }

        ordered_params = ['jira_id', 'error_id']

        db_manager.execute(update_query, update_params, ordered_params)

        logger.info(f"Updated ERROR_LOGS with JIRA ticket ID for error_id {incident['error_id']} with JIRA ID {jira_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert JIRA ticket details into database: {e}", exc_info=True)
        return False
    
def insert_errors_into_db(errors: List[Dict[str, Any]], db_manager, team_name: str, project_name: str, repo_name: str) -> bool:
    """
    Insert error records into the ERROR_LOGS table
    """
    #db_manager = DatabaseManager(DATABASE_URL)
    print(f"Some Details: {project_name}, {repo_name}")
    try:
        for error in errors:
            query = f"""
                INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
                (event_timestamp,error_tool,project_id,repo_name,error_message, stack_trace, cleaned_stack_trace, severity_level, processed)
                VALUES ( GETUTCDATE(), @error_tool,@project_name,@repo_name, @error_message, @stack_trace, @cleaned_stack_trace, 'HIGH', 0)
            """
            params = {
                'error_tool': error['tool'],
                "project_name": project_name,
                "repo_name": repo_name,
                'error_message': error['main_error'],
                'stack_trace': error['stack_trace'],
                'cleaned_stack_trace': error['cleaned_stack_trace']
            }
            ordered_params = ['event_timestamp','error_tool','project_name', 'repo_name', 'error_message', 'stack_trace', 'cleaned_stack_trace','severity_level']
            db_manager.execute(query, params, ordered_params)
        print(f"Inserted {len(errors)} errors into database")
        return True
    except Exception as e:
        logger.error(f"Failed to insert errors into database: {e}", exc_info=True)
        return False    

def insert_solution_data(error_id,solution_data: List[Dict[str, Any]], db_manager) -> bool:
    """
    Insert solution data into the SOLUTIONS table
    Args:
        solution_data: List of solution records to insert
    Returns:
        True if insertion is successful, False otherwise
    """
    try:
        query = f"""INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.SOLUTIONS 
                (error_id, proposed_solution, confidence_score, final_solution_source)
                VALUES (@error_id, @proposed_solution, 0.8, 'AI Generated');"""
            
        params = {  
                'error_id': error_id,
                'proposed_solution': solution_data
            }
        ordered_params = ['error_id', 'proposed_solution']
        db_manager.execute(query, params, ordered_params)
        logger.info(f"Inserted {error_id} solution records into database")

        query = f"""UPDATE EL
                SET EL.SOLUTION_ID = S.solution_id
                FROM {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS EL
                JOIN {DATABASE_NAME}.{DATABASE_SCHEMA}.SOLUTIONS S ON EL.error_id = S.error_id"""
        db_manager.execute(query)
        logger.info(f"Updated ERROR_LOGS with SOLUTION_ID for error_id {error_id}")

        query = f"""UPDATE JTD
                SET JTD.SOLUTION_ID = S.solution_id
                FROM {DATABASE_NAME}.{DATABASE_SCHEMA}.JIRA_TICKET_DETAILS JTD
                JOIN {DATABASE_NAME}.{DATABASE_SCHEMA}.SOLUTIONS S ON JTD.error_id = S.error_id"""
        db_manager.execute(query)
        logger.info(f"Updated JIRA_TICKET_DETAILS with SOLUTION_ID for error_id {error_id}")

        return True
    except Exception as e:
        logger.error(f"Failed to insert solution data into database: {e}", exc_info=True)
        return False

def get_solution_data_from_db(similar_error_id, db_manager) -> Optional[Dict[str, Any]]:
    """
    Fetch solution data from the SOLUTIONS table based on error_id
    Args:
        error_id: The ID of the error to fetch solution for
    Returns:
        A dictionary containing solution data if found, None otherwise
    """
    try:
        error_id = [item['similar_id'] for item in similar_error_id if 'similar_id' in item]
        if error_id:
            error_id = ','.join(map(str, error_id))
            print(f"Fetching solution data for error_id {error_id} from database")
            query = f"""
                SELECT 
                e.cleaned_stack_trace,
                s.proposed_solution,
                s.confidence_score
            FROM {DATABASE_NAME}.{DATABASE_SCHEMA}.SOLUTIONS s
            JOIN {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS e ON s.error_id = e.error_id
            WHERE s.error_id IN ({error_id})
            AND s.confidence_score >= 0.8
            ORDER BY s.confidence_score DESC
            OFFSET 0 ROWS\nFETCH NEXT 1 ROWS ONLY

            """

            result = db_manager.fetch_all(query)
        
            if result:
                logger.info(f"Fetched solution data for error_id {error_id} from database")
                return result
            else:
                logger.info(f"No solution data found for error_id {error_id} in database")
                return None
    except Exception as e:
        logger.error(f"Failed to fetch solution data from database: {e}", exc_info=True)
        return None

def upsert_solution_data(solution_data: List[Dict[str, Any]], solution, status: List[Dict[str, Any]], db_manager) -> bool:
    """
    Upsert solution data into the SOLUTIONS table
    Args:
        solution_data: List of solution records to insert
    Returns:
        True if insertion is successful, False otherwise
    """
    try:
        query = f"""INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.SOLUTIONS 
                (error_id, proposed_solution, confidence_score)
                OUTPUT INSERTED.solution_id
                VALUES ({solution_data['error_id']}, {solution}, 0.7);"""
        solution_id_result = db_manager.fetch_one(query)
        solution_id = solution_id_result['SOLUTION_ID'] 
        logger.info(f"Inserted {len(solution_data)} solution records into database")
        
        query = f"""UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
                SET SOLUTION_ID = {solution_id}
                WHERE error_id = {solution_data['error_id']}"""
        db_manager.execute(query)
        logger.info(f"Updated ERROR_LOGS with SOLUTION_ID for error_id {solution_data['error_id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert solution data into database: {e}", exc_info=True)
        return False

def update_solution_status(solution, error_id,status, db_manager) -> None:
    if status is None:
            return True
    elif status == "APPROVED":
            query = f"""UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
                SET confidence_score = confidence_score + 0.1,
                applied_solution = {solution}
                WHERE error_id = {error_id}"""
            db_manager.execute(query)
            logger.info(f"Updated ERROR_LOGS with increased confidence_score for error_id {error_id}")
    elif status == "DECLINED":
            query = f"""UPDATE {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
                SET confidence_score = confidence_score - 0.2,
                applied_solution = {solution}
                WHERE error_id = {error_id}"""
            db_manager.execute(query)
            logger.info(f"Updated ERROR_LOGS with decreased confidence_score for error_id {error_id}")

def insert_job_status_data(db_manager, file_summary=None):
    """
    Insert ONE row into JOB_STATUS per file.
    """
    try:
        # Always create ONE record per file
        record = {
            "start_time": file_summary["start_time"],
            "end_time": file_summary["end_time"],
            "job_type": file_summary.get("label_type", "UNKNOWN"),
            "success_tag": "SUCCESS",
            "failure_tag": "FAILURE",
            "running_tag": "RUNNING",
            "success_count": file_summary.get("successful_workflows", 0),
            "failure_count": file_summary.get("failure_workflows", 0),
            "running_count": file_summary.get("running_workflows", 0),
        }

        query = f"""
        INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.JOB_STATUS
        (start_time, end_time, job_type,
         success_tag, failure_tag, running_tag,
         success_count, failure_count, running_count)
        VALUES
        (@start_time, @end_time, @job_type,
         @success_tag, @failure_tag, @running_tag,
         @success_count, @failure_count, @running_count);
        """

        db_manager.execute(query, record, list(record.keys()))
        print("Inserted ONE job status row for file.")

        return True

    except Exception as e:
        logger.error(f"Failed to insert job status data: {e}", exc_info=True)
        return False
    
def insert_errors_into_db_new(errors: list[dict], db_manager, team_name: str, project_name: str, repo_name: str) -> bool:
    """
    Insert error records into the ERROR_LOGS table
    """
    print(f"Some Details: {project_name}, {repo_name}")
    try:
        for error in errors:
            query = f"""
                INSERT INTO {DATABASE_NAME}.{DATABASE_SCHEMA}.ERROR_LOGS
                (error_tool, project_id, repo_name, job_type, 
                 error_message, stack_trace, cleaned_stack_trace, 
                 severity_level, processed, start_timestamp, end_timestamp)
                VALUES (
                    @error_tool, @project_name, @repo_name, @job_type,
                    @error_message, @stack_trace, @cleaned_stack_trace,
                    'HIGH', 0, @start_timestamp, @end_timestamp
                )
            """

            params = {
                'error_tool': error['tool'],
                'project_name': project_name,
                'repo_name': repo_name,
                'job_type': error.get('label_type'),   # NEW FIELD
                'error_message': error['main_error'],
                'stack_trace': error['stack_trace'],
                'cleaned_stack_trace': error['cleaned_stack_trace'],
                'start_timestamp': error.get('start_time'),
                'end_timestamp': error.get('end_time')
            }

            # MUST match only the markers in VALUES(...)
            ordered_params = [
                'error_tool', 'project_name', 'repo_name', 'job_type',
                'error_message', 'stack_trace', 'cleaned_stack_trace',
                'start_timestamp', 'end_timestamp'
            ]

            db_manager.execute(query, params, ordered_params)

        print(f"Inserted {len(errors)} errors into database")
        return True

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to insert errors into database: {e}", exc_info=True)
        return False
    
def insert_query_store_data_sql(query_data: List[Dict[str, Any]], db_manager) -> bool:

    try:
        for entry in query_data:
            query = f""" 
                INSERT INTO AI_PredictiveRecoveryDB.dbo.query_store 
                (question, sql_query)
                VALUES 
                (@question, @sql_query);
            """
            params = {
                'question': entry.get('question', ''),
                'sql_query': entry.get('sql_query', '')
            }
            
            ordered_params = ['question', 'sql_query']
            
            # Execute the insertion via your db_manager
            db_manager.execute(query, params, ordered_params)
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert query data into query_store: {e}", exc_info=True)
        return False

def get_jira_ticket_details_from_db(error_id, db_manager) -> Optional[Dict[str, Any]]:
    """
    Fetch JIRA ticket details from the JIRA_TICKET_DETAILS table based on error_id
    Args:
        error_id: The ID of the error to fetch JIRA ticket details for

        error_id = ','.join(map(str, error_id))"""
    
    print(f"Fetching solution data for error_id {error_id} from database")
    try:
        query = f"""
                    SELECT 
                    jtd.ticket_id,
                    jtd.jira_title,
                    jtd.description,
                    jtd.jira_ticket_link
                    from {DATABASE_NAME}.{DATABASE_SCHEMA}.JIRA_TICKET_DETAILS jtd
                    WHERE jtd.error_id IN ({error_id})

                """

        result = db_manager.fetch_all(query)
            
        if result:
            logger.info(f"Fetched jira details for error_id {error_id} from database")
            return result
        else:
            logger.info(f"No jira details found for error_id {error_id} in database")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch jira details from database: {e}", exc_info=True)
        return None
   
def upsert_pr_metadata(meta: dict, db_manager) -> None:
    query = f"""
    MERGE {DATABASE_NAME}.{DATABASE_SCHEMA}.pr_metadata AS target
    USING (SELECT
        @jira_ticket_number AS jira_ticket_number,
        @repo_slug AS repo_slug,
        @pr_id AS pr_id,
        @pr_url AS pr_url,
        @title AS title,
        @branch AS branch,
        @base_branch AS base_branch,
        @status AS status,
        @approved_at AS approved_at,
        @merged_at AS merged_at,
        @created_at AS created_at,
        @updated_at AS updated_at
    ) AS source
    ON target.jira_ticket_number = source.jira_ticket_number
    AND target.pr_id = source.pr_id

    WHEN MATCHED THEN
    UPDATE SET
        status = source.status,
        approved_at = COALESCE(source.approved_at, target.approved_at),
        merged_at = COALESCE(source.merged_at, target.merged_at),
        updated_at = COALESCE(source.updated_at, target.updated_at),
        db_updated_at = sysdatetime()

    WHEN NOT MATCHED THEN
    INSERT (
        jira_ticket_number,
        repo_slug,
        pr_id,
        pr_url,
        title,
        branch,
        base_branch,
        status,
        approved_at,
        merged_at,
        created_at,
        updated_at
    )
    VALUES (
        source.jira_ticket_number,
        source.repo_slug,
        source.pr_id,
        source.pr_url,
        source.title,
        source.branch,
        source.base_branch,
        source.status,
        source.approved_at,
        source.merged_at,
        source.created_at,
        source.updated_at
    );
    """

    params = {
        "jira_ticket_number": meta["jira_key"],
        "repo_slug": meta["repo"],
        "pr_id": meta["pr_number"],
        "pr_url": meta["pr_url"],
        "title": meta["title"],
        "branch": meta["branch"],
        "base_branch": meta["base_branch"],
        "status": meta["status"],
        "approved_at": meta.get("approved_at"),
        "merged_at": meta.get("merged_at"),
        "created_at": meta.get("created_at"),
        "updated_at": meta.get("updated_at"),
    }

    db_manager.execute(query, params, list(params.keys()))
    
if __name__ == "__main__":
        db_manager = DatabaseManager(DATABASE_URL)
        errors = insert_solution_data(error_id=198, solution_data = ['abcjndjnin'],db_manager=db_manager)
        print(errors)