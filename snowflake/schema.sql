-- First-load SQL for SHARED_DB.PUBLIC.EMAIL_RECIPIENTS.
-- The Streamlit app reads and writes this table only.
-- Uses IF NOT EXISTS so an existing table is not replaced.
-- Seed rows are MERGE'd and can be re-run.

CREATE DATABASE IF NOT EXISTS SHARED_DB;
CREATE SCHEMA IF NOT EXISTS SHARED_DB.PUBLIC;

CREATE TABLE IF NOT EXISTS SHARED_DB.PUBLIC.EMAIL_RECIPIENTS (
    EMAIL_ADDRESS      VARCHAR(320) NOT NULL,
    RECIPIENT_NAME     VARCHAR(256),
    INTEGRATION_SCOPE  VARCHAR(50)  NOT NULL DEFAULT 'ALL',
    RECIPIENT_TYPE     VARCHAR(20)  NOT NULL DEFAULT 'TO',
    IS_ACTIVE          BOOLEAN      NOT NULL DEFAULT TRUE,
    CREATED_TIMESTAMP  TIMESTAMP_NTZ(9) NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT         TIMESTAMP_NTZ(9),
    NOTES              VARCHAR(16777216),
    ENVIRONMENT        VARCHAR(50)  NOT NULL DEFAULT 'Live',
    STATUS_SCOPE       VARCHAR(50)  NOT NULL DEFAULT 'All',
    SEND_DAYS          VARCHAR(50)  NOT NULL DEFAULT 'All',
    PRIMARY KEY (EMAIL_ADDRESS, INTEGRATION_SCOPE, ENVIRONMENT, STATUS_SCOPE)
);

COMMENT ON TABLE SHARED_DB.PUBLIC.EMAIL_RECIPIENTS IS
    'Email addresses that receive the Live Weather Travel dashboard and other integrations.';

-- Starter row. Re-running this MERGE does not remove other addresses.
MERGE INTO SHARED_DB.PUBLIC.EMAIL_RECIPIENTS AS tgt
USING (
    SELECT
        column1 AS EMAIL_ADDRESS,
        column2 AS RECIPIENT_NAME,
        column3 AS INTEGRATION_SCOPE,
        column4 AS RECIPIENT_TYPE,
        column5 AS IS_ACTIVE,
        column6 AS NOTES,
        column7 AS ENVIRONMENT,
        column8 AS STATUS_SCOPE,
        column9 AS SEND_DAYS
    FROM VALUES
        (
            'dazag888@gmail.com',
            'Dashboard owner',
            'ALL',
            'TO',
            TRUE,
            'Primary inbox for dashboard and data exception report email',
            'Live',
            'All',
            'All'
        )
) AS src
ON tgt.EMAIL_ADDRESS = src.EMAIL_ADDRESS
   AND tgt.INTEGRATION_SCOPE = src.INTEGRATION_SCOPE
   AND tgt.ENVIRONMENT = src.ENVIRONMENT
   AND tgt.STATUS_SCOPE = src.STATUS_SCOPE
WHEN NOT MATCHED THEN
    INSERT (
        EMAIL_ADDRESS,
        RECIPIENT_NAME,
        INTEGRATION_SCOPE,
        RECIPIENT_TYPE,
        IS_ACTIVE,
        NOTES,
        ENVIRONMENT,
        STATUS_SCOPE,
        SEND_DAYS
    )
    VALUES (
        src.EMAIL_ADDRESS,
        src.RECIPIENT_NAME,
        src.INTEGRATION_SCOPE,
        src.RECIPIENT_TYPE,
        src.IS_ACTIVE,
        src.NOTES,
        src.ENVIRONMENT,
        src.STATUS_SCOPE,
        src.SEND_DAYS
    )
WHEN MATCHED THEN
    UPDATE SET
        RECIPIENT_NAME = src.RECIPIENT_NAME,
        RECIPIENT_TYPE = src.RECIPIENT_TYPE,
        IS_ACTIVE = src.IS_ACTIVE,
        NOTES = src.NOTES,
        SEND_DAYS = src.SEND_DAYS,
        UPDATED_AT = CURRENT_TIMESTAMP();

SELECT
    EMAIL_ADDRESS,
    RECIPIENT_NAME,
    INTEGRATION_SCOPE,
    RECIPIENT_TYPE,
    IS_ACTIVE,
    ENVIRONMENT,
    STATUS_SCOPE,
    SEND_DAYS,
    NOTES
FROM SHARED_DB.PUBLIC.EMAIL_RECIPIENTS
ORDER BY IS_ACTIVE DESC, EMAIL_ADDRESS;
