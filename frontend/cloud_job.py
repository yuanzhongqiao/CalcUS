import os
import json

from django.conf import settings

from .models import Calculation
from .environment_variables import *

if settings.IS_CLOUD:
    from google.cloud import batch_v1


def record_event_analytics(request, event_name, **extra_params):
    """
    Records particular significant events triggered by the user for analysis and management
    """

    if (
        IS_TEST
        or settings.DEBUG
        or not settings.IS_CLOUD
        or settings.ANALYTICS_MEASUREMENT_ID == ""
        or settings.ANALYTICS_API_SECRET == ""
    ):
        return

    from google.cloud import tasks_v2

    client = tasks_v2.CloudTasksClient()

    if "_ga" not in request.COOKIES:
        logger.warning(
            f"The Google Analytics cookie does not appear to be set for {request.user.id}"
        )
        return

    payload = {
        "client_id": request.COOKIES["_ga"],
        "events": [
            {
                "name": event_name,
                "params": {
                    "engagement_time_msec": "100",
                    **extra_params,
                },
            }
        ],
    }

    if "CALCUS_SESSION_COOKIE" in request.COOKIES:
        payload["events"][0]["params"]["session_id"] = request.COOKIES[
            "CALCUS_SESSION_COOKIE"
        ]

    if not request.user.is_anonymous:
        payload["user_id"] = str(request.user.id)
        if request.user.is_trial:
            account_type = "trial_account"
        elif request.user.is_temporary:
            account_type = "student_account"
        else:
            account_type = "full_account"

        payload["user_properties"] = {"account_type": {"value": account_type}}

    url = f"https://www.google-analytics.com/mp/collect?measurement_id={settings.ANALYTICS_MEASUREMENT_ID}&api_secret={settings.ANALYTICS_API_SECRET}"

    parent = client.queue_path(
        settings.GCP_PROJECT_ID, settings.GCP_LOCATION, "analytics"
    )

    task = {
        "http_request": {
            "http_method": "POST",
            "url": url,
            "oidc_token": {"service_account_email": settings.GCP_SERVICE_ACCOUNT_EMAIL},
            "headers": {"Content-type": "application/json"},
        }
    }
    task["http_request"]["body"] = json.dumps(payload).encode()

    client.create_task(parent=parent, task=task)


def create_container_job(calc, nproc, timeout):
    client = batch_v1.BatchServiceClient()

    runnable = batch_v1.Runnable()
    runnable.container = batch_v1.Runnable.Container()
    runnable.container.image_uri = settings.COMPUTE_IMAGE
    runnable.container.commands = [
        "/usr/local/bin/python",
        "manage.py",
        "run_calc",
        str(calc.id),
    ]

    env = batch_v1.Environment()
    env.secret_variables = {"POSTGRES_PASSWORD": settings.POSTGRES_SECRET_URI}
    env.variables = {
        "POSTGRES_USER": settings.POSTGRES_USER,
        "POSTGRES_HOST": os.environ.get(
            "COMPUTE_POSTGRES_HOST", settings.POSTGRES_HOST
        ),
        "CALCUS_COMPUTE": "True",
        "NUM_CPU": str(nproc),
        "OMP_NUM_THREADS": f"{nproc},1",
        "OMP_STACKSIZE": "1536MB",  # for the c3 machines only
    }

    runnable.environment = env

    task = batch_v1.TaskSpec()
    task.runnables = [runnable]

    resources = batch_v1.ComputeResource()
    resources.cpu_milli = nproc * 1000  # in milliseconds per cpu-second
    resources.memory_mib = nproc * 1024 * 2
    task.compute_resource = resources

    task.max_retry_count = 1
    task.max_run_duration = f"{timeout}s"

    group = batch_v1.TaskGroup()
    group.task_count = 1
    group.task_spec = task

    # TODO: batch some calculations together
    group.parallelism = 1

    policy = batch_v1.AllocationPolicy.InstancePolicy()
    policy.machine_type = f"c3-highcpu-{nproc}"

    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.policy = policy
    acc = batch_v1.ServiceAccount()
    acc.email = settings.COMPUTE_SERVICE_ACCOUNT

    allocation_policy = batch_v1.AllocationPolicy()
    allocation_policy.instances = [instances]
    allocation_policy.service_account = acc

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.labels = {"software": "xtb", "user_group": calc.order.author.user_type}

    # We use Cloud Logging as it's an out of the box available option
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.job = job
    create_request.job_id = f"j{str(calc.id).lower()}"

    create_request.parent = (
        f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_LOCATION}"
    )

    return client.create_job(create_request)


def send_gcloud_task(url, payload, compute=True):
    if IS_TEST or settings.DEBUG:
        import grpc
        from google.cloud import tasks_v2
        from google.cloud.tasks_v2.services.cloud_tasks.transports import (
            CloudTasksGrpcTransport,
        )

        if "GITHUB_WORKSPACE" in os.environ:
            hostname = "localhost"
        else:
            hostname = "taskqueue"

        client = tasks_v2.CloudTasksClient(
            transport=CloudTasksGrpcTransport(
                channel=grpc.insecure_channel(f"{hostname}:8123")
            )
        )
    else:
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksClient()

    if compute:
        queue = "xtb-compute"
        url = getattr(settings, f"COMPUTE_SMALL_HOST_URL") + url
    else:
        queue = "actions"
        url = settings.ACTION_HOST_URL + url

    parent = client.queue_path(settings.GCP_PROJECT_ID, settings.GCP_LOCATION, queue)

    task = {
        "http_request": {
            "http_method": "POST",
            "url": url,
            "oidc_token": {"service_account_email": settings.GCP_SERVICE_ACCOUNT_EMAIL},
        }
    }
    task["http_request"]["body"] = payload.encode()

    client.create_task(parent=parent, task=task)


def job_triage(calc):
    if calc.step.name in ["Conformational Search", "Constrained Conformational Search"]:
        nproc = 8
    else:
        nproc = 1

    user_type = calc.order.author.user_type

    return (
        min(settings.RESOURCE_LIMITS[user_type]["nproc"], nproc),
        settings.RESOURCE_LIMITS[user_type]["time"],
    )


def submit_cloud_job(calc):
    nproc, timeout = job_triage(calc)
    if nproc == 1:
        send_gcloud_task("/cloud_calc/", str(calc.id))
    else:
        create_container_job(calc, nproc, timeout)
