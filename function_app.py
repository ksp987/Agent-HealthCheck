import logging
import azure.functions as func
from src.ai_agents import gmail_reader


app = func.FunctionApp()

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def gmail_reader(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    gmail_reader.read_healthcheck_attachments()