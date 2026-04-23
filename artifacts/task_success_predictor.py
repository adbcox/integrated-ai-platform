from framework.job_schema import Job
from typing import Any, Dict

def predict_task_success(job: Job, execution_report: dict[str, Any]) -> dict[str, Any]:
    task_category = job.task_category
    
    if task_category not in execution_report['by_task_category']:
        return {
            'predicted_success_rate': 0.5,
            'confidence': 'low',
            'recommendation': 'try_local',
            'reasoning': 'No historical data for this task category.',
            'data_source': 'default'
        }
    
    # Historical data exists for the task category
    category_data = execution_report['by_task_category'][task_category]
    success_rate = category_data.get('success_rate', 0.5)
    confidence = 'high' if len(category_data.get('executions', [])) > 10 else 'medium'
    
    recommendation = 'try_local'
    reasoning = f"Historical success rate for {task_category} is {success_rate:.2f}."
    
    return {
        'predicted_success_rate': success_rate,
        'confidence': confidence,
        'recommendation': recommendation,
        'reasoning': reasoning,
        'data_source': 'historical'
    }
