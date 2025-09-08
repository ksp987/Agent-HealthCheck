# function_app.py

import logging
import azure.functions as func
from ai_agent import gmail_reader as gmail_module


app = func.FunctionApp()

@app.timer_trigger(
        schedule="0 */5 * * * *", 
        arg_name="myTimer", 
        run_on_startup=False,
        use_monitor=False
        ) 

def run_gmail_reader(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info("Triggering Gmail attachment to fetch...")

    gmail_module.read_healthcheck_attachments()