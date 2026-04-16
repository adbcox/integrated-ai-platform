from framework.state_store import StateStore
from typing import Any

def generate_execution_report(store: StateStore) -> dict[str, Any]:
    by_task_category = {}
    by_pattern_type = {}
    overall_success_count = 0
    overall_total_count = 0

    jobs = store.list_jobs()
    for job_id in jobs:
        job = store.load_job(job_id)
        result = store.load_result(job_id)

        task_category = job.get('task_category', 'unknown')
        pattern_type = job.get('pattern_type', 'unknown')

        success = (result.get('outcome_class') == 'success' or
                   result.get('status') == 'completed')

        if task_category not in by_task_category:
            by_task_category[task_category] = {'success_count': 0, 'total_count': 0}
        if pattern_type not in by_pattern_type:
            by_pattern_type[pattern_type] = {'success_count': 0, 'total_count': 0}

        if success:
            overall_success_count += 1
            by_task_category[task_category]['success_count'] += 1
            by_pattern_type[pattern_type]['success_count'] += 1

        overall_total_count += 1
        by_task_category[task_category]['total_count'] += 1
        by_pattern_type[pattern_type]['total_count'] += 1

    for category in by_task_category.values():
        category['success_rate'] = (category['success_count'] / category['total_count']) if category['total_count'] > 0 else 0.0

    for pattern in by_pattern_type.values():
        pattern['success_rate'] = (pattern['success_count'] / pattern['total_count']) if pattern['total_count'] > 0 else 0.0

    overall_success_rate = (overall_success_count / overall_total_count) if overall_total_count > 0 else 0.0

    return {
        'by_task_category': by_task_category,
        'by_pattern_type': by_pattern_type,
        'overall': {
            'success_count': overall_success_count,
            'total_count': overall_total_count,
            'success_rate': overall_success_rate
        }
    }
