-- Snowflake SYSTEM$SEND_EMAIL for the Live Weather Travel app.
-- Sends to active Live TO recipients in SHARED_DB.PUBLIC.EMAIL_RECIPIENTS
-- whose SEND_DAYS is All or Weekends.
-- Schedule: Sunday 16:00 Europe/London (UK time, including BST).

CREATE OR REPLACE NOTIFICATION INTEGRATION TEST_EMAIL_INTEGRATION
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ('dazag888@gmail.com')
  COMMENT = 'Sunday status email for the Live Weather Travel app';

CREATE OR REPLACE PROCEDURE SNOWFLAKE_LEARNING_DB.TEST2.SEND_SUNDAY_STATUS_EMAIL()
  RETURNS VARCHAR
  LANGUAGE SQL
  EXECUTE AS OWNER
AS
$$
DECLARE
  recipient VARCHAR;
  body VARCHAR;
  vendor_count NUMBER;
  exception_count NUMBER;
  sent_count NUMBER DEFAULT 0;
  recipient_cursor CURSOR FOR
    SELECT EMAIL_ADDRESS
    FROM SHARED_DB.PUBLIC.EMAIL_RECIPIENTS
    WHERE IS_ACTIVE = TRUE
      AND RECIPIENT_TYPE = 'TO'
      AND ENVIRONMENT = 'Live'
      AND STATUS_SCOPE = 'All'
      AND SEND_DAYS IN ('All', 'Weekends');
BEGIN
  SELECT COUNT(*) INTO :vendor_count
  FROM SNOWFLAKE_LEARNING_DB.TEST2.JERSEY_BUILDING_VENDORS;

  SELECT COUNT(*) INTO :exception_count
  FROM SHARED.PUBLIC.DATA_EXCEPTION_REPORT;

  body := 'Sunday status for the Live Weather Travel app.' || CHR(10)
    || 'Jersey building vendors in SNOWFLAKE_LEARNING_DB.TEST2: ' || :vendor_count || CHR(10)
    || 'Data exception report rows in SHARED.PUBLIC.DATA_EXCEPTION_REPORT: ' || :exception_count || CHR(10)
    || 'This message is scheduled for Sunday 16:00 UK time (Europe/London).';

  OPEN recipient_cursor;
  FOR rec IN recipient_cursor DO
    recipient := rec.EMAIL_ADDRESS;
    CALL SYSTEM$SEND_EMAIL(
      'TEST_EMAIL_INTEGRATION',
      :recipient,
      'Live Weather Travel — Sunday status',
      :body
    );
    sent_count := sent_count + 1;
  END FOR;
  CLOSE recipient_cursor;

  RETURN 'Sent ' || sent_count || ' email(s)';
END;
$$;

CREATE OR REPLACE TASK SNOWFLAKE_LEARNING_DB.TEST2.SUNDAY_STATUS_EMAIL
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 16 * * SUN Europe/London'
  COMMENT = 'Send the Live Weather Travel Sunday status email at 16:00 UK time'
AS
  CALL SNOWFLAKE_LEARNING_DB.TEST2.SEND_SUNDAY_STATUS_EMAIL();

ALTER TASK SNOWFLAKE_LEARNING_DB.TEST2.SUNDAY_STATUS_EMAIL RESUME;
