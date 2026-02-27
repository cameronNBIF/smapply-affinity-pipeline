from main import main
import azure.functions as func
import logging
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)

app = func.FunctionApp()

@app.function_name(name="smapply-affinity-pipeline")
@app.timer_trigger(schedule="0 0 8 * * *", arg_name="myTimer", run_on_startup=True)
def smapply_affinity_pipeline(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    main()