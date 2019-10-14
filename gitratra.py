import os
import sys
from github import Github
import pickle
from datetime import datetime
import getpass

"""
  gitratra: query a list of GitHub repositories to store traffic
  information into a file

  Uses the following representation:
  - TrafficData: dictionary of RepositoryData (key = repository_name)
  - RepositoryData: dictionary of MetricsData (key = metric_name = "clones" or "views")
  - MetricsData: dictionary of [count, uniques] (key = timestamp (datetime))
"""


"""
  Write traffic data into a file
"""
def write_data(traffic_data, data_file_path):
  with open(data_file_path, "w") as writer:
    writer.write("gitratra_v1\n")
    for repository_name in traffic_data:
      writer.write(">" + repository_name + "\n")
      repository_data = traffic_data[repository_name]
      for metric_name in repository_data:
        writer.write("#" + metric_name + "\n")
        metric_data = repository_data[metric_name]
        for timestamp in metric_data:
          timestamp_str = datetime.strftime(timestamp, '%Y-%m-%d')
          writer.write(timestamp_str + " ")
          metrics = metric_data[timestamp]
          writer.write(str(metrics[0]) + " " + str(metrics[1]) + "\n")

"""
  Several helper functions for navigating into a list
  of lines
"""
def no_more_lines(reader):
  return reader[1] >= len(reader[0])

def pick_line(reader):
  if (no_more_lines(reader)):
    return None
  return reader[0][reader[1]][:-1]

def read_line(reader):
  if (no_more_lines(reader)):
    return None
  reader[1] = reader[1] + 1
  return reader[0][reader[1] - 1][:-1]

""" 
  Several functions to read Data from a file
"""
def read_metric_data(reader, repository_data):
  metrics_name = read_line(reader)[1:]
  metric_data = {}
  while (True):
    line = pick_line(reader)
    if (no_more_lines(reader) or line.startswith("#") or line.startswith(">")):
      break;
    line = read_line(reader)
    split = line.split(" ")
    timestamp = datetime.strptime(split[0], '%Y-%m-%d')
    count = int(split[1])
    uniques = int(split[2])
    metric_data[timestamp] = [count, uniques]
  repository_data[metrics_name] = metric_data

def read_repository_data(reader, traffic_data):
  repository = read_line(reader)[1:]
  traffic_data[repository] = {}
  while (not no_more_lines(reader) and pick_line(reader).startswith("#")):
    read_metric_data(reader, traffic_data[repository])

def read_traffic_data(data_file_path):
  traffic_data = {}
  lines = open(data_file_path).readlines()
  reader = [lines, 0]
  gitratra_format = read_line(reader)
  assert(gitratra_format == "gitratra_v1")
  while (reader[1] < len(reader[0])):
    read_repository_data(reader, traffic_data)
  return traffic_data  

def get_traffic_data(data_file_path):
  if (not os.path.isfile(data_file_path)):
    return {}
  else:
    print("File " + data_file_path + " already exists, loading existing traffic data...")
    return read_traffic_data(data_file_path)


"""
  Given a Repository object and a metric name ("view" or "clone"), 
  update our Data structure with a query to github
"""
def update_metric(repo, traffic_data, metric_name):
  metrics = None
  if (metric_name == "views"):
    metrics = repo.get_views_traffic()[metric_name]
  elif (metric_name == "clones"):
    metrics = repo.get_clones_traffic()[metric_name]
  else:
    assert(False)
  metric_data = traffic_data[repo.name][metric_name]
  for metric in metrics: 
    count = metric.count
    uniques = metric.uniques
    if (metric.timestamp in metric_data):
      # at the 14th oldest timestamp, the number of clones or views given by 
      # GitHub might decrease depending on the hour
      # We don't want to blindly erase,the existing value, but to take 
      # the max.
      count = max(count, metric_data[metric.timestamp][0])
      uniques = max(uniques, metric_data[metric.timestamp][1])
    assert(count >= uniques)
    metric_data[metric.timestamp] = [count, uniques]

"""
  Given a Repository object, update a Data object with
  queries to github
"""
def update_repo(repo, traffic_data):
  if (not repo.name in traffic_data):
    print("Adding new repository " + repo.name)
    traffic_data[repo.name] = {}
    traffic_data[repo.name]["clones"] = {}
    traffic_data[repo.name]["views"] = {}
  print("querying current traffic data from " + repo.name + "...")
  update_metric(repo, traffic_data, "clones")
  update_metric(repo, traffic_data, "views")

"""
  Briefly summarize the traffic information
  stored in the traffic data
"""
def print_summary(traffic_data):
  print("")
  for repo_name in traffic_data:
    repository_data = traffic_data[repo_name]
    print(repo_name)
    for metric_name in repository_data:
      total_uniques = 0
      total_count = 0
      metric_data = repository_data[metric_name]
      for timestamp in metric_data:
        metrics = metric_data[timestamp]
        total_count += metrics[0]
        total_uniques += metrics[1]
      print(metric_name + ": " + str(total_count))
      print("unique " + metric_name + ": " + str(total_uniques))
    print("")


def read_repositories_names(repositories_file_path):
  res = []
  lines = open(repositories_file_path).readlines()
  for line in lines:
    strip = line.strip()
    if (len(strip) > 0):
      res.append(strip)
  return res

"""
  Main function
"""
def run_gitratra(token, data_path, repositories_file_path):
  print("Authentification...")
  g = None
  split_token = token.split(":")
  if (split_token[0] == "token"):
    g = Github(split_token[1])
  else:
    g = Github(split_token[1], getpass.getpass())
  repositories = read_repositories_names(repositories_file_path)
  traffic_data = get_traffic_data(data_path)
  for repo_name in repositories:
    repo = g.get_user().get_repo(repo_name)
    update_repo(repo, traffic_data)
  print_summary(traffic_data)
  write_data(traffic_data, data_path)

def print_error_syntax():
    print("Possible syntaxes:")
    print("python run_generax.py token:<github_token> <repositories_list_file> <output_file>.")
    print("python run_generax.py username:<username> <repositories_list_file> <output_file>.")

if (__name__== "__main__"):
  if (len(sys.argv) != 4):
    print_error_syntax()
    sys.exit(0)
  token = sys.argv[1]
  if (len(token.split(":")) != 2):
    print("ERROR: Invalid token or username string")
    print_error_syntax()
    sys.exit(1)
  repositories_file_path = sys.argv[2]
  data_path = sys.argv[3]
  run_gitratra(token, data_path, repositories_file_path)


