import os
import sys
from github import Github
import pickle
from datetime import datetime

"""
  Data: dictionary of RepositoryData (key = repository name)
  RepositoryData: dictionary of TrackedMetrics (key = "clones" or "views")
  TrackedMetrics: dictionary of [count, uniques] (key = timestamp)
"""

def write_data(data, data_file_path):
  with open(data_file_path, "w") as writer:
    writer.write("gitratra_v1\n")
    for repository_name in data:
      writer.write(">" + repository_name + "\n")
      repository_data = data[repository_name]
      for tracked_metric_name in repository_data:
        writer.write("#" + tracked_metric_name + "\n")
        tracked_metric = repository_data[tracked_metric_name]
        for timestamp in tracked_metric:
          date_str = datetime.strftime(timestamp, '%Y-%m-%d')
          writer.write(date_str + " ")
          metrics = tracked_metric[timestamp]
          writer.write(str(metrics[0]) + " " + str(metrics[1]) + "\n")

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

def read_tracked_metrics(reader, repository_data):
  metrics_name = read_line(reader)[1:]
  tracked_metrics = {}
  while (True):
    line = pick_line(reader)
    if (no_more_lines(reader) or line.startswith("#") or line.startswith(">")):
      break;
    line = read_line(reader)
    split = line.split(" ")
    timestamp = datetime.strptime(split[0], '%Y-%m-%d')
    count = int(split[1])
    uniques = int(split[2])
    tracked_metrics[timestamp] = [count, uniques]
  repository_data[metrics_name] = tracked_metrics

def read_repository_data(reader, data):
  repository = read_line(reader)[1:]
  data[repository] = {}
  while (not no_more_lines(reader) and pick_line(reader).startswith("#")):
    read_tracked_metrics(reader, data[repository])

def read_data(data_file_path):
  data = {}
  lines = open(data_file_path).readlines()
  reader = [lines, 0]
  gitratra_format = read_line(reader)
  assert(gitratra_format == "gitratra_v1")
  while (reader[1] < len(reader[0])):
    read_repository_data(reader, data)
  return data  

def get_data(data_file_path):
  if (not os.path.isfile(data_file_path)):
    return {}
  else:
    print("File " + data_file_path + " already exists, loading existing tracked metrics...")
    return read_data(data_file_path)


def get_db(data_path):
  if (not os.path.isfile(data_path)):
    print("File " + data_path + " does not exist yet. A new file will be created")
    return {}
  else:
    with open(data_path, 'rb') as handle:
      return pickle.load(handle)

def save_db(data_path, db):
  print("Saving results...")
  with open(data_path, 'wb') as handle:
    pickle.dump(db, handle, protocol=pickle.HIGHEST_PROTOCOL)

def print_per_stamp(per_stamp):
  for stamp in per_stamp:
    print(str(stamp) + " " + str(per_stamp[stamp]))


def update_metric(repo, data, metric_name):
  metrics = None
  if (metric_name == "views"):
    metrics = repo.get_views_traffic()[metric_name]
  elif (metric_name == "clones"):
    metrics = repo.get_clones_traffic()[metric_name]
  else:
    assert(False)
  tracked_metrics = data[repo.name][metric_name]
  for metric in metrics: 
    count = metric.count
    uniques = metric.uniques
    if (metric.timestamp in tracked_metrics):
      # the 14th day, the number of clones or views given by 
      # GitHub might decrease depending on the hour
      # We don't want to blindly erase,the existing value, but to take 
      # the max.
      count = max(count, tracked_metrics[metric.timestamp][0])
      uniques = max(uniques, tracked_metrics[metric.timestamp][1])
    assert(count >= uniques)
    tracked_metrics[metric.timestamp] = [count, uniques]

def update_repo(repo, data):
  if (not repo.name in data):
    print("Adding new repository " + repo.name)
    data[repo.name] = {}
    data[repo.name]["clones"] = {}
    data[repo.name]["views"] = {}
  print("querying current traffic data from " + repo.name + "...")
  update_metric(repo, data, "clones")
  update_metric(repo, data, "views")

def print_summary(data):
  print("")
  for repo_name in data:
    repository_data = data[repo_name]
    print(repo_name)
    for metric_name in repository_data:
      total_uniques = 0
      total_count = 0
      tracked_metrics = repository_data[metric_name]
      for timestamp in tracked_metrics:
        metrics = tracked_metrics[timestamp]
        total_count += metrics[0]
        total_uniques += metrics[1]
      print(metric_name + ": " + str(total_count))
      print("unique " + metric_name + ": " + str(total_uniques))
    print("")


def get_repositories(repositories_file_path):
  res = []
  lines = open(repositories_file_path).readlines()
  for line in lines:
    strip = line.strip()
    if (len(strip) > 0):
      res.append(strip)
  return res

def run_gitratra(token, data_path, repositories_file_path):
  print("Authentification...")
  g = Github(token)
  repositories = get_repositories(repositories_file_path)
  data = get_data(data_path)
  for repo_name in repositories:
    repo = g.get_user().get_repo(repo_name)
    update_repo(repo, data)
  print_summary(data)
  write_data(data, data_path)

def print_repository_table(data_path, repository_name):
  data = get_data(data_path)
  repository_data = data[repository_name]
  print("Printing the whole data for repository " + repository_name)
  for metric_name in repository_data:
    print(metric_name)
    metric_data = repository_data[metric_name]
    for timestamp in metric_data:
      timestamp_data = metric_data[timestamp]
      print(str(timestamp) + " count=" + str(timestamp_data[0]) + " uniques=" + str(timestamp_data[1]))

if (__name__== "__main__"):
  if (len(sys.argv) != 4):
    print("Syntax error: python run_generax.py auth_token repositories_list_file output_file.")
    sys.exit(0)

token = sys.argv[1]
repositories_file_path = sys.argv[2]
data_path = sys.argv[3]
run_gitratra(token, data_path, repositories_file_path)


