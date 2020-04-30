import click
from ..common import utils
from ..common import executer

def resolve_cluster(gcp_project_id, gcp_cluster_id, gcp_cluster_zone) -> (str, str):
  print("\n===== Resolve GCP Cluster =====\n")

  display_cluster_list(gcp_project_id)

  gcp_cluster_id, gcp_cluster_zone = resolve_cluster_id_zone(
      gcp_project_id, gcp_cluster_id, gcp_cluster_zone)

  # Get cluster credentail for next steps
  cmd = "gcloud container clusters get-credentials {0} --zone {1} --project {2}".format(
      gcp_cluster_id, gcp_cluster_zone, gcp_project_id)
  print("Executing command to check whether can access the cluster: {0}".format(cmd))
  cmd_result = executer.execute(cmd)
  if cmd_result.has_error:
    utils.print_error("{0}".format(cmd_result.stderr))
    gcp_create_cluster = click.confirm("Seem can't access the cluster, do you want to create a new one?", default=True)

    if gcp_create_cluster:
      create_cluster_and_get_credentials(gcp_project_id, gcp_cluster_id, gcp_cluster_zone, cmd)
    else:
      utils.print_error("Please check your inputed cluster to make sure you can access it or create new one.")
      exit(1)
  else:
    print("Got access to cluster: {0}, zone: {1}, project: {2}".format(
        gcp_cluster_id, gcp_cluster_zone, gcp_project_id))

  return gcp_cluster_id, gcp_cluster_zone

def display_cluster_list(gcp_project_id):
  cmd = "gcloud container clusters list --project {0}".format(gcp_project_id)
  print("Executing command to get list of clusters: {0}".format(cmd))
  cmd_result = executer.execute(cmd)
  if cmd_result.has_error:
    utils.print_error("{0}".format(cmd_result.stderr))
    exit(1)
  else:
    print(cmd_result.stdout)

def resolve_cluster_id_zone(gcp_project_id, gcp_cluster_id, gcp_cluster_zone):
  if gcp_cluster_id == None:
    print("Didn't specify --gcp-cluster-id.")
    gcp_cluster_id = click.prompt('Input an existing GCP Cluster ID or new one to be created', type=str, default='cluster-kfp')
  else:
    print("GCP Cluster ID: {0}".format(gcp_cluster_id))

  if gcp_cluster_zone == None:
    print("Didn't specify --gcp-zone.")
    # todo support region for multi-zone cluster
    gcp_cluster_zone = click.prompt('Input GCP Zone: ', type=str, default='us-central1-a')
  else:
    print("GCP Zone: {0}".format(gcp_cluster_zone))

  return gcp_cluster_id, gcp_cluster_zone

def create_cluster_and_get_credentials(gcp_project_id, gcp_cluster_id, gcp_cluster_zone, cmd):
  print("Let's create a new GKE cluster.")
  utils.print_warning("To better customize your cluster, please create it outside of this tool.")

  # TODO: handle Workload Identity mode
  cmd = "gcloud container clusters create {0} --zone {1} --project {2} --machine-type n1-standard-4 --scopes cloud-platform"
  cmd = cmd.format(gcp_cluster_id, gcp_cluster_zone, gcp_project_id)
  print("Executing command to create a cluster (it may takes mintues): {0}".format(cmd))
  cmd_result = executer.execute(cmd)
  if cmd_result.has_error:
    utils.print_error("{0}".format(cmd_result.stderr))
    exit(1)
  else:
    print(cmd_result.stdout)

  # Get credential for following usage
  print("Executing command to access the cluster: {0}".format(cmd))
  cmd_result = executer.execute(cmd)
  if cmd_result.has_error:
    utils.print_error("{0}".format(cmd_result.stderr))
    exit(1)
  else:
    print("Got access to cluster: {0}, zone: {1}, project: {2}".format(
        gcp_cluster_id, gcp_cluster_zone, gcp_project_id))