

/* Create DB */
IF DB_ID('AI_PredictiveRecoveryDB') IS NULL
BEGIN
    CREATE DATABASE AI_PredictiveRecoveryDB;
END
GO

USE AI_PredictiveRecoveryDB;
GO

/* Create schema */
IF NOT EXISTS (
    SELECT 1 FROM sys.schemas WHERE name = 'project_1'
)
BEGIN
    EXEC ('CREATE SCHEMA project_1 AUTHORIZATION dbo');
END
GO

USE AI_PredictiveRecoveryDB;

CREATE TABLE [project_1].[solutions](
    [solution_id] [int] IDENTITY(1,1) NOT NULL,
    [error_id] [int] NOT NULL,
    [proposed_solution] [nvarchar](max) NOT NULL,
    [applied_solution] [nvarchar](max) NULL,
    [confidence_score] [decimal](5, 2) NOT NULL,
    [final_solution_source] [varchar](30) NOT NULL,
    [created_at] [datetime2](3) NOT NULL DEFAULT SYSDATETIME(),
    [updated_at] [datetime2](3) NULL DEFAULT SYSDATETIME(),
    CONSTRAINT [PK_solutions] PRIMARY KEY CLUSTERED ([solution_id])
);

CREATE TABLE [AI_PREDICTIVERECOVERYDB].[Project_1].[root_causes](
	[root_cause_id] [int] IDENTITY(1,1) NOT NULL,
	[error_id] [int] NOT NULL,
	[root_cause] [nvarchar](max) NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NULL,
PRIMARY KEY CLUSTERED 
(
	[root_cause_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

CREATE TABLE [project_1].[jira_ticket_details](

	[jira_id] [int] IDENTITY(1,1) NOT NULL,

	[ticket_id] [nvarchar](50) NOT NULL,

	[error_id] [int] NULL,

	[jira_title] [nvarchar](255) NOT NULL,

	[description] [nvarchar](max) NULL,

	[solution_id] [int] NULL,

	[created_at] [datetime2](7) NULL,

	[updated_at] [datetime2](7) NULL,

	[jira_ticket_link] [varchar](500) NULL,

PRIMARY KEY CLUSTERED 

(

	[jira_id] ASC

)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]

) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO



CREATE TABLE [AI_PREDICTIVERECOVERYDB].[Project_1].[ERROR_LOGS](
	[error_id] [int] IDENTITY(1,1) NOT NULL,
	[event_timestamp] [datetime2](3) DEFAULT SYSDATETIME(),
	[start_timestamp] [datetime2](3) NOT NULL,
	[end_timestamp] [datetime2](3) NOT NULL,
	[job_type] VARCHAR(255) NOT NULL,
	[error_tool] [varchar](255) NOT NULL,
	[project_id] [varchar](100) NULL,
	[repo_name] [varchar](200) NULL,
	[error_message] [text] NOT NULL,
	[stack_trace] [text] NULL,
	[cleaned_stack_trace] [text] NULL,
	[severity_level] [text] NULL,
	[occurrence_count] [int] NULL,
	[solution_id] [int] NULL,
	[root_cause_id] [int] NULL,
	[jira_id] [int] NULL,
	[processed] [bit] NULL,
PRIMARY KEY CLUSTERED 
(
	[error_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

CREATE TABLE [AI_PREDICTIVERECOVERYDB].[Project_1].[JOB_STATUS](
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [start_time] DATETIME2(3) NOT NULL,
    [end_time] DATETIME2(3) NOT NULL,
    [job_type] VARCHAR(255) NOT NULL,
    [success_tag] VARCHAR(255) NOT NULL,
    [failure_tag] VARCHAR(255) NOT NULL,
    [running_tag] VARCHAR(255) NOT NULL,
    [success_count] INT NOT NULL,
    [failure_count] INT NOT NULL,
    [running_count] INT NOT NULL
);